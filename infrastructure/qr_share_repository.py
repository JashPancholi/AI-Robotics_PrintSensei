from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from infrastructure.database import SessionLocal
from infrastructure.database_models import QrShare


@dataclass(frozen=True)
class QrShareRecord:
    id: UUID
    history_id: UUID
    token: str
    image_asset_path: str
    page_asset_path: str
    public_url: str
    qr_image_path: str
    created_at: datetime
    expires_at: datetime
    last_printed_at: datetime | None
    print_count: int


class QrShareRepository:
    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self.session_factory = session_factory

    def create(
        self,
        share_id: UUID,
        history_id: UUID,
        token: str,
        image_asset_path: str,
        page_asset_path: str,
        public_url: str,
        qr_image_path: str | Path,
        expires_at: datetime,
    ) -> QrShareRecord:
        with self.session_factory() as session:
            entry = QrShare(
                id=str(share_id),
                history_id=str(history_id),
                token=token,
                image_asset_path=image_asset_path,
                page_asset_path=page_asset_path,
                public_url=public_url,
                qr_image_path=Path(qr_image_path).as_posix(),
                expires_at=expires_at,
            )
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return self._to_record(entry)

    def get(self, share_id: UUID) -> QrShareRecord | None:
        with self.session_factory() as session:
            entry = session.get(QrShare, str(share_id))
            return self._to_record(entry) if entry else None

    def get_by_token(self, token: str) -> QrShareRecord | None:
        with self.session_factory() as session:
            entry = session.query(QrShare).filter(QrShare.token == token).first()
            return self._to_record(entry) if entry else None

    def list_expired(self, now: datetime | None = None) -> list[QrShareRecord]:
        cutoff = now or datetime.now(timezone.utc)
        with self.session_factory() as session:
            entries = session.query(QrShare).filter(QrShare.expires_at <= cutoff).all()
            return [self._to_record(entry) for entry in entries]

    def get_active_for_history(
        self,
        history_id: UUID,
        now: datetime | None = None,
    ) -> QrShareRecord | None:
        cutoff = now or datetime.now(timezone.utc)
        with self.session_factory() as session:
            entry = (
                session.query(QrShare)
                .filter(QrShare.history_id == str(history_id))
                .order_by(QrShare.created_at.desc())
                .first()
            )
            if entry is None or self._as_utc(entry.expires_at) <= self._as_utc(cutoff):
                return None
            return self._to_record(entry)

    def mark_printed(self, share_id: UUID) -> QrShareRecord | None:
        with self.session_factory() as session:
            entry = session.get(QrShare, str(share_id))
            if entry is None:
                return None
            entry.print_count += 1
            entry.last_printed_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(entry)
            return self._to_record(entry)

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

    @classmethod
    def _to_record(cls, entry: QrShare) -> QrShareRecord:
        return QrShareRecord(
            id=UUID(entry.id),
            history_id=UUID(entry.history_id),
            token=entry.token,
            image_asset_path=entry.image_asset_path,
            page_asset_path=entry.page_asset_path,
            public_url=entry.public_url,
            qr_image_path=entry.qr_image_path,
            created_at=cls._as_utc(entry.created_at),
            expires_at=cls._as_utc(entry.expires_at),
            last_printed_at=(
                cls._as_utc(entry.last_printed_at) if entry.last_printed_at else None
            ),
            print_count=entry.print_count,
        )
