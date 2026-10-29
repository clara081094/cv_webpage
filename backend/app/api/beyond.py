"""Public endpoints for the "Más allá del código" section.

Flat list of entries catalogued by their ``tags`` column — no categories.
"""

from app.api.helpers import ok
from app.errors import NotFoundError
from app.extensions import db
from app.models import BeyondItem
from app.schemas.output import dump_beyond_item
from app.services.i18n import localized, note_fallbacks, resolve_language
from app.services.query import paginate, pagination_args, request_tag, tag_counts
from flask import Blueprint, request

bp = Blueprint("beyond", __name__)


@bp.get("/beyond")
def list_beyond():
    lang = resolve_language()
    page, per_page = pagination_args(default_per_page=24)

    stmt, row = localized(BeyondItem, lang)

    tag = request_tag()
    if tag:
        # varchar[] containment, served by the GIN index on beyond_item.tags.
        stmt = stmt.where(row.tags.contains([tag]))

    status = request.args.get("status")
    if status:
        stmt = stmt.where(row.status == status)

    stmt = stmt.order_by(row.display_order, row.created_at.desc())
    rows, total = paginate(stmt, page, per_page)
    note_fallbacks(rows)
    return ok(
        [dump_beyond_item(item) for item in rows],
        lang,
        page=page,
        per_page=per_page,
        total=total,
    )


@bp.get("/beyond/tags")
def list_beyond_tags():
    """Tags in use with their counts. Reserves the slug "tags": an entry named
    that would be unreachable at /beyond/tags."""
    lang = resolve_language()
    return ok(tag_counts(BeyondItem, lang), lang)


@bp.get("/beyond/<slug>")
def get_beyond_item(slug):
    lang = resolve_language()
    stmt, row = localized(BeyondItem, lang)
    item = db.session.scalars(stmt.where(row.slug == slug)).first()
    if item is None:
        raise NotFoundError(f"Beyond entry '{slug}' not found")
    note_fallbacks([item])
    return ok(dump_beyond_item(item, detail=True), lang)
