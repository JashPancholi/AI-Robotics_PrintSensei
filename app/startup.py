from infrastructure.database import init_db
from infrastructure.qr_share_repository import QrShareRepository
from backend.services.qr import LocalShareStorage, cleanup_expired_shares
from shared.config import QR_LOCAL_STORAGE_DIR
from shared.logging_config import get_logger

logger = get_logger("startup")


def initialize_app() -> None:
    init_db()
    cleanup_expired_shares(
        QrShareRepository(),
        LocalShareStorage(QR_LOCAL_STORAGE_DIR),
    )
    logger.info("PrintSensei startup complete")
