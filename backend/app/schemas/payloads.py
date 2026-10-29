"""Pydantic input models for the admin API.

Convention: language-neutral values sit at the top level and translated text goes
under ``translations``, keyed by language:

    {"institution": "U. Nacional",
     "translations": {"es": {"title": "Maestría"}, "en": {"title": "Master"}}}

Each key of ``translations`` becomes one row in the entity's own table, all rows
sharing the same group id.
"""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    TypeAdapter,
    field_validator,
)

Language = Literal["es", "en"]
Order = Annotated[int, Field(ge=0)]


class Payload(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContentPayload(Payload):
    display_order: Order = 0
    is_published: bool = True
    metadata: dict = Field(default_factory=dict)


class GalleryImage(Payload):
    """Gallery entry stored inside a JSONB column, so ids travel as strings."""

    media_id: str
    caption: str | None = Field(default=None, max_length=255)

    @field_validator("media_id")
    @classmethod
    def must_be_uuid(cls, value: str) -> str:
        return str(UUID(value))


# --- auth ---------------------------------------------------------------


class LoginIn(Payload):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)


# --- bio ----------------------------------------------------------------


class BioTextIn(Payload):
    greeting: str | None = Field(default=None, max_length=80)
    headline: str | None = Field(default=None, max_length=255)
    tagline: str | None = Field(default=None, max_length=255)
    summary: str | None = None
    role_label: str | None = Field(default=None, max_length=160)


class BioIn(Payload):
    full_name: str = Field(min_length=1, max_length=160)
    phone: str | None = Field(default=None, max_length=40)
    email: EmailStr | None = None
    location: str | None = Field(default=None, max_length=160)
    resume_url: str | None = Field(default=None, max_length=500)
    birth_date: date | None = None
    photo_id: UUID | None = None
    metadata: dict = Field(default_factory=dict)
    translations: dict[Language, BioTextIn] = Field(default_factory=dict)


class SocialLinkIn(ContentPayload):
    platform: str = Field(min_length=1, max_length=40)
    url: str = Field(min_length=1, max_length=500)
    label: str = Field(min_length=1, max_length=80)
    icon_name: str = Field(min_length=1, max_length=40)

    @field_validator("url")
    @classmethod
    def must_be_http_url(cls, value: str) -> str:
        """Validated as a URL but kept as str: the column stores text."""
        TypeAdapter(HttpUrl).validate_python(value)
        return value


# --- about --------------------------------------------------------------


class EducationTextIn(Payload):
    title: str = Field(min_length=1, max_length=255)
    institution_label: str | None = Field(default=None, max_length=200)
    description: str | None = None


class EducationIn(ContentPayload):
    institution: str = Field(min_length=1, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    credential_url: str | None = Field(default=None, max_length=500)
    logo_id: UUID | None = None
    translations: dict[Language, EducationTextIn] = Field(default_factory=dict)


class ExperienceTextIn(Payload):
    role: str = Field(min_length=1, max_length=200)
    company_label: str | None = Field(default=None, max_length=200)
    description: str | None = None
    highlights: list[str] = Field(default_factory=list)


class ExperienceIn(ContentPayload):
    company: str = Field(min_length=1, max_length=200)
    company_url: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=160)
    employment_type: str | None = Field(default=None, max_length=40)
    start_date: date
    end_date: date | None = None
    is_current: bool = False
    logo_id: UUID | None = None
    translations: dict[Language, ExperienceTextIn] = Field(default_factory=dict)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, value, info):
        start = info.data.get("start_date")
        if value and start and value < start:
            raise ValueError("end_date must not precede start_date")
        return value


class LanguageTextIn(Payload):
    name: str = Field(min_length=1, max_length=80)
    level_label: str | None = Field(default=None, max_length=80)


class LanguageIn(ContentPayload):
    code: str = Field(min_length=2, max_length=5)
    percentage: int = Field(ge=0, le=100)
    cefr_level: str | None = Field(default=None, max_length=10)
    translations: dict[Language, LanguageTextIn] = Field(default_factory=dict)


# --- projects -----------------------------------------------------------


class ProjectTextIn(Payload):
    title: str = Field(min_length=1, max_length=200)
    data: str | None = None
    images: list[GalleryImage] = Field(default_factory=list)


class ProjectIn(ContentPayload):
    slug: str | None = Field(default=None, max_length=140)
    repo_url: str | None = Field(default=None, max_length=500)
    live_url: str | None = Field(default=None, max_length=500)
    started_at: date | None = None
    finished_at: date | None = None
    is_featured: bool = False
    cover_id: UUID | None = None
    tags: list[str] = Field(default_factory=list)
    translations: dict[Language, ProjectTextIn] = Field(default_factory=dict)


# --- beyond -------------------------------------------------------------


class BeyondItemTextIn(Payload):
    title: str = Field(min_length=1, max_length=255)
    data: str | None = None
    images: list[GalleryImage] = Field(default_factory=list)


class BeyondItemIn(ContentPayload):
    slug: str | None = Field(default=None, max_length=160)
    status: Literal["reading", "finished", "wishlist", "ongoing", "archived"] | None = (
        None
    )
    tags: list[str] = Field(default_factory=list)
    cover_id: UUID | None = None
    translations: dict[Language, BeyondItemTextIn] = Field(default_factory=dict)


# --- shared -------------------------------------------------------------


class ReorderEntry(Payload):
    id: UUID
    display_order: Order


class ReorderIn(Payload):
    items: list[ReorderEntry] = Field(min_length=1)


class MediaMetaIn(Payload):
    alt_text: str | None = Field(default=None, max_length=255)
