from dataclasses import dataclass, replace
from threading import Lock
import traceback
from typing import Any, Callable
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
    image: str | None = None
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

    def _update(self, request_id: UUID, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(request_id)
            if job is not None:
                self._jobs[request_id] = replace(job, **kwargs)

    def create(self, text: str, detail_level: str, image: str | None = None) -> StudyJobSnapshot:
        job = StudyJobSnapshot(
            request_id=uuid4(),
            text=text,
            detail_level=detail_level,
            image=image,
        )
        with self._lock:
            self._jobs[job.request_id] = job
        return replace(job)

    def get(self, request_id: UUID) -> StudyJobSnapshot | None:
        with self._lock:
            job = self._jobs.get(request_id)
            return replace(job) if job is not None else None

    def run(self, request_id: UUID) -> None:
        job = self.get(request_id)
        if job is None:
            return

        self._update(request_id, status=Status.PROCESSING, progress=5, stage="Starting")
        try:
            result = self.service_factory().generate(
                job.text,
                job.detail_level,
                image=job.image,
                progress_callback=lambda progress, stage: self._update(
                    request_id,
                    progress=progress,
                    stage=stage,
                ),
            )
            self._update(
                request_id,
                status=Status.READY,
                progress=100,
                stage="Completed",
                result=result,
            )
            if self.on_complete:
                self.on_complete(job.text, result)
        except Exception as exc:
            traceback.print_exc()
            self._update(
                request_id,
                status=Status.ERROR,
                stage="Failed",
                error=str(exc),
            )