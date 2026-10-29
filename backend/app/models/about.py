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
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym


class Education(
    UUIDMixin,
    TimestampMixin,
    MetadataMixin,
    OrderedMixin,
    PublishableMixin,
    LanguageRowMixin,
    db.Model,
):
    """One row per language; rows sharing ``education_id`` are the same study."""

    __tablename__ = "education"
    __table_args__ = (
        UniqueConstraint(
            "education_id", "language", name="uq_education_group_language"
        ),
        CheckConstraint("language IN ('es', 'en')", name="ck_education_language"),
    )

    education_id: Mapped[uuid.UUID] = group_column("education_id")
    group_id = synonym("education_id")

    # language-neutral
    institution: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    credential_url: Mapped[str | None] = mapped_column(String(500))
    logo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="SET NULL")
    )

    # translated
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_label: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)

    logo: Mapped[MediaAsset | None] = relationship(MediaAsset, lazy="joined")

    NEUTRAL_FIELDS = (
        "institution",
        "start_date",
        "end_date",
        "credential_url",
        "logo_id",
        "display_order",
        "is_published",
    )
    TEXT_FIELDS = ("title", "institution_label", "description")


class Experience(
    UUIDMixin,
    TimestampMixin,
    MetadataMixin,
    OrderedMixin,
    PublishableMixin,
    LanguageRowMixin,
    db.Model,
):
    __tablename__ = "experience"
    __table_args__ = (
        UniqueConstraint(
            "experience_id", "language", name="uq_experience_group_language"
        ),
        CheckConstraint("language IN ('es', 'en')", name="ck_experience_language"),
    )

    experience_id: Mapped[uuid.UUID] = group_column("experience_id")
    group_id = synonym("experience_id")

    # language-neutral
    company: Mapped[str] = mapped_column(String(200), nullable=False)
    company_url: Mapped[str | None] = mapped_column(String(500))
    location: Mapped[str | None] = mapped_column(String(160))
    employment_type: Mapped[str | None] = mapped_column(String(40))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    logo_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="SET NULL")
    )

    # translated
    role: Mapped[str] = mapped_column(String(200), nullable=False)
    company_label: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    highlights: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    logo: Mapped[MediaAsset | None] = relationship(MediaAsset, lazy="joined")

    NEUTRAL_FIELDS = (
        "company",
        "company_url",
        "location",
        "employment_type",
        "start_date",
        "end_date",
        "is_current",
        "logo_id",
        "display_order",
        "is_published",
    )
    TEXT_FIELDS = ("role", "company_label", "description", "highlights")


class LanguageSkill(
    UUIDMixin,
    TimestampMixin,
    MetadataMixin,
    OrderedMixin,
    PublishableMixin,
    LanguageRowMixin,
    db.Model,
):
    """A language she speaks.

    Two different meanings of "language" meet here: ``code`` is the language the
    skill is about ("en" = English), while ``language`` is the language this row
    is written in.
    """

    __tablename__ = "language_skill"
    __table_args__ = (
        UniqueConstraint(
            "language_skill_id", "language", name="uq_language_skill_group_language"
        ),
        UniqueConstraint("code", "language", name="uq_language_skill_code_language"),
        CheckConstraint("language IN ('es', 'en')", name="ck_language_skill_language"),
        CheckConstraint(
            "percentage >= 0 AND percentage <= 100", name="ck_language_skill_percentage"
        ),
    )

    language_skill_id: Mapped[uuid.UUID] = group_column("language_skill_id")
    group_id = synonym("language_skill_id")

    # language-neutral
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    percentage: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    cefr_level: Mapped[str | None] = mapped_column(String(10))

    # translated
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    level_label: Mapped[str | None] = mapped_column(String(80))

    NEUTRAL_FIELDS = (
        "code",
        "percentage",
        "cefr_level",
        "display_order",
        "is_published",
    )
    TEXT_FIELDS = ("name", "level_label")
