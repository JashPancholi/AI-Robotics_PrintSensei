import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.shares import (
    get_local_share_storage,
    get_qr_share_repository,
    get_qr_share_service,
)
from app.enums.label_type import LabelType
from app.main import app
from app.models.label_data import LabelData
from app.renderer import LabelRenderer
from backend.services.qr.service import (
    QrShareService,
    build_mobile_share_page,
    cleanup_expired_shares,
)
from backend.services.qr.storage import LocalShareStorage
from infrastructure.database_models import Base
from infrastructure.history_repository import HistoryRepository
from infrastructure.qr_share_repository import QrShareRepository


def repositories():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    return HistoryRepository(factory), QrShareRepository(factory)


def add_history(repository: HistoryRepository, image_path: Path, title="Mouse <Inside>"):
    history_id = uuid4()
    repository.create(
        request_id=history_id,
        prompt='Explain a "cheap" mouse & its parts',
        title=title,
        image_path=image_path,
        content_type="diagram",
        width=384,
        height=300,
    )
    return history_id


def make_service(
    tmp_path,
    now,
    base_url="http://192.168.1.50:8000",
    storage=None,
):
    history, shares = repositories()
    source = tmp_path / "source.png"
    Image.new("1", (384, 200), "white").save(source)
    history_id = add_history(history, source)
    storage = storage or LocalShareStorage(tmp_path / "shares")
    service = QrShareService(
        history,
        shares,
        storage,
        base_url,
        ttl_days=7,
        renderer=LabelRenderer(tmp_path / "labels"),
        clock=lambda: now[0],
    )
    return service, history, shares, storage, history_id


def test_share_stores_local_mobile_page_and_reuses_active_share(tmp_path):
    now = [datetime(2026, 8, 31, 10, tzinfo=timezone.utc)]
    service, _, _, storage, history_id = make_service(tmp_path, now)

    created = service.create_or_reuse(history_id)
    reused = service.create_or_reuse(history_id)

    assert reused.id == created.id
    assert created.public_url == f"http://192.168.1.50:8000/share/{created.token}"
    assert created.expires_at == now[0] + timedelta(days=7)
    assert storage.resolve_asset(created.image_asset_path).is_file()
    assert Path(created.qr_image_path).is_file()
    page = storage.resolve_asset(created.page_asset_path).read_text(encoding="utf-8")
    assert "Mouse &lt;Inside&gt;" in page
    assert "&quot;cheap&quot; mouse &amp; its parts" in page
    assert f'href="/share/{created.token}/image.png" download=' in page


def test_expired_share_is_replaced_and_local_files_are_removed(tmp_path):
    now = [datetime(2026, 8, 31, 10, tzinfo=timezone.utc)]
    service, _, _, storage, history_id = make_service(tmp_path, now)
    first = service.create_or_reuse(history_id)
    first_image = storage.resolve_asset(first.image_asset_path)

    now[0] = first.expires_at + timedelta(seconds=1)
    second = service.create_or_reuse(history_id)

    assert second.id != first.id
    assert second.token != first.token
    assert not first_image.exists()
    assert storage.resolve_asset(second.image_asset_path).is_file()


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "https://127.0.0.1:8001",
        "http://example.com",
        "http://192.168.1.50:8000/path",
    ],
)
def test_share_api_rejects_unsafe_configuration(tmp_path, base_url):
    now = [datetime.now(timezone.utc)]
    service, _, _, _, history_id = make_service(tmp_path, now, base_url=base_url)
    client = TestClient(app)
    app.dependency_overrides[get_qr_share_service] = lambda: service
    try:
        response = client.post(f"/api/history/{history_id}/share")
    finally:
        app.dependency_overrides.pop(get_qr_share_service, None)

    assert response.status_code == 503


def test_public_https_tunnel_url_is_accepted(tmp_path):
    now = [datetime.now(timezone.utc)]
    service, _, _, _, history_id = make_service(
        tmp_path,
        now,
        base_url="https://demo-name.trycloudflare.com",
    )

    share = service.create_or_reuse(history_id)

    assert share.public_url == (
        f"https://demo-name.trycloudflare.com/share/{share.token}"
    )


def test_changed_tunnel_hostname_creates_a_new_share(tmp_path):
    now = [datetime.now(timezone.utc)]
    first_service, history, shares, storage, history_id = make_service(
        tmp_path,
        now,
        base_url="https://first-name.trycloudflare.com",
    )
    first = first_service.create_or_reuse(history_id)
    second_service = QrShareService(
        history,
        shares,
        storage,
        "https://second-name.trycloudflare.com",
        renderer=LabelRenderer(tmp_path / "labels"),
        clock=lambda: now[0],
    )

    second = second_service.create_or_reuse(history_id)

    assert second.id != first.id
    assert second.public_url.startswith("https://second-name.trycloudflare.com/share/")


def test_share_api_maps_local_storage_failure_to_server_error(tmp_path):
    class FailingStorage(LocalShareStorage):
        def store_assets(self, *args, **kwargs):
            raise OSError("disk unavailable")

    now = [datetime.now(timezone.utc)]
    storage = FailingStorage(tmp_path / "shares")
    service, _, _, _, history_id = make_service(tmp_path, now, storage=storage)
    client = TestClient(app)
    app.dependency_overrides[get_qr_share_service] = lambda: service
    try:
        response = client.post(f"/api/history/{history_id}/share")
    finally:
        app.dependency_overrides.pop(get_qr_share_service, None)

    assert response.status_code == 500


def test_share_api_returns_gone_for_missing_source_image(tmp_path):
    history, shares = repositories()
    history_id = add_history(history, tmp_path / "missing.png")
    service = QrShareService(
        history,
        shares,
        LocalShareStorage(tmp_path / "shares"),
        "http://192.168.1.50:8000",
    )
    client = TestClient(app)
    app.dependency_overrides[get_qr_share_service] = lambda: service
    try:
        response = client.post(f"/api/history/{history_id}/share")
    finally:
        app.dependency_overrides.pop(get_qr_share_service, None)

    assert response.status_code == 410


def test_public_page_and_image_require_a_valid_unexpired_token(tmp_path):
    now = [datetime.now(timezone.utc)]
    service, _, shares, storage, history_id = make_service(tmp_path, now)
    share = service.create_or_reuse(history_id)
    client = TestClient(app)
    app.dependency_overrides[get_qr_share_repository] = lambda: shares
    app.dependency_overrides[get_local_share_storage] = lambda: storage
    try:
        page = client.get(f"/share/{share.token}")
        image = client.get(f"/share/{share.token}/image.png")
        missing = client.get("/share/not-a-real-token")
    finally:
        app.dependency_overrides.pop(get_qr_share_repository, None)
        app.dependency_overrides.pop(get_local_share_storage, None)

    assert page.status_code == 200
    assert "Mouse &lt;Inside&gt;" in page.text
    assert f'src="/share/{share.token}/image.png"' in page.text
    assert page.headers["cache-control"] == "no-store"
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/png"
    assert missing.status_code == 404


def test_public_routes_return_gone_and_clean_expired_assets(tmp_path):
    now = [datetime.now(timezone.utc) - timedelta(days=8)]
    service, _, shares, storage, history_id = make_service(tmp_path, now)
    share = service.create_or_reuse(history_id)
    image_path = storage.resolve_asset(share.image_asset_path)
    client = TestClient(app)
    app.dependency_overrides[get_qr_share_repository] = lambda: shares
    app.dependency_overrides[get_local_share_storage] = lambda: storage
    try:
        page = client.get(f"/share/{share.token}")
        image = client.get(f"/share/{share.token}/image.png")
    finally:
        app.dependency_overrides.pop(get_qr_share_repository, None)
        app.dependency_overrides.pop(get_local_share_storage, None)

    assert page.status_code == 410
    assert image.status_code == 410
    assert not image_path.exists()


def test_qr_print_counter_is_separate_from_history_counter(tmp_path):
    now = [datetime.now(timezone.utc)]
    service, history, shares, _, history_id = make_service(tmp_path, now)
    share = service.create_or_reuse(history_id)
    client = TestClient(app)
    app.dependency_overrides[get_qr_share_repository] = lambda: shares
    try:
        response = client.post(f"/api/shares/{share.id}/print")
    finally:
        app.dependency_overrides.pop(get_qr_share_repository, None)

    assert response.status_code == 200
    assert response.json()["message"] == "QR print simulated successfully."
    assert response.json()["print_count"] == 1
    assert shares.get(share.id).print_count == 1
    assert history.get(history_id).print_count == 0


def test_mobile_page_escapes_user_content(tmp_path):
    history, _ = repositories()
    image = tmp_path / "x.png"
    image.touch()
    history_id = add_history(history, image, title="</title><script>alert(1)</script>")

    page = build_mobile_share_page(
        history.get(history_id),
        "/share/example-token/image.png",
        datetime.now(timezone.utc) + timedelta(days=7),
    )

    assert "</title><script>alert(1)</script>" not in page
    assert "&lt;/title&gt;&lt;script&gt;alert(1)&lt;/script&gt;" in page


def test_rendered_qr_contains_configured_local_page_url():
    public_url = (
        "http://192.168.1.50:8000/share/"
        "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFG"
    )
    image = LabelRenderer()._render_image(
        LabelData(title="Scan to View", qr_data=public_url, label_type=LabelType.QR)
    )

    decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(np.array(image.convert("L")))
    assert decoded == public_url


def test_local_storage_refuses_access_or_deletion_outside_share_root(tmp_path):
    storage = LocalShareStorage(tmp_path / "shares")
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"keep")

    with pytest.raises(ValueError, match="outside local share storage"):
        storage.resolve_asset(outside)
    with pytest.raises(ValueError, match="outside local share storage"):
        storage.delete_assets(str(outside), str(outside))

    assert outside.read_bytes() == b"keep"


def test_cleanup_ignores_legacy_remote_paths(tmp_path):
    now = datetime.now(timezone.utc)
    history, shares = repositories()
    source = tmp_path / "source.png"
    source.touch()
    history_id = add_history(history, source)
    shares.create(
        share_id=uuid4(),
        history_id=history_id,
        token="legacy-azure-token",
        image_asset_path="shares/legacy/image.png",
        page_asset_path="shares/legacy/index.html",
        public_url="https://example.web.core.windows.net/shares/legacy/index.html",
        qr_image_path="generated_labels/old.png",
        expires_at=now - timedelta(days=1),
    )

    assert cleanup_expired_shares(shares, LocalShareStorage(tmp_path / "local"), now) == 0
