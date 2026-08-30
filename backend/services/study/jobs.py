from dataclasses import dataclass, replace
from threading import Lock
from typing import Callable
from uuid import UUID, uuid4

from app.enums.status import Status
from backend.services.study.service import (
    StudyGenerationResult,
    StudyService,
    StudyServiceError,
)


@dataclass
class StudyJobSnapshot:
    request_id: UUID
    text: str
    detail_level: str
    status: Status = Status.RECEIVED
    progress: int = 0
    stage: str = "Queued"
    result: StudyGenerationResult | None = None
    error: str | None = None


class StudyJobManager:
    def __init__(
        self,
        service_factory: Callable[[], StudyService] = StudyService,
        on_complete: Callable[[str, StudyGenerationResult], None] | None = None,
    ) -> None:
        self.service_factory = service_factory
        self.on_complete = on_complete
        self._jobs: dict[UUID, StudyJobSnapshot] = {}
        self._lock = Lock()

    def create(self, text: str, detail_level: str) -> StudyJobSnapshot:
        job = StudyJobSnapshot(
            request_id=uuid4(),
            text=text,
            detail_level=detail_level,
        )
        with self._lock:
            self._jobs[job.request_id] = job
        return replace(job)

    def get(self, request_id: UUID) -> StudyJobSnapshot | None:
        with self._lock:
            job = self._jobs.get(request_id)
            return replace(job) if job else None

    def run(self, request_id: UUID) -> None:
        job = self.get(request_id)
        if job is None:
            return

        self._update(request_id, status=Status.PROCESSING, progress=1, stage="Starting")
        try:
            result = self.service_factory().generate(
                job.text,
                job.detail_level,
                progress_callback=lambda progress, stage: self._update(
                    request_id,
                    progress=progress,
                    stage=stage,
                ),
            )
            result = replace(result, request_id=request_id)
            if self.on_complete:
                self.on_complete(job.text, result)
        except Exception as exc:
            message = (
                str(exc)
                if isinstance(exc, StudyServiceError)
                else "Study generation failed unexpectedly."
            )
            self._update(
                request_id,
                status=Status.ERROR,
                stage="Generation failed",
                error=message,
            )
            return

        self._update(
            request_id,
            status=Status.READY,
            progress=100,
            stage="Ready",
            result=result,
        )

    def _update(self, request_id: UUID, **changes) -> None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is None:
                return
            for field, value in changes.items():
                setattr(job, field, value)
