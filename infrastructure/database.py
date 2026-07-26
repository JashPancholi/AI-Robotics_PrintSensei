from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from shared.config import DATABASE_URL

DB_PATH = Path("app/database/printsensei.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db() -> None:
    from infrastructure.database_models import Base as ModelsBase

    ModelsBase.metadata.create_all(bind=engine)
