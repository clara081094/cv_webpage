"""Shared helpers for the API layer: response envelopes and slug handling."""

import uuid

from app.errors import ApiError, NotFoundError
from app.extensions import db
from app.services.i18n import meta as i18n_meta
from flask import jsonify, request
from slugify import slugify
from sqlalchemy import select


def ok(data, lang: str | None = None, **extra_meta):
    payload = {"data": data}
    if lang is not None:
        payload["meta"] = i18n_meta(lang, **extra_meta)
    elif extra_meta:
        payload["meta"] = extra_meta
    return jsonify(payload)


def created(data, lang: str | None = None):
    return ok(data, lang), 201


def no_content():
    return "", 204


def body() -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiError("A JSON body is required", code="MISSING_BODY")
    if not isinstance(payload, dict):
        raise ApiError("Body must be a JSON object", code="INVALID_BODY")
    return payload


def parse_uuid(value: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise NotFoundError("Invalid identifier") from exc


def get_or_404(model, identifier):
    entity = db.session.get(model, parse_uuid(str(identifier)))
    if entity is None:
        raise NotFoundError(f"{model.__name__} not found")
    return entity


def unique_group_slug(model, candidate: str, *, group_id) -> str:
    """Slugify and de-duplicate, ignoring the rows of this same item.

    The slug repeats across the language rows of one item, so uniqueness is
    checked per group, not per row.
    """
    base = slugify(candidate)[:120] or "item"
    slug = base
    counter = 2
    # no_autoflush: the rows being built have no slug yet, and an autoflush here
    # would hit the NOT NULL constraint we are about to satisfy.
    with db.session.no_autoflush:
        while True:
            stmt = select(model.id).where(
                model.slug == slug, model.group_id != group_id
            )
            if db.session.scalars(stmt).first() is None:
                return slug
            slug = f"{base}-{counter}"
            counter += 1
