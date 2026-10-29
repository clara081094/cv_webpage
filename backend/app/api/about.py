"""Public endpoints for the "Sobre mí" section.

Feeds the Home hero, the Footer and the About page: contact card, social links,
work experience, education and languages.
"""

from app.api.helpers import ok
from app.errors import NotFoundError
from app.extensions import db
from app.models import Bio, Education, Experience, LanguageSkill, SocialLink
from app.schemas.output import (
    dump_bio,
    dump_education,
    dump_experience,
    dump_language,
    dump_social_link,
)
from app.services.i18n import localized, note_fallbacks, resolve_language
from app.services.query import localized_rows
from flask import Blueprint
from sqlalchemy import select

bp = Blueprint("about", __name__)


def _bio_or_404(lang) -> Bio:
    stmt, _row = localized(Bio, lang, published_only=False)
    bio = db.session.scalars(stmt).first()
    if bio is None:
        raise NotFoundError(
            "Bio has not been created yet. Create it with PUT /admin/bio."
        )
    note_fallbacks([bio])
    return bio


def _social_links() -> list[SocialLink]:
    stmt = (
        select(SocialLink)
        .where(SocialLink.is_published.is_(True))
        .order_by(SocialLink.display_order)
    )
    return list(db.session.scalars(stmt).all())


def _education_rows(lang):
    return localized_rows(
        Education,
        lang,
        lambda row: row.display_order,
        lambda row: row.end_date.desc().nullsfirst(),
    )


def _experience_rows(lang):
    return localized_rows(
        Experience,
        lang,
        lambda row: row.display_order,
        lambda row: row.start_date.desc(),
    )


def _language_rows(lang):
    return localized_rows(
        LanguageSkill,
        lang,
        lambda row: row.display_order,
        lambda row: row.percentage.desc(),
    )


@bp.get("/bio")
def get_bio():
    lang = resolve_language()
    bio = _bio_or_404(lang)
    return ok(dump_bio(bio, social_links=_social_links()), lang)


@bp.get("/social-links")
def list_social_links():
    lang = resolve_language()
    return ok([dump_social_link(link) for link in _social_links()], lang)


@bp.get("/about")
def get_about():
    """Aggregated payload for the About page: one request instead of four."""
    lang = resolve_language()
    bio = _bio_or_404(lang)
    return ok(
        {
            "bio": dump_bio(bio, social_links=_social_links()),
            "experience": [dump_experience(row) for row in _experience_rows(lang)],
            "education": [dump_education(row) for row in _education_rows(lang)],
            "languages": [dump_language(row) for row in _language_rows(lang)],
        },
        lang,
    )


@bp.get("/education")
def list_education():
    lang = resolve_language()
    return ok([dump_education(row) for row in _education_rows(lang)], lang)


@bp.get("/experience")
def list_experience():
    lang = resolve_language()
    return ok([dump_experience(row) for row in _experience_rows(lang)], lang)


@bp.get("/languages")
def list_languages():
    lang = resolve_language()
    return ok([dump_language(row) for row in _language_rows(lang)], lang)
