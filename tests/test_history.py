import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.history import get_history_repository
from app.main import app
from infrastructure.database_models import Base
from infrastructure.history_repository import HistoryRepository

client = TestClient(app)


def create_repository() -> HistoryRepository:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine)
    return HistoryRepository(session_factory=testing_session)


def test_history_repository_persists_generation_and_print_metadata():
    repository = create_repository()
    request_id = uuid4()
    repository.create(
        request_id=request_id,
        prompt="a cheap mouse internal working diagram",
        title="Mouse Internal Working",
        image_path="diagram_images/human_heart.png",
        content_type="diagram",
        width=384,
        height=384,
    )

    records = repository.list()
    printed = repository.mark_printed(request_id)

    assert len(records) == 1
    assert records[0].prompt == "a cheap mouse internal working diagram"
    assert records[0].image_path == "diagram_images/human_heart.png"
    assert printed.print_count == 1
    assert printed.last_printed_at is not None


def test_history_api_lists_previews_and_records_simulated_print():
    repository = create_repository()
    request_id = uuid4()
    repository.create(
        request_id=request_id,
        prompt="mouse diagram",
        title="Mouse Diagram",
        image_path="diagram_images/human_heart.png",
        content_type="diagram",
        width=384,
        height=384,
    )
    app.dependency_overrides[get_history_repository] = lambda: repository
    try:
        listing = client.get("/api/history")
        printing = client.post(f"/api/history/{request_id}/print")
    finally:
        app.dependency_overrides.pop(get_history_repository, None)

    assert listing.status_code == 200
    assert listing.json()["items"][0]["preview"] == {
        "url": "/diagram-images/human_heart.png",
        "width": 384,
        "height": 384,
    }
    assert printing.status_code == 200
    assert printing.json()["status"] == "done"
    assert printing.json()["print_count"] == 1
