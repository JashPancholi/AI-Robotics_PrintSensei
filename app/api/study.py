from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.enums.status import Status
from app.schemas.study import (
    PreviewAsset,
    StudyGenerateRequest,
    StudyGenerateResponse,
    StudyJobStartResponse,
    StudyJobStatusResponse,
    StudyLabelPayload,
    StudyPrintResponse,
)
from backend.services.study import (
    StudyGenerationResult,
    StudyJobManager,
    StudyService,
    StudyServiceError,
)
from infrastructure.history_repository import HistoryRepository

router = APIRouter(prefix="/api/study", tags=["study"])
history_repository = HistoryRepository()


def _save_history(
    repository: HistoryRepository,
    prompt: str,
    result: StudyGenerationResult,
) -> None:
    repository.create(
        request_id=result.request_id,
        prompt=prompt,
        title=result.content.title,
        image_path=result.render.file,
        content_type=result.content_type,
        width=result.render.width,
        height=result.render.height,
    )


job_manager = StudyJobManager(
    on_complete=lambda prompt, result: _save_history(
        history_repository,
        prompt,
        result,
    )
)


def get_study_service() -> StudyService:
    return StudyService()


def get_study_job_manager() -> StudyJobManager:
    return job_manager


def get_generation_history_repository() -> HistoryRepository:
    return history_repository


def _generation_response(result: StudyGenerationResult) -> StudyGenerateResponse:
    return StudyGenerateResponse(
        request_id=result.request_id,
        status=Status.READY,
        label=StudyLabelPayload(
            title=result.content.title,
            points=result.content.points,
            content_type=result.content_type,
        ),
        preview=PreviewAsset(
            url=result.preview_url,
            width=result.render.width,
            height=result.render.height,
        ),
    )


@router.post(
    "/generate",
    response_model=StudyGenerateResponse,
    responses={status.HTTP_502_BAD_GATEWAY: {"description": "Study generation or rendering failed."}},
)
def generate_study_label(
    payload: StudyGenerateRequest,
    service: StudyService = Depends(get_study_service),
    repository: HistoryRepository = Depends(get_generation_history_repository),
) -> StudyGenerateResponse:
    try:
        result = service.generate(payload.text, payload.detail_level)
    except StudyServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    _save_history(repository, payload.text, result)
    return _generation_response(result)


@router.post(
    "/jobs",
    response_model=StudyJobStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_study_job(
    payload: StudyGenerateRequest,
    background_tasks: BackgroundTasks,
    manager: StudyJobManager = Depends(get_study_job_manager),
) -> StudyJobStartResponse:
    job = manager.create(payload.text, payload.detail_level)
    background_tasks.add_task(manager.run, job.request_id)
    return StudyJobStartResponse(
        request_id=job.request_id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
    )


@router.get("/jobs/{request_id}", response_model=StudyJobStatusResponse)
def get_study_job(
    request_id: UUID,
    manager: StudyJobManager = Depends(get_study_job_manager),
) -> StudyJobStatusResponse:
    job = manager.get(request_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study job not found.")

    return StudyJobStatusResponse(
        request_id=job.request_id,
        status=job.status,
        progress=job.progress,
        stage=job.stage,
        result=_generation_response(job.result) if job.result else None,
        error=job.error,
    )


@router.post(
    "/{request_id}/print",
    response_model=StudyPrintResponse,
    responses={status.HTTP_501_NOT_IMPLEMENTED: {"description": "Study printing is not implemented yet."}},
)
def print_study_label(request_id: UUID) -> StudyPrintResponse:
    del request_id
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Study printing will be implemented after preview generation.",
    )
