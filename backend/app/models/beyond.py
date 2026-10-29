import uuid

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
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

STATUSES = ("reading", "finished", "wishlist", "ongoing", "archived")


class BeyondItem(
    UUIDMixin,
    TimestampMixin,
    MetadataMixin,
    OrderedMixin,
    PublishableMixin,
    LanguageRowMixin,
    db.Model,
):

    __tablename__ = "beyond_item"
    __table_args__ = (
        UniqueConstraint(
            "beyond_item_id", "language", name="uq_beyond_item_group_language"
        ),
        UniqueConstraint("slug", "language", name="uq_beyond_item_slug_language"),
        CheckConstraint("language IN ('es', 'en')", name="ck_beyond_item_language"),
        CheckConstraint(
            "status IS NULL OR status IN "
            "('reading', 'finished', 'wishlist', 'ongoing', 'archived')",
            name="ck_beyond_item_status",
        ),
        Index("ix_beyond_item_tags", "tags", postgresql_using="gin"),
    )

    beyond_item_id: Mapped[uuid.UUID] = group_column("beyond_item_id")
    group_id = synonym("beyond_item_id")

    # language-neutral
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str | None] = mapped_column(String(20))
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(60)),
        nullable=False,
        default=list,
        server_default=text("'{}'::varchar[]"),
    )
    cover_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("media_asset.id", ondelete="SET NULL")
    )

    # translated. Gallery captions are text, so the gallery lives on the row.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    data: Mapped[str | None] = mapped_column(Text)
    images: Mapped[list] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )

    cover: Mapped[MediaAsset | None] = relationship(MediaAsset, lazy="joined")

    NEUTRAL_FIELDS = (
        "slug",
        "status",
        "tags",
        "cover_id",
        "display_order",
        "is_published",
    )
    TEXT_FIELDS = ("title", "data", "images")

    def __repr__(self) -> str:
        return f"<BeyondItem {self.slug} [{self.language}]>"
