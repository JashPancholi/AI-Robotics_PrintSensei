from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.database import SessionLocal
from infrastructure.database_models import HistoryEntry


@dataclass(frozen=True)
class HistoryRecord:
    id: UUID
    prompt: str
    title: str
    image_path: str
    content_type: str
    width: int
    height: int
    created_at: datetime
    last_printed_at: datetime | None
    print_count: int


class HistoryRepository:
    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self.session_factory = session_factory

    def create(
        self,
        request_id: UUID,
        prompt: str,
        title: str,
        image_path: str | Path,
        content_type: str,
        width: int,
        height: int,
    ) -> HistoryRecord:
        with self.session_factory() as session:
            existing = session.get(HistoryEntry, str(request_id))
            if existing:
                return self._to_record(existing)

            entry = HistoryEntry(
                id=str(request_id),
                prompt=prompt,
                title=title,
                image_path=Path(image_path).as_posix(),
                content_type=content_type,
                width=width,
                height=height,
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return self._to_record(entry)

    def list(self) -> list[HistoryRecord]:
        with self.session_factory() as session:
            entries = (
                session.query(HistoryEntry)
                .order_by(HistoryEntry.created_at.desc())
                .all()
            )
            return [self._to_record(entry) for entry in entries]

    def get(self, request_id: UUID) -> HistoryRecord | None:
        with self.session_factory() as session:
            entry = session.get(HistoryEntry, str(request_id))
            return self._to_record(entry) if entry else None

    def mark_printed(self, request_id: UUID) -> HistoryRecord | None:
        with self.session_factory() as session:
            entry = session.get(HistoryEntry, str(request_id))
            if entry is None:
                return None
            entry.print_count += 1
            entry.last_printed_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(entry)
            return self._to_record(entry)

    @staticmethod
    def _to_record(entry: HistoryEntry) -> HistoryRecord:
        return HistoryRecord(
            id=UUID(entry.id),
            prompt=entry.prompt,
            title=entry.title,
            image_path=entry.image_path,
            content_type=entry.content_type,
            width=entry.width,
            height=entry.height,
            created_at=entry.created_at,
            last_printed_at=entry.last_printed_at,
            print_count=entry.print_count,
        )
