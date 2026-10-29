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
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym


class Project(
    UUIDMixin,
    TimestampMixin,
    MetadataMixin,
    OrderedMixin,
    PublishableMixin,
    LanguageRowMixin,
    db.Model,
):
    """One row per language; rows sharing ``project_id`` are the same project.

    ``tags`` and ``images`` are columns rather than join tables: a foreign key
    cannot point at an item that spans two rows.
    """

    __tablename__ = "project"
    __table_args__ = (
        UniqueConstraint("project_id", "language", name="uq_project_group_language"),
        # The slug is shared by both language rows, so it is unique per language.
        UniqueConstraint("slug", "language", name="uq_project_slug_language"),
        CheckConstraint("language IN ('es', 'en')", name="ck_project_language"),
        Index("ix_project_tags", "tags", postgresql_using="gin"),
    )

    project_id: Mapped[uuid.UUID] = group_column("project_id")
    group_id = synonym("project_id")

    # language-neutral
    slug: Mapped[str] = mapped_column(String(140), nullable=False)
    repo_url: Mapped[str | None] = mapped_column(String(500))
    live_url: Mapped[str | None] = mapped_column(String(500))
    started_at: Mapped[date | None] = mapped_column(Date)
    finished_at: Mapped[date | None] = mapped_column(Date)
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    cover_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="SET NULL")
    )
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(60)),
        nullable=False,
        default=list,
        server_default=text("'{}'::varchar[]"),
    )

    # translated. Gallery captions are text, so the gallery lives on the row.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    data: Mapped[str | None] = mapped_column(Text)
    images: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    cover: Mapped[MediaAsset | None] = relationship(MediaAsset, lazy="joined")

    NEUTRAL_FIELDS = (
        "slug",
        "repo_url",
        "live_url",
        "started_at",
        "finished_at",
        "is_featured",
        "cover_id",
        "tags",
        "display_order",
        "is_published",
    )
    TEXT_FIELDS = ("title", "data", "images")

    def __repr__(self) -> str:
        return f"<Project {self.slug} [{self.language}]>"
