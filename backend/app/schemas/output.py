"""Response serializers.

Each content row already belongs to one language, so a serializer just reads its
columns — no translation lookup. ``id`` in the response is the group id (the id
shared by the language rows), which is what the API accepts back on writes;
``row_id`` is the id of the concrete row that was serialized.

Shapes match what the React components already expect, so the frontend can swap
its static dictionaries for fetch calls without renaming props.
"""

from datetime import date

PRESENT_LABEL = {"es": "Presente", "en": "Present"}


def dump_media(media) -> dict | None:
    if media is None:
        return None
    return {
        "id": str(media.id),
        "url": media.url,
        "alt": media.alt_text,
        "width": media.width,
        "height": media.height,
        "mime_type": media.mime_type,
    }


def _identity(row) -> dict:
    return {
        "id": str(row.group_id),
        "row_id": str(row.id),
        "language": row.language,
    }


def format_period(start: date | None, end: date | None, lang: str) -> str | None:
    """Build the "2022 — Presente" label the UI shows, from real dates."""
    if start is None and end is None:
        return None
    start_label = str(start.year) if start else ""
    end_label = str(end.year) if end else PRESENT_LABEL.get(lang, PRESENT_LABEL["en"])
    if start_label and start_label == end_label:
        return start_label
    return f"{start_label} — {end_label}".strip(" —")


def dump_images(images) -> list[dict]:
    """Gallery entries are stored as JSONB: [{media_id, url, caption}]."""
    return list(images or [])


def dump_bio(row, social_links=None) -> dict:
    payload = {
        **_identity(row),
        "full_name": row.full_name,
        "phone": row.phone,
        "email": row.email,
        "location": row.location,
        "resume_url": row.resume_url,
        "photo": dump_media(row.photo),
        "greeting": row.greeting,
        "headline": row.headline,
        "tagline": row.tagline,
        "summary": row.summary,
        "role_label": row.role_label,
        "metadata": row.meta,
    }
    if social_links is not None:
        payload["social_links"] = [dump_social_link(link) for link in social_links]
    return payload


def dump_social_link(link) -> dict:
    return {
        "id": str(link.id),
        "platform": link.platform,
        "url": link.url,
        "label": link.label,
        "icon_name": link.icon_name,
        "display_order": link.display_order,
        "metadata": link.meta,
    }


def dump_education(row) -> dict:
    return {
        **_identity(row),
        "title": row.title,
        "institution": row.institution_label or row.institution,
        "description": row.description,
        "period": format_period(row.start_date, row.end_date, row.language),
        "start_date": row.start_date.isoformat() if row.start_date else None,
        "end_date": row.end_date.isoformat() if row.end_date else None,
        "credential_url": row.credential_url,
        "logo": dump_media(row.logo),
        "display_order": row.display_order,
        "is_published": row.is_published,
        "metadata": row.meta,
    }


def dump_experience(row) -> dict:
    end = None if row.is_current else row.end_date
    return {
        **_identity(row),
        "role": row.role,
        "company": row.company_label or row.company,
        "description": row.description,
        "highlights": row.highlights or [],
        "period": format_period(row.start_date, end, row.language),
        "start_date": row.start_date.isoformat() if row.start_date else None,
        "end_date": row.end_date.isoformat() if row.end_date else None,
        "is_current": row.is_current,
        "location": row.location,
        "employment_type": row.employment_type,
        "company_url": row.company_url,
        "logo": dump_media(row.logo),
        "display_order": row.display_order,
        "is_published": row.is_published,
        "metadata": row.meta,
    }


def dump_language(row) -> dict:
    return {
        **_identity(row),
        "code": row.code,
        "name": row.name,
        "level": row.level_label,
        "percentage": row.percentage,
        "cefr_level": row.cefr_level,
        "display_order": row.display_order,
        "is_published": row.is_published,
        "metadata": row.meta,
    }


def dump_project(row, *, detail: bool = False) -> dict:
    payload = {
        **_identity(row),
        "slug": row.slug,
        "title": row.title,
        "tags": list(row.tags or []),
        "cover": dump_media(row.cover),
        "repo_url": row.repo_url,
        "live_url": row.live_url,
        "is_featured": row.is_featured,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
        "display_order": row.display_order,
        "is_published": row.is_published,
        "metadata": row.meta,
    }
    # `data` is the project body; the gallery is detail-only.
    payload["data"] = row.data
    if detail:
        payload["images"] = dump_images(row.images)
    return payload


def dump_beyond_item(row, *, detail: bool = False) -> dict:
    payload = {
        **_identity(row),
        "slug": row.slug,
        "title": row.title,
        "data": row.data,
        "status": row.status,
        "tags": list(row.tags or []),
        "cover": dump_media(row.cover),
        "display_order": row.display_order,
        "is_published": row.is_published,
        "metadata": row.meta,
    }
    if detail:
        payload["images"] = dump_images(row.images)
    return payload


def dump_group(rows, dumper) -> dict:
    """Admin view of one item: neutral fields once, plus every language row.

    ``rows`` are all the rows sharing a group id.
    """
    ordered = sorted(rows, key=lambda row: row.language)
    first = ordered[0]
    base = dumper(first)
    base.pop("row_id", None)
    base.pop("language", None)

    # Public serializers blend a translated label into a neutral key (education's
    # `institution` shows `institution_label`). The editor needs the raw neutral
    # value, so put it back.
    for name in first.NEUTRAL_FIELDS:
        if name in base:
            value = getattr(first, name)
            if isinstance(value, str | int | bool | list) or value is None:
                base[name] = value

    base["translations"] = {
        row.language: {name: getattr(row, name) for name in row.TEXT_FIELDS}
        for row in ordered
    }
    return base


def dump_user(user) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }
