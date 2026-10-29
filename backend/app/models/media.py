from datetime import datetime

from app.extensions import db
from app.models.mixins import MetadataMixin, UUIDMixin
from flask import current_app
from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column


class MediaAsset(UUIDMixin, MetadataMixin, db.Model):
    __tablename__ = "media_asset"

    filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str] = mapped_column(String(80), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True
    )
    alt_text: Mapped[str | None] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    @property
    def url(self) -> str:
        base = current_app.config["PUBLIC_MEDIA_URL"].rstrip("/")
        return f"{base}/{self.filename}"

    def __repr__(self) -> str:
        return f"<MediaAsset {self.filename}>"
