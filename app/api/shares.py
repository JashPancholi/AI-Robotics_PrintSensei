from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse

from app.enums.status import Status
from app.schemas.share import QrSharePrintResponse, QrShareResponse
from app.schemas.study import PreviewAsset
from backend.services.qr import (
    LocalShareStorage,
    QrShareService,
    ShareConfigurationError,
    ShareStorageError,
)
from infrastructure.history_repository import HistoryRepository
from infrastructure.qr_share_repository import QrShareRecord, QrShareRepository
from shared.config import (
    HARDWARE_MODE,
    QR_SHARE_BASE_URL,
    QR_LOCAL_STORAGE_DIR,
    QR_SHARE_TTL_DAYS,
)

router = APIRouter(prefix="/api", tags=["shares"])
public_router = APIRouter(tags=["public shares"])


def get_qr_share_repository() -> QrShareRepository:
    return QrShareRepository()


def get_local_share_storage() -> LocalShareStorage:
    return LocalShareStorage(QR_LOCAL_STORAGE_DIR)


def get_qr_share_service() -> QrShareService:
    return QrShareService(
        history_repository=HistoryRepository(),
        share_repository=QrShareRepository(),
        storage=get_local_share_storage(),
        public_base_url=QR_SHARE_BASE_URL,
        ttl_days=QR_SHARE_TTL_DAYS,
    )


def _share_response(record: QrShareRecord) -> QrShareResponse:
    return QrShareResponse(
        id=record.id,
        history_id=record.history_id,
        public_url=record.public_url,
        qr_preview=PreviewAsset(
            url=f"/generated-labels/{Path(record.qr_image_path).name}",
            width=384,
            height=_image_height(record.qr_image_path),
        ),
        created_at=record.created_at,
        expires_at=record.expires_at,
        print_count=record.print_count,
    )


def _image_height(image_path: str) -> int:
    try:
        from PIL import Image

        with Image.open(image_path) as image:
            return image.height
    except (FileNotFoundError, OSError):
        return 384


def _get_available_share(
    token: str,
    repository: QrShareRepository,
    storage: LocalShareStorage,
) -> QrShareRecord:
    record = repository.get_by_token(token)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR share not found.")
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        try:
            storage.delete_assets(record.image_asset_path, record.page_asset_path)
        except (OSError, ValueError):
            pass
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="QR share has expired.")
    return record


@router.post("/history/{history_id}/share", response_model=QrShareResponse)
def create_history_share(
    history_id: UUID,
    service: QrShareService = Depends(get_qr_share_service),
) -> QrShareResponse:
    try:
        return _share_response(service.create_or_reuse(history_id))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc)) from exc
    except ShareConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except ShareStorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/shares/{share_id}/print", response_model=QrSharePrintResponse)
def print_qr_share(
    share_id: UUID,
    repository: QrShareRepository = Depends(get_qr_share_repository),
) -> QrSharePrintResponse:
    record = repository.get(share_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR share not found.")
    if not Path(record.qr_image_path).is_file():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="QR image is no longer available.")

    updated = repository.mark_printed(share_id)
    simulated = HARDWARE_MODE.lower() == "pc"
    return QrSharePrintResponse(
        share_id=share_id,
        status=Status.DONE,
        message="QR print simulated successfully." if simulated else "QR print job completed.",
        print_count=updated.print_count,
    )


@public_router.get("/share/{token}", response_class=HTMLResponse)
def view_qr_share(
    token: str,
    repository: QrShareRepository = Depends(get_qr_share_repository),
    storage: LocalShareStorage = Depends(get_local_share_storage),
) -> HTMLResponse:
    record = _get_available_share(token, repository, storage)
    try:
        page_path = storage.resolve_asset(record.page_asset_path)
        content = page_path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="QR share page is no longer available.",
        ) from exc
    # Repair pages created before image URLs included their share token. Relative
    # URLs resolve against `/share/{token}` as if `{token}` were a filename.
    image_url = f"/share/{token}/image.png"
    content = content.replace('src="./image.png"', f'src="{image_url}"')
    content = content.replace('href="./image.png"', f'href="{image_url}"')
    return HTMLResponse(content, headers={"Cache-Control": "no-store"})


@public_router.get("/share/{token}/image.png", response_class=FileResponse)
def view_qr_share_image(
    token: str,
    repository: QrShareRepository = Depends(get_qr_share_repository),
    storage: LocalShareStorage = Depends(get_local_share_storage),
) -> FileResponse:
    record = _get_available_share(token, repository, storage)
    try:
        image_path = storage.resolve_asset(record.image_asset_path)
        if not image_path.is_file():
            raise FileNotFoundError
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="QR share image is no longer available.",
        ) from exc
    return FileResponse(
        image_path,
        media_type="image/png",
        headers={"Cache-Control": "no-store"},
    )
