"""Más allá del código: a flat, tag-catalogued list."""

API = "/api/v1"


def test_beyond_lists_entries_in_the_asked_language(client, seeded):
    payload = client.get(f"{API}/beyond?lang=es").get_json()
    items = payload["data"]
    assert payload["meta"]["total"] == 3
    assert [item["title"] for item in items] == [
        "Libro actual",
        "Rutina de flexibilidad",
        "Primera serie",
    ]

    english = client.get(f"{API}/beyond?lang=en").get_json()["data"]
    assert [item["title"] for item in english] == [
        "Current read",
        "Flexibility routine",
        "First series",
    ]
    # Same entries, same group ids, different rows.
    assert {item["id"] for item in items} == {item["id"] for item in english}


def test_beyond_entry_shape(client, seeded):
    book = client.get(f"{API}/beyond?tag=books&lang=es").get_json()["data"][0]
    assert book["slug"] == "libro-actual"
    assert book["status"] == "reading"
    assert book["tags"] == ["books", "reading"]
    assert book["data"] == "Autor pendiente."
    # Interest-specific fields live in metadata, not in dedicated columns.
    assert {"author", "year"} <= set(book["metadata"])


def test_beyond_filters_by_tag_and_status(client, seeded):
    assert client.get(f"{API}/beyond?tag=flex").get_json()["meta"]["total"] == 1
    assert client.get(f"{API}/beyond?tag=cooking").get_json()["meta"]["total"] == 0
    assert client.get(f"{API}/beyond?status=ongoing").get_json()["meta"]["total"] == 1


def test_beyond_tags_are_counted(client, seeded):
    tags = {
        row["tag"]: row["count"]
        for row in client.get(f"{API}/beyond/tags").get_json()["data"]
    }
    assert tags == {
        "books": 1,
        "flex": 1,
        "photography": 1,
        "reading": 1,
        "training": 1,
    }


def test_beyond_detail_by_slug(client, seeded):
    detail = client.get(f"{API}/beyond/primera-serie?lang=en").get_json()["data"]
    assert detail["title"] == "First series"
    assert detail["images"] == []

    assert client.get(f"{API}/beyond/nope").status_code == 404


def test_beyond_paginates(client, seeded):
    payload = client.get(f"{API}/beyond?per_page=2").get_json()
    assert len(payload["data"]) == 2
    assert payload["meta"]["total"] == 3


def test_beyond_admin_crud(client, auth_headers):
    created = client.post(
        f"{API}/admin/beyond",
        headers=auth_headers,
        json={
            "status": "finished",
            "tags": ["Books", "Science Fiction", "books"],
            "metadata": {"author": "Ursula K. Le Guin"},
            "translations": {
                "es": {
                    "title": "La mano izquierda de la oscuridad",
                    "data": "Relectura.",
                },
                "en": {"title": "The Left Hand of Darkness", "data": "A reread."},
            },
        },
    )
    assert created.status_code == 201, created.get_json()
    item = created.get_json()["data"]
    # Slugified and deduplicated on write; slug comes from the default language.
    assert item["tags"] == ["books", "science-fiction"]
    assert item["slug"] == "la-mano-izquierda-de-la-oscuridad"
    assert sorted(item["translations"]) == ["en", "es"]

    public = client.get(f"{API}/beyond?tag=science-fiction&lang=en").get_json()["data"]
    assert public[0]["data"] == "A reread."

    updated = client.put(
        f"{API}/admin/beyond/{item['id']}",
        headers=auth_headers,
        json={
            "status": "archived",
            "translations": {"en": {"title": "Left Hand of Darkness"}},
        },
    )
    assert updated.status_code == 200, updated.get_json()
    data = updated.get_json()["data"]
    assert data["status"] == "archived"
    assert data["translations"]["es"]["title"] == "La mano izquierda de la oscuridad"

    assert (
        client.delete(
            f"{API}/admin/beyond/{item['id']}", headers=auth_headers
        ).status_code
        == 204
    )
    assert client.get(f"{API}/beyond").get_json()["meta"]["total"] == 0


def test_beyond_rejects_unknown_status(client, auth_headers):
    response = client.post(
        f"{API}/admin/beyond",
        headers=auth_headers,
        json={"status": "inventado", "translations": {"es": {"title": "X"}}},
    )
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"
