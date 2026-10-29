"""Language resolution for single-table translations.

Content tables hold one row per language, so reading is a filter, not a join:

    SELECT * FROM education WHERE language = 'es'

``localized()`` builds that filter and adds the fallback: if a group has no row
in the requested language, the row in the default language is used instead and
``meta.lang_fallback`` is set so the frontend knows.
"""

from app.errors import ApiError
from flask import current_app, g, request
from sqlalchemy import select
from sqlalchemy.orm import aliased


def supported_languages() -> list[str]:
    return current_app.config["SUPPORTED_LOCALES"]


def default_language() -> str:
    return current_app.config["DEFAULT_LOCALE"]


def resolve_language() -> str:
    """Read and validate ``?lang``; unknown values are a client error, not silent."""
    requested = request.args.get("lang")
    if not requested:
        return default_language()
    requested = requested.lower()
    if requested not in supported_languages():
        raise ApiError(
            f"Unsupported language '{requested}'",
            code="UNSUPPORTED_LANGUAGE",
            status_code=400,
            details={"supported": supported_languages()},
        )
    return requested


def mark_fallback() -> None:
    g.lang_fallback = True


def used_fallback() -> bool:
    return bool(getattr(g, "lang_fallback", False))


def note_fallbacks(rows) -> None:
    """Flag the response if any returned row is not in the requested language."""
    lang = getattr(g, "requested_language", None)
    if lang and any(row.language != lang for row in rows):
        mark_fallback()


def localized(model, language: str, *, published_only: bool = True):
    """One row per group: the requested language, or the default as fallback.

    DISTINCT ON collapses each group to a single row, preferring the requested
    language. Wrapping it in a subquery lets callers keep filtering and ordering
    by any column, including display_order.
    """
    g.requested_language = language
    fallback = default_language()

    inner = select(model).where(model.language.in_({language, fallback}))
    if published_only and hasattr(model, "is_published"):
        inner = inner.where(model.is_published.is_(True))
    inner = inner.distinct(model.group_id).order_by(
        model.group_id, (model.language == language).desc()
    )

    row = aliased(model, inner.subquery())
    return select(row), row


def meta(language: str, **extra) -> dict:
    payload = {"lang": language}
    if used_fallback():
        payload["lang_fallback"] = True
    payload.update(extra)
    return payload
