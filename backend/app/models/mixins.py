import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column

LANGUAGE_LENGTH = 5


@declarative_mixin
class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


@declarative_mixin
class MetadataMixin:
    """Free-form metadata bag present on every content table.

    Named ``meta`` in Python because ``metadata`` is reserved by SQLAlchemy's
    declarative API; the column itself is ``metadata_json``.
    """

    meta: Mapped[dict] = mapped_column(
        "metadata_json",
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
    )


@declarative_mixin
class OrderedMixin:
    display_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0"), index=True
    )


@declarative_mixin
class PublishableMixin:
    is_published: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )


@declarative_mixin
class LanguageRowMixin:
    """Translations live in the same table as the content: one row per language.

    Each row has its own ``id``; the rows describing the same real item share the
    group column (``education_id`` in ``education``, ``project_id`` in
    ``project``...), exposed generically as ``group_id`` so the query helpers do
    not need to know the table.

    Language-neutral values (dates, slug, institution, percentages) are repeated
    on every row of a group. The admin writer always updates all rows of a group
    in one transaction, which is what keeps them from drifting apart.
    """

    language: Mapped[str] = mapped_column(
        String(LANGUAGE_LENGTH), nullable=False, index=True
    )


def group_column(name: str) -> Mapped[uuid.UUID]:
    """The id shared by every language row of the same item.

    No default on purpose: a per-row default would hand each language a
    different id and silently split the item in two.
    """
    return mapped_column(name, UUID(as_uuid=True), nullable=False, index=True)
