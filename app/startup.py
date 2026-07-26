from infrastructure.database import init_db
from shared.logging_config import get_logger

logger = get_logger("startup")


def initialize_app() -> None:
    init_db()
    logger.info("PrintSensei startup complete")
