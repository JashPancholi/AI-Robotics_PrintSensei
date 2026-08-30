from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.enums.status import Status
from app.schemas.history import (
    HistoryItemResponse,
    HistoryListResponse,
    HistoryPrintResponse,
)
from app.schemas.study import PreviewAsset
from infrastructure.history_repository import HistoryRecord, HistoryRepository
from shared.config import HARDWARE_MODE

router = APIRouter(prefix="/api/history", tags=["history"])


def get_history_repository() -> HistoryRepository:
    return HistoryRepository()


def _history_response(record: HistoryRecord) -> HistoryItemResponse:
    route = "diagram-images" if record.content_type == "diagram" else "generated-labels"
    return HistoryItemResponse(
        id=record.id,
        prompt=record.prompt,
        title=record.title,
        content_type=record.content_type,
        preview=PreviewAsset(
            url=f"/{route}/{Path(record.image_path).name}",
            width=record.width,
            height=record.height,
        ),
        created_at=record.created_at,
        last_printed_at=record.last_printed_at,
        print_count=record.print_count,
    )


@router.get("", response_model=HistoryListResponse)
def list_history(
    repository: HistoryRepository = Depends(get_history_repository),
) -> HistoryListResponse:
    return HistoryListResponse(
        items=[_history_response(record) for record in repository.list()]
    )


@router.get("/{request_id}", response_model=HistoryItemResponse)
def get_history_item(
    request_id: UUID,
    repository: HistoryRepository = Depends(get_history_repository),
) -> HistoryItemResponse:
    record = repository.get(request_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found.")
    return _history_response(record)


@router.post("/{request_id}/print", response_model=HistoryPrintResponse)
def print_history_item(
    request_id: UUID,
    repository: HistoryRepository = Depends(get_history_repository),
) -> HistoryPrintResponse:
    record = repository.get(request_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History item not found.")
    if not Path(record.image_path).is_file():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="History image is no longer available.")

    updated = repository.mark_printed(request_id)
    simulated = HARDWARE_MODE.lower() == "pc"
    return HistoryPrintResponse(
        request_id=request_id,
        status=Status.DONE,
        message="Print simulated successfully." if simulated else "Print job completed.",
        print_count=updated.print_count,
    )
