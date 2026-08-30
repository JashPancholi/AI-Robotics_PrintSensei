import html
import ipaddress
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from app.enums.label_type import LabelType
from app.models.label_data import LabelData
from app.renderer import LabelRenderer
from backend.services.qr.storage import LocalShareStorage
from infrastructure.history_repository import HistoryRecord, HistoryRepository
from infrastructure.qr_share_repository import QrShareRecord, QrShareRepository


class ShareConfigurationError(RuntimeError):
    pass


class ShareStorageError(RuntimeError):
    pass


class QrShareService:
    def __init__(
        self,
        history_repository: HistoryRepository,
        share_repository: QrShareRepository,
        storage: LocalShareStorage,
        public_base_url: str,
        ttl_days: int = 7,
        renderer: LabelRenderer | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.history_repository = history_repository
        self.share_repository = share_repository
        self.storage = storage
        self.public_base_url = public_base_url.rstrip("/")
        self.ttl_days = ttl_days
        self.renderer = renderer or LabelRenderer()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def create_or_reuse(self, history_id: UUID) -> QrShareRecord:
        self._validate_configuration()
        now = self._utc(self.clock())
        cleanup_expired_shares(self.share_repository, self.storage, now)

        active = self.share_repository.get_active_for_history(history_id, now)
        local_url_prefix = f"{self.public_base_url}/share/"
        if (
            active is not None
            and active.public_url.startswith(local_url_prefix)
            and self.storage.assets_exist(
                active.image_asset_path,
                active.page_asset_path,
            )
        ):
            return active

        history = self.history_repository.get(history_id)
        if history is None:
            raise LookupError("History item not found.")

        source_path = Path(history.image_path)
        if not source_path.is_file():
            raise FileNotFoundError("History image is no longer available.")

        token = secrets.token_urlsafe(32)
        public_url = f"{local_url_prefix}{token}"
        expires_at = now + timedelta(days=self.ttl_days)
        page_html = build_mobile_share_page(
            history=history,
            image_url=f"/share/{token}/image.png",
            expires_at=expires_at,
        )

        try:
            assets = self.storage.store_assets(token, source_path, page_html)
        except Exception as exc:
            raise ShareStorageError("Could not store the local QR share.") from exc

        qr_image_path: str | None = None
        try:
            render_result = self.renderer.render(
                LabelData(
                    title="Scan to View",
                    body=f"Available until {expires_at:%Y-%m-%d}",
                    qr_data=public_url,
                    label_type=LabelType.QR,
                )
            )
            qr_image_path = render_result.file
            return self.share_repository.create(
                share_id=uuid4(),
                history_id=history_id,
                token=token,
                image_asset_path=assets.image_path,
                page_asset_path=assets.page_path,
                public_url=public_url,
                qr_image_path=qr_image_path,
                expires_at=expires_at,
            )
        except Exception as exc:
            self.storage.delete_assets(assets.image_path, assets.page_path)
            if qr_image_path:
                Path(qr_image_path).unlink(missing_ok=True)
            raise ShareStorageError("Could not finish the local QR share.") from exc

    def _validate_configuration(self) -> None:
        if self.ttl_days < 1:
            raise ShareConfigurationError("QR_SHARE_TTL_DAYS must be at least 1.")

        try:
            parsed = urlsplit(self.public_base_url)
            _ = parsed.port
        except ValueError as exc:
            raise ShareConfigurationError(
                "QR_SHARE_BASE_URL must contain a valid URL and port."
            ) from exc

        hostname = (parsed.hostname or "").lower()
        if (
            parsed.scheme not in {"http", "https"}
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ShareConfigurationError(
                "QR_SHARE_BASE_URL must be an HTTP or HTTPS origin without a path."
            )

        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None

        if hostname == "localhost" or (address is not None and address.is_loopback):
            raise ShareConfigurationError(
                "QR_SHARE_BASE_URL cannot use localhost or a loopback address."
            )

        if parsed.scheme == "http" and not self._is_private_lan_ipv4(address):
            raise ShareConfigurationError(
                "Public QR share URLs must use HTTPS; HTTP is allowed only for private LAN IPv4 addresses."
            )

    @staticmethod
    def _is_private_lan_ipv4(
        address: ipaddress.IPv4Address | ipaddress.IPv6Address | None,
    ) -> bool:
        if not isinstance(address, ipaddress.IPv4Address):
            return False
        return any(
            address in network
            for network in (
                ipaddress.ip_network("10.0.0.0/8"),
                ipaddress.ip_network("172.16.0.0/12"),
                ipaddress.ip_network("192.168.0.0/16"),
            )
        )

    @staticmethod
    def _utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


def cleanup_expired_shares(
    repository: QrShareRepository,
    storage: LocalShareStorage,
    now: datetime | None = None,
) -> int:
    removed = 0
    for share in repository.list_expired(now):
        try:
            storage.delete_assets(share.image_asset_path, share.page_asset_path)
            removed += 1
        except (OSError, ValueError):
            continue
    return removed


def build_mobile_share_page(
    history: HistoryRecord,
    image_url: str,
    expires_at: datetime,
) -> str:
    title = html.escape(history.title, quote=True)
    prompt = html.escape(history.prompt, quote=True)
    safe_image_url = html.escape(image_url, quote=True)
    expiry_iso = expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    expiry_json = json.dumps(expiry_iso)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="robots" content="noindex,nofollow,noarchive">
  <title>{title} · PrintSensei</title>
  <style>
    :root {{ color-scheme: dark; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; background: #0d0d0d; color: #eee; }}
    main {{ width: min(92vw, 680px); margin: 0 auto; padding: 28px 0 40px; }}
    h1 {{ margin: 0 0 8px; font-size: 1.5rem; }}
    .prompt,.expiry {{ color: #aaa; line-height: 1.5; }}
    img {{ display: block; width: 100%; max-height: 70vh; margin: 22px 0; object-fit: contain; background: white; }}
    a {{ display: inline-block; padding: 12px 18px; border-radius: 6px; background: #5b8dee; color: white; text-decoration: none; font-weight: 650; }}
  </style>
</head>
<body>
  <main id="share">
    <h1>{title}</h1>
    <p class="prompt">{prompt}</p>
    <img src="{safe_image_url}" alt="{title}">
    <a href="{safe_image_url}" download="printsensei-image.png">Download image</a>
    <p class="expiry">This share expires <time id="expiry" datetime="{expiry_iso}">{expiry_iso}</time>.</p>
  </main>
  <script>
    const expiry = new Date({expiry_json});
    if (Date.now() >= expiry.getTime()) {{
      document.getElementById('share').innerHTML = '<h1>Share expired</h1><p class="prompt">This PrintSensei link is no longer available.</p>';
    }} else {{
      document.getElementById('expiry').textContent = expiry.toLocaleString();
    }}
  </script>
</body>
</html>"""
