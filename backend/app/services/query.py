"""Query helpers shared by the public endpoints: pagination, args, tag counts."""

from app.errors import ApiError
from app.extensions import db
from app.services.i18n import localized, note_fallbacks
from flask import request
from sqlalchemy import func, select

MAX_PER_PAGE = 100


def pagination_args(default_per_page: int = 12) -> tuple[int, int]:
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", default_per_page))
    except ValueError as exc:
        raise ApiError(
            "page and per_page must be integers", code="BAD_PAGINATION"
        ) from exc
    if page < 1 or per_page < 1:
        raise ApiError("page and per_page must be positive", code="BAD_PAGINATION")
    return page, min(per_page, MAX_PER_PAGE)


def paginate(stmt, page: int, per_page: int) -> tuple[list, int]:
    total = db.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.session.scalars(stmt.limit(per_page).offset((page - 1) * per_page)).all()
    return list(rows), total


def bool_arg(name: str) -> bool | None:
    raw = request.args.get(name)
    if raw is None:
        return None
    return raw.lower() in {"1", "true", "yes"}


def request_tag() -> str | None:
    tag = request.args.get("tag")
    return tag.strip().lower() if tag else None


def localized_rows(model, lang: str, *order_by):
    """Every item of ``model`` in ``lang``, ordered.

    ``order_by`` takes callables so the caller can order by columns of the
    aliased row that ``localized()`` builds: ``lambda row: row.display_order``.
    """
    stmt, row = localized(model, lang)
    stmt = stmt.order_by(*[column(row) for column in order_by])
    rows = list(db.session.scalars(stmt).all())
    note_fallbacks(rows)
    return rows


def tag_counts(model, lang: str) -> list[dict]:
    """Tags in use on published items, with how many items carry each one."""
    stmt, _row = localized(model, lang)
    sub = stmt.subquery()
    tag = func.unnest(sub.c.tags).label("tag")
    counted = (
        select(tag, func.count().label("count"))
        .group_by(tag)
        .order_by(func.count().desc(), tag)
    )
    return [
        {"tag": item.tag, "count": item.count}
        for item in db.session.execute(counted).all()
    ]
