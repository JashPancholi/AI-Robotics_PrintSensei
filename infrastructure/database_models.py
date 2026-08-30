from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SystemStatus(Base):
    __tablename__ = "system_status"

    id = Column(Integer, primary_key=True, index=True)
    component = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)


class HistoryEntry(Base):
    __tablename__ = "history_entries"

    id = Column(String(36), primary_key=True)
    prompt = Column(Text, nullable=False)
    title = Column(String(120), nullable=False)
    image_path = Column(String(500), nullable=False)
    content_type = Column(String(20), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    last_printed_at = Column(DateTime(timezone=True), nullable=True)
    print_count = Column(Integer, nullable=False, default=0)


class QrShare(Base):
    __tablename__ = "qr_shares"

    id = Column(String(36), primary_key=True)
    history_id = Column(
        String(36),
        ForeignKey("history_entries.id"),
        nullable=False,
        index=True,
    )
    token = Column(String(128), nullable=False, unique=True, index=True)
    # Keep the original SQL column names so existing development databases remain
    # readable after switching the share provider from Azure to local storage.
    image_asset_path = Column("azure_image_path", String(500), nullable=False)
    page_asset_path = Column("azure_page_path", String(500), nullable=False)
    public_url = Column(String(1000), nullable=False)
    qr_image_path = Column(String(500), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_printed_at = Column(DateTime(timezone=True), nullable=True)
    print_count = Column(Integer, nullable=False, default=0)
