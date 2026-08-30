import os

from dotenv import load_dotenv

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "PrintSensei")
APP_VERSION = os.getenv("APP_VERSION", "0.1")
MODE = os.getenv("MODE", "development")
HARDWARE_MODE = os.getenv("HARDWARE_MODE", "pc")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app/database/printsensei.db")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = tuple(
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
)
QR_SHARE_BASE_URL = os.getenv(
    "QR_SHARE_BASE_URL",
    os.getenv("QR_LOCAL_BASE_URL", ""),
).rstrip("/")
QR_LOCAL_STORAGE_DIR = os.getenv("QR_LOCAL_STORAGE_DIR", "shared_content/shares")
QR_SHARE_TTL_DAYS = int(os.getenv("QR_SHARE_TTL_DAYS", "7"))
