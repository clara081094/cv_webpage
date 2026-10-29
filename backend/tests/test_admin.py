API = "/api/v1"


def test_admin_requires_token(client):
    assert client.get(f"{API}/admin/projects").status_code == 401
    assert client.post(f"{API}/admin/projects", json={}).status_code == 401


def test_login_rejects_wrong_password(client, admin):
    response = client.post(
        f"{API}/auth/login", json={"email": admin["email"], "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_returns_current_admin(client, auth_headers):
    payload = client.get(f"{API}/auth/me", headers=auth_headers).get_json()["data"]
    assert payload["email"] == "admin@example.com"


def test_project_crud_roundtrip(client, auth_headers, app):
    create = client.post(
        f"{API}/admin/projects",
        headers=auth_headers,
        json={
            "is_featured": True,
            "tags": ["Flask", "Postgres"],
            "translations": {
                "es": {"title": "Nuevo proyecto", "data": "Cuerpo en español"},
                "en": {"title": "New project", "data": "Body in English"},
            },
        },
    )
    assert create.status_code == 201, create.get_json()
    project = create.get_json()["data"]
    assert project["slug"] == "nuevo-proyecto"
    assert project["tags"] == ["flask", "postgres"]
    assert sorted(project["translations"]) == ["en", "es"]

    # One insert wrote two rows, one per language.
    from app.extensions import db
    from app.models import Project
    from sqlalchemy import select

    rows = db.session.scalars(select(Project)).all()
    assert len(rows) == 2
    assert len({row.project_id for row in rows}) == 1

    public = client.get(f"{API}/projects?lang=en").get_json()["data"]
    assert public[0]["title"] == "New project"

    update = client.put(
        f"{API}/admin/projects/{project['id']}",
        headers=auth_headers,
        json={
            "is_published": False,
            "translations": {"en": {"title": "Renamed project"}},
        },
    )
    assert update.status_code == 200, update.get_json()
    data = update.get_json()["data"]
    assert data["translations"]["en"]["title"] == "Renamed project"
    # The Spanish row survives a single-language update.
    assert data["translations"]["es"]["title"] == "Nuevo proyecto"

    assert client.get(f"{API}/projects").get_json()["data"] == []

    deleted = client.delete(
        f"{API}/admin/projects/{project['id']}", headers=auth_headers
    )
    assert deleted.status_code == 204
    # Deleting the item removed both language rows.
    assert db.session.scalars(select(Project)).all() == []


def test_neutral_fields_stay_in_sync_across_languages(client, auth_headers, app):
    """A neutral field is duplicated per row, so the writer updates every row."""
    from app.extensions import db
    from app.models import Experience
    from sqlalchemy import select

    created = client.post(
        f"{API}/admin/experience",
        headers=auth_headers,
        json={
            "company": "Acme",
            "start_date": "2020-01-01",
            "translations": {
                "es": {"role": "Ingeniera"},
                "en": {"role": "Engineer"},
            },
        },
    )
    assert created.status_code == 201, created.get_json()
    group_id = created.get_json()["data"]["id"]

    client.put(
        f"{API}/admin/experience/{group_id}",
        headers=auth_headers,
        json={"company": "Acme Corp", "start_date": "2021-06-01", "translations": {}},
    )

    rows = db.session.scalars(select(Experience)).all()
    assert {row.company for row in rows} == {"Acme Corp"}
    assert len({row.start_date for row in rows}) == 1
    assert {row.role for row in rows} == {"Ingeniera", "Engineer"}


def test_adding_a_language_later_copies_neutral_values(client, auth_headers):
    created = client.post(
        f"{API}/admin/education",
        headers=auth_headers,
        json={
            "institution": "Universidad X",
            "start_date": "2015-01-01",
            "translations": {"es": {"title": "Maestría"}},
        },
    )
    assert created.status_code == 201, created.get_json()
    group_id = created.get_json()["data"]["id"]

    added = client.put(
        f"{API}/admin/education/{group_id}",
        headers=auth_headers,
        json={
            "institution": "Universidad X",
            "translations": {"en": {"title": "Master"}},
        },
    )
    assert added.status_code == 200, added.get_json()

    english = client.get(f"{API}/education?lang=en").get_json()["data"][0]
    assert english["title"] == "Master"
    assert english["start_date"] == "2015-01-01"


def test_language_row_without_required_text_is_rejected(client, auth_headers):
    """Every language row carries its own NOT NULL title, so it cannot be omitted."""
    response = client.post(
        f"{API}/admin/education",
        headers=auth_headers,
        json={
            "institution": "Universidad X",
            "translations": {
                "es": {"title": "Maestría"},
                "en": {"description": "no title"},
            },
        },
    )
    assert response.status_code == 422
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "translations.en.title" in error["details"]


def test_create_without_translations_is_rejected(client, auth_headers):
    response = client.post(
        f"{API}/admin/education",
        headers=auth_headers,
        json={"institution": "Universidad X"},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "MISSING_TRANSLATIONS"


def test_bio_put_is_an_upsert(client, auth_headers):
    body = {
        "full_name": "Clara Justino Limaco",
        "email": "clara@example.com",
        "translations": {
            "es": {"role_label": "Ingeniera"},
            "en": {"role_label": "Engineer"},
        },
    }
    first = client.put(f"{API}/admin/bio", headers=auth_headers, json=body)
    assert first.status_code == 200, first.get_json()

    body["full_name"] = "Clara J. Limaco"
    second = client.put(f"{API}/admin/bio", headers=auth_headers, json=body)
    assert second.get_json()["data"]["full_name"] == "Clara J. Limaco"

    public = client.get(f"{API}/bio?lang=en").get_json()["data"]
    assert public["full_name"] == "Clara J. Limaco"
    assert public["role_label"] == "Engineer"


def test_validation_error_lists_fields(client, auth_headers):
    response = client.post(
        f"{API}/admin/languages",
        headers=auth_headers,
        json={
            "code": "de",
            "percentage": 150,
            "translations": {"es": {"name": "Alemán"}},
        },
    )
    assert response.status_code == 422
    error = response.get_json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "percentage" in error["details"]


def test_reorder_updates_every_language_row(client, auth_headers, seeded, app):
    from app.extensions import db
    from app.models import Project
    from sqlalchemy import select

    projects = client.get(f"{API}/admin/projects", headers=auth_headers).get_json()[
        "data"
    ]
    payload = {
        "items": [
            {"id": projects[0]["id"], "display_order": 5},
            {"id": projects[1]["id"], "display_order": 1},
        ]
    }
    response = client.patch(
        f"{API}/admin/projects/reorder", headers=auth_headers, json=payload
    )
    assert response.status_code == 200
    assert response.get_json()["data"]["updated"] == 2

    moved = db.session.scalars(
        select(Project).where(Project.project_id == projects[0]["id"])
    ).all()
    assert {row.display_order for row in moved} == {5}

    public = client.get(f"{API}/projects").get_json()["data"]
    assert public[0]["slug"] == projects[1]["slug"]


def test_social_link_crud(client, auth_headers):
    created = client.post(
        f"{API}/admin/social-links",
        headers=auth_headers,
        json={
            "platform": "linkedin",
            "url": "https://linkedin.com/in/clara",
            "label": "LinkedIn",
            "icon_name": "linkedin",
        },
    )
    assert created.status_code == 201, created.get_json()
    link_id = created.get_json()["data"]["id"]

    updated = client.put(
        f"{API}/admin/social-links/{link_id}",
        headers=auth_headers,
        json={
            "platform": "linkedin",
            "url": "https://linkedin.com/in/clara-limaco",
            "label": "LinkedIn",
            "icon_name": "linkedin",
        },
    )
    assert updated.get_json()["data"]["url"].endswith("clara-limaco")

    assert (
        client.delete(
            f"{API}/admin/social-links/{link_id}", headers=auth_headers
        ).status_code
        == 204
    )
