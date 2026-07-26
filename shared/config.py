from dotenv import load_dotenv
import os

load_dotenv()

APP_NAME = os.getenv("APP_NAME", "PrintSensei")
APP_VERSION = os.getenv("APP_VERSION", "0.1")
MODE = os.getenv("MODE", "development")
HARDWARE_MODE = os.getenv("HARDWARE_MODE", "pc")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app/database/printsensei.db")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
