"""Sobre mí: bio, experiencia, educación, idiomas — plus the language-row rules."""

API = "/api/v1"


def test_bio_requires_seed(client):
    response = client.get(f"{API}/bio")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_about_aggregates_everything(client, seeded):
    response = client.get(f"{API}/about?lang=es")
    assert response.status_code == 200
    payload = response.get_json()
    data = payload["data"]

    assert data["bio"]["full_name"] == "Clara Justino Limaco"
    assert data["bio"]["role_label"] == "Ingeniera de Software"
    assert len(data["bio"]["social_links"]) == 3
    assert len(data["experience"]) == 3
    assert len(data["education"]) == 2
    assert len(data["languages"]) == 2
    assert payload["meta"]["lang"] == "es"


def test_one_row_per_item_per_language(client, seeded, app):
    """Both languages live in the same table, one row each, sharing a group id."""
    from app.extensions import db
    from app.models import Education
    from sqlalchemy import select

    rows = db.session.scalars(select(Education)).all()
    assert len(rows) == 4  # 2 studies x 2 languages

    groups = {}
    for row in rows:
        groups.setdefault(row.education_id, []).append(row)
    assert len(groups) == 2
    for group in groups.values():
        assert sorted(row.language for row in group) == ["en", "es"]
        # Neutral values are identical across languages; only text differs.
        assert len({row.institution for row in group}) == 1
        assert len({row.start_date for row in group}) == 1
        assert len({row.title for row in group}) == 2


def test_endpoint_returns_the_row_for_the_asked_language(client, seeded):
    es = client.get(f"{API}/education?lang=es").get_json()["data"]
    en = client.get(f"{API}/education?lang=en").get_json()["data"]

    assert [item["language"] for item in es] == ["es", "es"]
    assert [item["language"] for item in en] == ["en", "en"]
    # Same item: same group id, different row and text.
    assert {item["id"] for item in es} == {item["id"] for item in en}
    assert es[0]["row_id"] != en[0]["row_id"]
    assert es[0]["title"] == "Ingeniería en Sistemas Computacionales"
    assert en[0]["title"] == "B.Eng. in Computer Systems Engineering"


def test_period_is_computed_from_dates(client, seeded):
    current = client.get(f"{API}/experience?lang=es").get_json()["data"][0]
    assert current["period"] == "2022 — Presente"
    assert current["is_current"] is True

    current_en = client.get(f"{API}/experience?lang=en").get_json()["data"][0]
    assert current_en["period"] == "2022 — Present"
    assert current_en["role"] == "Senior Software Engineer"


def test_single_year_period_is_not_duplicated(client, seeded):
    education = client.get(f"{API}/education?lang=es").get_json()["data"]
    certification = next(item for item in education if "Certificación" in item["title"])
    assert certification["period"] == "2019"


def test_unsupported_language_is_a_client_error(client, seeded):
    response = client.get(f"{API}/about?lang=fr")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "UNSUPPORTED_LANGUAGE"


def test_seed_is_idempotent_even_after_edits(client, seeded, app, auth_headers):
    """Seeds match on metadata_json->>'seed_key', not on editable content."""
    from app.extensions import db
    from app.models import Education
    from seeds import seed_initial
    from sqlalchemy import func, select

    def row_count():
        return db.session.scalar(select(func.count()).select_from(Education))

    before = row_count()

    group_id = client.get(f"{API}/admin/education", headers=auth_headers).get_json()[
        "data"
    ][0]["id"]
    client.put(
        f"{API}/admin/education/{group_id}",
        headers=auth_headers,
        json={"institution": "Renamed University", "translations": {}},
    )

    seed_initial.run()
    assert row_count() == before
    # Re-seeding restores the seeded value on both language rows.
    rows = db.session.scalars(
        select(Education).where(Education.education_id == group_id)
    ).all()
    assert {row.institution for row in rows} == {"Universidad Nacional"}
