"""Public endpoints for the "Proyectos" section."""

from app.api.helpers import ok
from app.errors import NotFoundError
from app.extensions import db
from app.models import Project
from app.schemas.output import dump_project
from app.services.i18n import localized, note_fallbacks, resolve_language
from app.services.query import (
    bool_arg,
    paginate,
    pagination_args,
    request_tag,
    tag_counts,
)
from flask import Blueprint

bp = Blueprint("projects", __name__)


@bp.get("/projects")
def list_projects():
    lang = resolve_language()
    page, per_page = pagination_args()

    stmt, row = localized(Project, lang)

    tag = request_tag()
    if tag:
        # varchar[] containment, served by the GIN index on project.tags.
        stmt = stmt.where(row.tags.contains([tag]))

    featured = bool_arg("featured")
    if featured is not None:
        stmt = stmt.where(row.is_featured.is_(featured))

    stmt = stmt.order_by(row.display_order, row.started_at.desc().nullslast())
    rows, total = paginate(stmt, page, per_page)
    note_fallbacks(rows)
    return ok(
        [dump_project(item) for item in rows],
        lang,
        page=page,
        per_page=per_page,
        total=total,
    )


@bp.get("/projects/<slug>")
def get_project(slug):
    lang = resolve_language()
    stmt, row = localized(Project, lang)
    project = db.session.scalars(stmt.where(row.slug == slug)).first()
    if project is None:
        raise NotFoundError(f"Project '{slug}' not found")
    note_fallbacks([project])
    return ok(dump_project(project, detail=True), lang)


@bp.get("/tags")
def list_tags():
    """Project tags in use, with how many projects carry each one."""
    lang = resolve_language()
    return ok(tag_counts(Project, lang), lang)
