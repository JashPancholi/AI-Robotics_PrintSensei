import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.enums.status import Status
from app.renderer import RenderResult
from backend.services.study import GeneratedStudyContent, StudyGenerationResult
from backend.services.study.jobs import StudyJobManager


class FakeProgressStudyService:
    def generate(self, text, detail_level, progress_callback):
        assert text == "Explain binary search"
        assert detail_level == "medium"
        progress_callback(15, "Generating study points")
        progress_callback(80, "Rendering label preview")
        return StudyGenerationResult(
            request_id=uuid4(),
            content=GeneratedStudyContent(
                title="Binary Search",
                points=["Repeatedly halves a sorted search range."],
            ),
            render=RenderResult(
                status="success",
                file="generated_labels/label_00001.png",
                width=384,
                height=200,
            ),
        )


def test_job_manager_reports_completed_stage_progress_and_result():
    saved = []
    manager = StudyJobManager(
        service_factory=FakeProgressStudyService,
        on_complete=lambda prompt, result: saved.append((prompt, result)),
    )
    created = manager.create("Explain binary search", "medium")

    assert created.status is Status.RECEIVED
    assert created.progress == 0

    manager.run(created.request_id)
    completed = manager.get(created.request_id)

    assert completed.status is Status.READY
    assert completed.progress == 100
    assert completed.stage == "Ready"
    assert completed.result.request_id == created.request_id
    assert saved == [("Explain binary search", completed.result)]
