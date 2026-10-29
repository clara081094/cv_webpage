"""Seed the database with the content currently hardcoded in the frontend.

Source of truth for these values: frontend/src/data/profile.js and
frontend/src/i18n/{es,en}.js.

The shape below mirrors the schema: ``neutral`` holds the values that do not
depend on the language and get copied to every row, ``text`` holds one entry per
language. Idempotent: every seeded item carries a stable ``seed_key`` in its
metadata, so re-running matches the same group even after its content was edited
through the API.
"""

import uuid
from datetime import date

from app.extensions import db
from app.models import (
    BeyondItem,
    Bio,
    Education,
    Experience,
    LanguageSkill,
    Project,
    SocialLink,
)
from sqlalchemy import select

BIO = {
    "key": "bio",
    "neutral": {
        "full_name": "Clara Justino Limaco",
        "phone": "+34 664423852",
        "email": "clara.081094@gmail.com",
    },
    "text": {
        "es": {
            "greeting": "Hola",
            "tagline": "Un poco de mí",
            "role_label": "Ingeniera de Software",
            "headline": "Construyendo software con propósito",
            "summary": (
                "Ingeniera de software especializada en construir productos digitales "
                "robustos, desde el backend hasta la experiencia de usuario."
            ),
        },
        "en": {
            "greeting": "Hi",
            "tagline": "A bit about me",
            "role_label": "Software Engineer",
            "headline": "Building software with purpose",
            "summary": (
                "Software engineer specialized in building robust digital products, "
                "from the backend to the user experience."
            ),
        },
    },
}

SOCIAL_LINKS = [
    {
        "platform": "linkedin",
        "label": "LinkedIn",
        "icon_name": "linkedin",
        "url": "https://www.linkedin.com/",
    },
    {
        "platform": "instagram",
        "label": "Instagram",
        "icon_name": "instagram",
        "url": "https://www.instagram.com/",
    },
    {
        "platform": "github",
        "label": "GitHub",
        "icon_name": "github",
        "url": "https://github.com/",
    },
]

EXPERIENCE = [
    {
        "key": "experience-tech-company",
        "neutral": {
            "company": "Empresa Tecnológica",
            "start_date": date(2022, 1, 1),
            "end_date": None,
            "is_current": True,
        },
        "text": {
            "es": {
                "role": "Ingeniera de Software Senior",
                "company_label": "Empresa Tecnológica",
                "description": (
                    "Desarrollo de APIs y arquitectura de microservicios para una "
                    "plataforma con miles de usuarios activos."
                ),
            },
            "en": {
                "role": "Senior Software Engineer",
                "company_label": "Tech Company",
                "description": (
                    "Building APIs and microservice architecture for a platform with "
                    "thousands of active users."
                ),
            },
        },
    },
    {
        "key": "experience-startup",
        "neutral": {
            "company": "Startup de Software",
            "start_date": date(2020, 1, 1),
            "end_date": date(2022, 1, 1),
            "is_current": False,
        },
        "text": {
            "es": {
                "role": "Ingeniera de Software",
                "company_label": "Startup de Software",
                "description": (
                    "Construcción de features full-stack y colaboración directa con "
                    "diseño y producto."
                ),
            },
            "en": {
                "role": "Software Engineer",
                "company_label": "Software Startup",
                "description": (
                    "Built full-stack features in close collaboration "
                    "with design and product."
                ),
            },
        },
    },
    {
        "key": "experience-consultancy",
        "neutral": {
            "company": "Consultora de TI",
            "start_date": date(2018, 1, 1),
            "end_date": date(2020, 1, 1),
            "is_current": False,
        },
        "text": {
            "es": {
                "role": "Desarrolladora Junior",
                "company_label": "Consultora de TI",
                "description": (
                    "Soporte y desarrollo de aplicaciones web para clientes "
                    "del sector financiero."
                ),
            },
            "en": {
                "role": "Junior Developer",
                "company_label": "IT Consultancy",
                "description": (
                    "Supported and developed web applications for "
                    "financial-sector clients."
                ),
            },
        },
    },
]

EDUCATION = [
    {
        "key": "education-national-university",
        "neutral": {
            "institution": "Universidad Nacional",
            "start_date": date(2014, 1, 1),
            "end_date": date(2018, 1, 1),
        },
        "text": {
            "es": {
                "title": "Ingeniería en Sistemas Computacionales",
                "institution_label": "Universidad Nacional",
            },
            "en": {
                "title": "B.Eng. in Computer Systems Engineering",
                "institution_label": "National University",
            },
        },
    },
    {
        "key": "education-cloud-cert",
        "neutral": {
            "institution": "Plataforma de Certificación",
            "start_date": date(2019, 1, 1),
            "end_date": date(2019, 1, 1),
        },
        "text": {
            "es": {
                "title": "Certificación en Arquitectura Cloud",
                "institution_label": "Plataforma de Certificación",
            },
            "en": {
                "title": "Cloud Architecture Certification",
                "institution_label": "Certification Platform",
            },
        },
    },
]

LANGUAGES = [
    {
        "key": "language-es",
        "neutral": {"code": "es", "percentage": 100, "cefr_level": "C2"},
        "text": {
            "es": {"name": "Español", "level_label": "Nativo"},
            "en": {"name": "Spanish", "level_label": "Native"},
        },
    },
    {
        "key": "language-en",
        "neutral": {"code": "en", "percentage": 85, "cefr_level": "C1"},
        "text": {
            "es": {"name": "Inglés", "level_label": "Avanzado"},
            "en": {"name": "English", "level_label": "Advanced"},
        },
    },
]

PROJECTS = [
    {
        "key": "project-school",
        "neutral": {
            "slug": "school-management-platform",
            "is_featured": True,
            "tags": ["react", "python", "postgresql"],
        },
        "text": {
            "es": {
                "title": "Plataforma de gestión escolar",
                "data": "Sistema web para administrar calificaciones y asistencia.",
            },
            "en": {
                "title": "School management platform",
                "data": "Web system for managing grades and attendance.",
            },
        },
    },
    {
        "key": "project-finance",
        "neutral": {
            "slug": "personal-finance-app",
            "is_featured": False,
            "tags": ["react-native", "nodejs"],
        },
        "text": {
            "es": {
                "title": "App de finanzas personales",
                "data": "Aplicación móvil para el control de gastos e ingresos.",
            },
            "en": {
                "title": "Personal finance app",
                "data": "Mobile app for tracking expenses and income.",
            },
        },
    },
    {
        "key": "project-recommendations",
        "neutral": {
            "slug": "recommendations-api",
            "is_featured": False,
            "tags": ["flask", "postgresql", "machine-learning"],
        },
        "text": {
            "es": {
                "title": "API de recomendaciones",
                "data": "Servicio backend de recomendaciones basado en datos de uso.",
            },
            "en": {
                "title": "Recommendations API",
                "data": "Backend recommendation service based on usage data.",
            },
        },
    },
]


BEYOND_ITEMS = [
    {
        "key": "beyond-current-read",
        "neutral": {
            "slug": "libro-actual",
            "status": "reading",
            "tags": ["books", "reading"],
            "metadata": {"author": "", "year": None},
        },
        "text": {
            "es": {"title": "Libro actual", "data": "Autor pendiente."},
            "en": {"title": "Current read", "data": "Author pending."},
        },
    },
    {
        "key": "beyond-flex-routine",
        "neutral": {
            "slug": "rutina-de-flexibilidad",
            "status": "ongoing",
            "tags": ["flex", "training"],
            "metadata": {"discipline": "", "frequency": ""},
        },
        "text": {
            "es": {"title": "Rutina de flexibilidad", "data": "En progreso."},
            "en": {"title": "Flexibility routine", "data": "In progress."},
        },
    },
    {
        "key": "beyond-first-series",
        "neutral": {
            "slug": "primera-serie",
            "status": None,
            "tags": ["photography"],
            "metadata": {"camera": "", "lens": "", "location": ""},
        },
        "text": {
            "es": {"title": "Primera serie", "data": "Pendiente de subir fotos."},
            "en": {"title": "First series", "data": "Photos pending upload."},
        },
    },
]


def _upsert_group(model, entry: dict, order: int) -> None:
    """Write one row per language, all sharing the same group id.

    Matching is done on ``metadata_json->>'seed_key'`` rather than on a content
    column: institution, slug or title can be edited through the admin API, and
    matching on them would create a second copy of the item.
    """
    neutral = dict(entry["neutral"])
    metadata = {**(neutral.pop("metadata", None) or {}), "seed_key": entry["key"]}

    anchor = db.session.scalars(
        select(model).where(model.meta["seed_key"].as_string() == entry["key"])
    ).first()
    if anchor is None:
        group_id = uuid.uuid4()
        existing = {}
    else:
        group_id = anchor.group_id
        # Load the whole group, not just the matched row: otherwise a second row
        # for an already existing language would be inserted.
        existing = {
            row.language: row
            for row in db.session.scalars(
                select(model).where(model.group_id == group_id)
            ).all()
        }

    for language, values in entry["text"].items():
        row = existing.get(language)
        if row is None:
            row = model(group_id=group_id, language=language)
            db.session.add(row)
        for name, value in neutral.items():
            setattr(row, name, value)
        row.meta = metadata
        for name, value in values.items():
            setattr(row, name, value)
        row.display_order = order


def seed_bio() -> None:
    _upsert_group(Bio, BIO, 0)


def seed_social_links() -> None:
    for order, data in enumerate(SOCIAL_LINKS):
        link = db.session.scalars(
            select(SocialLink).where(SocialLink.platform == data["platform"])
        ).first()
        if link is None:
            link = SocialLink(platform=data["platform"])
            db.session.add(link)
        link.label = data["label"]
        link.icon_name = data["icon_name"]
        link.url = data["url"]
        link.display_order = order


def seed_experience() -> None:
    for order, entry in enumerate(EXPERIENCE):
        _upsert_group(Experience, entry, order)


def seed_education() -> None:
    for order, entry in enumerate(EDUCATION):
        _upsert_group(Education, entry, order)


def seed_languages() -> None:
    for order, entry in enumerate(LANGUAGES):
        _upsert_group(LanguageSkill, entry, order)


def seed_projects() -> None:
    for order, entry in enumerate(PROJECTS):
        _upsert_group(Project, entry, order)


def seed_beyond() -> None:
    """Beyond entries are generic: no categories, catalogued by tags."""
    for order, entry in enumerate(BEYOND_ITEMS):
        _upsert_group(BeyondItem, entry, order)


def run() -> None:
    seed_bio()
    seed_social_links()
    seed_experience()
    seed_education()
    seed_languages()
    seed_projects()
    seed_beyond()
    db.session.commit()
