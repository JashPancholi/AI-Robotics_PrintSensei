import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.api.study import (
    get_generation_history_repository,
    get_study_job_manager,
    get_study_service,
)
from app.renderer import RenderResult
from app.schemas.study import StudyGenerateRequest
from backend.services.study import (
    GeneratedStudyContent,
    StudyGenerationResult,
    StudyServiceError,
)
from backend.services.study.jobs import StudyJobManager

client = TestClient(app)


def test_study_routes_are_published_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]

    assert "/api/study/generate" in paths
    assert "/api/study/jobs" in paths
    assert "/api/study/jobs/{request_id}" in paths
    assert "/api/study/{request_id}/print" in paths


def test_vite_development_origin_is_allowed_by_cors():
    response = client.options(
        "/api/study/generate",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_study_request_normalizes_text_and_defaults_detail_level():
    request = StudyGenerateRequest(text="  Explain binary search  ")

    assert request.text == "Explain binary search"
    assert request.detail_level == "medium"


def test_generate_rejects_blank_text():
    response = client.post("/api/study/generate", json={"text": "   "})

    assert response.status_code == 422


def test_generate_rejects_unknown_detail_level():
    response = client.post(
        "/api/study/generate",
        json={"text": "Explain binary search", "detail_level": "extreme"},
    )

    assert response.status_code == 422


def test_generate_returns_structured_study_preview():
    request_id = uuid4()

    class FakeStudyService:
        def generate(self, text, detail_level):
            assert text == "Explain binary search"
            assert detail_level == "low"
            return StudyGenerationResult(
                request_id=request_id,
                content=GeneratedStudyContent(
                    title="Binary Search",
                    points=["Searches a sorted collection by repeatedly halving it."],
                ),
                render=RenderResult(
                    status="success",
                    file="generated_labels/label_00001.png",
                    width=384,
                    height=240,
                ),
            )

    class FakeHistoryRepository:
        def create(self, **values):
            assert values["request_id"] == request_id
            assert values["prompt"] == "Explain binary search"

    app.dependency_overrides[get_study_service] = lambda: FakeStudyService()
    app.dependency_overrides[get_generation_history_repository] = lambda: FakeHistoryRepository()
    try:
        response = client.post(
            "/api/study/generate",
            json={"text": "Explain binary search", "detail_level": "low"},
        )
    finally:
        app.dependency_overrides.pop(get_study_service, None)
        app.dependency_overrides.pop(get_generation_history_repository, None)

    assert response.status_code == 200
    assert response.json() == {
        "request_id": str(request_id),
        "status": "ready",
        "label": {
            "title": "Binary Search",
            "points": ["Searches a sorted collection by repeatedly halving it."],
            "content_type": "notes",
            "label_type": "study",
        },
        "preview": {
            "url": "/generated-labels/label_00001.png",
            "width": 384,
            "height": 240,
        },
    }


def test_generate_returns_clean_gateway_error_when_service_fails():
    class FailingStudyService:
        def generate(self, text, detail_level):
            raise StudyServiceError("The AI service could not generate valid study content.")

    app.dependency_overrides[get_study_service] = lambda: FailingStudyService()
    try:
        response = client.post(
            "/api/study/generate",
            json={"text": "Explain binary search"},
        )
    finally:
        app.dependency_overrides.pop(get_study_service, None)

    assert response.status_code == 502
    assert response.json() == {
        "detail": "The AI service could not generate valid study content."
    }


def test_job_endpoints_return_progress_and_completed_result():
    class FakeJobService:
        def generate(self, text, detail_level, progress_callback):
            progress_callback(70, "Study content generated")
            return StudyGenerationResult(
                request_id=uuid4(),
                content=GeneratedStudyContent(
                    title="Binary Search",
                    points=["Repeatedly halves a sorted search range."],
                ),
                render=RenderResult(
                    status="success",
                    file="generated_labels/label_00002.png",
                    width=384,
                    height=200,
                ),
            )

    manager = StudyJobManager(service_factory=FakeJobService)
    app.dependency_overrides[get_study_job_manager] = lambda: manager
    try:
        started = client.post(
            "/api/study/jobs",
            json={"text": "Explain binary search"},
        )
        request_id = started.json()["request_id"]
        completed = client.get(f"/api/study/jobs/{request_id}")
    finally:
        app.dependency_overrides.pop(get_study_job_manager, None)

    assert started.status_code == 202
    assert started.json()["progress"] == 0
    assert completed.status_code == 200
    assert completed.json()["status"] == "ready"
    assert completed.json()["progress"] == 100
    assert completed.json()["result"]["preview"]["width"] == 384


def test_print_requires_a_uuid_request_id():
    response = client.post("/api/study/not-a-uuid/print")

    assert response.status_code == 422
