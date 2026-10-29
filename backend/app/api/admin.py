"""Admin CRUD.

Every content resource follows the same shape, so the routes are generated from
a declarative spec instead of eight near-identical blueprints:

    GET    /admin/<resource>            all groups, unpublished included
    POST   /admin/<resource>
    GET    /admin/<resource>/<group_id>
    PUT    /admin/<resource>/<group_id>
    DELETE /admin/<resource>/<group_id>
    PATCH  /admin/<resource>/reorder

Because translations live in the same table, one item is a *group* of rows that
share a group id. The writer keeps a group consistent: neutral fields are copied
to every row, text fields are written per language, and a delete removes the
whole group.
"""

import uuid
from dataclasses import dataclass
from typing import Any

from app.api.helpers import body, created, no_content, ok, unique_group_slug
from app.errors import ApiError, NotFoundError
from app.extensions import db
from app.models import (
    BeyondItem,
    Bio,
    Education,
    Experience,
    LanguageSkill,
    MediaAsset,
    Project,
    SocialLink,
)
from app.schemas.output import (
    dump_beyond_item,
    dump_bio,
    dump_education,
    dump_experience,
    dump_group,
    dump_language,
    dump_project,
    dump_social_link,
)
from app.schemas.payloads import (
    BeyondItemIn,
    BioIn,
    EducationIn,
    ExperienceIn,
    LanguageIn,
    ProjectIn,
    ReorderIn,
    SocialLinkIn,
)
from app.services.i18n import default_language
from flask import Blueprint
from flask_jwt_extended import jwt_required
from slugify import slugify
from sqlalchemy import select

# The /admin prefix is applied at registration time (app/api/__init__.py);
# setting it here too would be silently overridden.
bp = Blueprint("admin", __name__)


@dataclass(frozen=True)
class Resource:
    path: str
    model: Any
    payload: Any
    dumper: Any
    slug_from: str | None = None
    normalize: Any = None


def _group_rows(model, group_id) -> list:
    rows = list(
        db.session.scalars(select(model).where(model.group_id == group_id)).all()
    )
    if not rows:
        raise NotFoundError(f"{model.__name__} not found")
    return rows


def _all_groups(model) -> list[list]:
    stmt = select(model).order_by(model.display_order, model.group_id, model.language)
    groups: dict[uuid.UUID, list] = {}
    for row in db.session.scalars(stmt).all():
        groups.setdefault(row.group_id, []).append(row)
    return list(groups.values())


def _write_group(resource: Resource, payload, group_id: uuid.UUID | None):
    """Create or update every language row of one item."""
    model = resource.model
    data = payload.model_dump(exclude_unset=True)
    translations = data.pop("translations", None) or {}
    metadata = data.pop("metadata", None)

    existing = {}
    if group_id is not None:
        existing = {row.language: row for row in _group_rows(model, group_id)}
    else:
        group_id = uuid.uuid4()

    if not existing and not translations:
        raise ApiError(
            "At least one language is required in 'translations'",
            code="MISSING_TRANSLATIONS",
        )

    neutral = {name: data[name] for name in model.NEUTRAL_FIELDS if name in data}
    if resource.normalize is not None:
        resource.normalize(neutral)

    # Galleries reference media rows, so resolve them before anything is staged:
    # a query with half-built rows in the session would autoflush them.
    for values in translations.values():
        if "images" in values:
            values["images"] = _resolve_gallery(values["images"])

    rows = []
    new_rows = []
    for language in sorted(set(existing) | set(translations)):
        row = existing.get(language)
        if row is None:
            # A new language reuses the neutral values already stored for the item.
            template = next(iter(existing.values()), None)
            row = model(group_id=group_id, language=language)
            if template is not None:
                for name in model.NEUTRAL_FIELDS:
                    setattr(row, name, getattr(template, name))
                row.meta = template.meta
            new_rows.append(row)

        # Neutral values are written to every row: that is what keeps the
        # duplicated columns from drifting between languages.
        for name, value in neutral.items():
            setattr(row, name, value)
        if metadata is not None:
            row.meta = metadata
        for name, value in (translations.get(language) or {}).items():
            setattr(row, name, value)
        rows.append(row)

    _assign_slug(resource, rows, group_id, data.get("slug"))

    # Staged only once the whole group is valid, so a rejected request leaves
    # nothing half-written in the session.
    db.session.add_all(new_rows)
    return group_id, rows


def _assign_slug(resource: Resource, rows, group_id, explicit) -> None:
    """One slug per item, copied to every language row."""
    if resource.slug_from is None:
        return
    current = next((row.slug for row in rows if getattr(row, "slug", None)), None)
    if explicit:
        slug = unique_group_slug(resource.model, explicit, group_id=group_id)
    elif current:
        slug = current
    else:
        default = next(
            (row for row in rows if row.language == default_language()), rows[0]
        )
        slug = unique_group_slug(
            resource.model,
            getattr(default, resource.slug_from) or "item",
            group_id=group_id,
        )
    for row in rows:
        row.slug = slug


def _register(resource: Resource) -> None:
    name = resource.path.replace("/", "_")

    @bp.get(f"/{resource.path}", endpoint=f"list_{name}")
    @jwt_required()
    def list_items(resource=resource):
        return ok(
            [dump_group(rows, resource.dumper) for rows in _all_groups(resource.model)]
        )

    @bp.post(f"/{resource.path}", endpoint=f"create_{name}")
    @jwt_required()
    def create_item(resource=resource):
        payload = resource.payload.model_validate(body())
        group_id, _rows = _write_group(resource, payload, None)
        db.session.commit()
        return created(
            dump_group(_group_rows(resource.model, group_id), resource.dumper)
        )

    @bp.get(f"/{resource.path}/<uuid:group_id>", endpoint=f"get_{name}")
    @jwt_required()
    def get_item(group_id, resource=resource):
        return ok(dump_group(_group_rows(resource.model, group_id), resource.dumper))

    @bp.put(f"/{resource.path}/<uuid:group_id>", endpoint=f"update_{name}")
    @jwt_required()
    def update_item(group_id, resource=resource):
        payload = resource.payload.model_validate(body())
        _write_group(resource, payload, group_id)
        db.session.commit()
        return ok(dump_group(_group_rows(resource.model, group_id), resource.dumper))

    @bp.delete(f"/{resource.path}/<uuid:group_id>", endpoint=f"delete_{name}")
    @jwt_required()
    def delete_item(group_id, resource=resource):
        for row in _group_rows(resource.model, group_id):
            db.session.delete(row)
        db.session.commit()
        return no_content()

    @bp.patch(f"/{resource.path}/reorder", endpoint=f"reorder_{name}")
    @jwt_required()
    def reorder_items(resource=resource):
        payload = ReorderIn.model_validate(body())
        for entry in payload.items:
            for row in _group_rows(resource.model, entry.id):
                row.display_order = entry.display_order
        db.session.commit()
        return ok({"updated": len(payload.items)})


# --- resource-specific normalization ------------------------------------


def _resolve_gallery(images: list[dict]) -> list[dict]:
    """Store the media url next to the id: filenames are immutable, so reads need
    no extra query and a deleted asset is caught by the media delete check."""
    resolved = []
    for entry in images or []:
        asset = db.session.get(MediaAsset, uuid.UUID(entry["media_id"]))
        if asset is None:
            raise NotFoundError(f"Media {entry['media_id']} not found")
        resolved.append(
            {
                "media_id": str(asset.id),
                "url": asset.url,
                "caption": entry.get("caption"),
                "alt": asset.alt_text,
            }
        )
    return resolved


def _normalize_tags(neutral: dict) -> None:
    if "tags" in neutral:
        neutral["tags"] = list(
            dict.fromkeys(slugify(tag) for tag in neutral["tags"] if tag.strip())
        )


# --- resource table ----------------------------------------------------

RESOURCES = (
    Resource(
        path="education", model=Education, payload=EducationIn, dumper=dump_education
    ),
    Resource(
        path="experience",
        model=Experience,
        payload=ExperienceIn,
        dumper=dump_experience,
    ),
    Resource(
        path="languages", model=LanguageSkill, payload=LanguageIn, dumper=dump_language
    ),
    Resource(
        path="projects",
        model=Project,
        payload=ProjectIn,
        dumper=lambda row: dump_project(row, detail=True),
        slug_from="title",
        normalize=_normalize_tags,
    ),
    Resource(
        path="beyond",
        model=BeyondItem,
        payload=BeyondItemIn,
        dumper=lambda row: dump_beyond_item(row, detail=True),
        slug_from="title",
        normalize=_normalize_tags,
    ),
)

for _resource in RESOURCES:
    _register(_resource)


# --- social links (no language rows) -----------------------------------


@bp.get("/social-links")
@jwt_required()
def list_social_links():
    stmt = select(SocialLink).order_by(SocialLink.display_order)
    return ok([dump_social_link(link) for link in db.session.scalars(stmt).all()])


@bp.post("/social-links")
@jwt_required()
def create_social_link():
    payload = SocialLinkIn.model_validate(body())
    link = SocialLink(**payload.model_dump(exclude={"metadata"}))
    link.meta = payload.metadata
    db.session.add(link)
    db.session.commit()
    return created(dump_social_link(link))


@bp.put("/social-links/<uuid:link_id>")
@jwt_required()
def update_social_link(link_id):
    link = db.session.get(SocialLink, link_id)
    if link is None:
        raise NotFoundError("SocialLink not found")
    payload = SocialLinkIn.model_validate(body())
    for name, value in payload.model_dump(
        exclude_unset=True, exclude={"metadata"}
    ).items():
        setattr(link, name, value)
    if payload.metadata:
        link.meta = payload.metadata
    db.session.commit()
    return ok(dump_social_link(link))


@bp.delete("/social-links/<uuid:link_id>")
@jwt_required()
def delete_social_link(link_id):
    link = db.session.get(SocialLink, link_id)
    if link is None:
        raise NotFoundError("SocialLink not found")
    db.session.delete(link)
    db.session.commit()
    return no_content()


# --- bio (singleton) ---------------------------------------------------


@bp.get("/bio")
@jwt_required()
def get_bio_admin():
    rows = list(db.session.scalars(select(Bio)).all())
    if not rows:
        return ok(None)
    return ok(dump_group(rows, dump_bio))


@bp.put("/bio")
@jwt_required()
def upsert_bio():
    """Bio is a singleton: PUT creates its language rows the first time."""
    payload = BioIn.model_validate(body())
    existing = list(db.session.scalars(select(Bio)).all())
    resource = Resource(path="bio", model=Bio, payload=BioIn, dumper=dump_bio)
    group_id, _rows = _write_group(
        resource, payload, existing[0].group_id if existing else None
    )
    db.session.commit()
    return ok(dump_group(_group_rows(Bio, group_id), dump_bio))
