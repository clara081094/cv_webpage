import uuid
from datetime import date

from app.extensions import db
from app.models.media import MediaAsset
from app.models.mixins import (
    LanguageRowMixin,
    MetadataMixin,
    OrderedMixin,
    PublishableMixin,
    TimestampMixin,
    UUIDMixin,
    group_column,
)
from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym


class Bio(UUIDMixin, TimestampMixin, MetadataMixin, LanguageRowMixin, db.Model):
    """Contact card plus headline copy. One row per language.

    ``UNIQUE(language)`` keeps it a singleton: at most one row per language,
    therefore exactly one bio.
    """

    __tablename__ = "bio"
    __table_args__ = (
        UniqueConstraint("language", name="uq_bio_language"),
        UniqueConstraint("bio_id", "language", name="uq_bio_group_language"),
        CheckConstraint("language IN ('es', 'en')", name="ck_bio_language"),
    )

    bio_id: Mapped[uuid.UUID] = group_column("bio_id")
    group_id = synonym("bio_id")

    # language-neutral
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(160))
    resume_url: Mapped[str | None] = mapped_column(String(500))
    birth_date: Mapped[date | None] = mapped_column(Date)
    photo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="SET NULL")
    )

    # translated
    greeting: Mapped[str | None] = mapped_column(String(80))
    headline: Mapped[str | None] = mapped_column(String(255))
    tagline: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    role_label: Mapped[str | None] = mapped_column(String(160))

    photo: Mapped[MediaAsset | None] = relationship(MediaAsset, lazy="joined")

    NEUTRAL_FIELDS = (
        "full_name",
        "phone",
        "email",
        "location",
        "resume_url",
        "birth_date",
        "photo_id",
    )
    TEXT_FIELDS = ("greeting", "headline", "tagline", "summary", "role_label")


class SocialLink(
    UUIDMixin, TimestampMixin, MetadataMixin, OrderedMixin, PublishableMixin, db.Model
):
    """No language column: platform, url and label ("LinkedIn") are not translated."""

    __tablename__ = "social_link"

    platform: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    icon_name: Mapped[str] = mapped_column(String(40), nullable=False)

    def __repr__(self) -> str:
        return f"<SocialLink {self.platform}>"
