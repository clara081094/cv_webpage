"""Proyectos."""

API = "/api/v1"


def test_projects_list_and_tag_filter(client, seeded):
    listing = client.get(f"{API}/projects?lang=en").get_json()
    assert listing["meta"]["total"] == 3
    assert listing["data"][0]["slug"] == "school-management-platform"
    assert "react" in listing["data"][0]["tags"]

    filtered = client.get(f"{API}/projects?tag=flask").get_json()
    assert [item["slug"] for item in filtered["data"]] == ["recommendations-api"]

    featured = client.get(f"{API}/projects?featured=true").get_json()
    assert len(featured["data"]) == 1


def test_project_detail_and_404(client, seeded):
    detail = client.get(f"{API}/projects/recommendations-api?lang=es").get_json()[
        "data"
    ]
    assert detail["title"] == "API de recomendaciones"
    assert detail["images"] == []

    assert client.get(f"{API}/projects/nope").status_code == 404


def test_slug_is_shared_by_both_language_rows(client, seeded):
    es = client.get(f"{API}/projects/recommendations-api?lang=es").get_json()["data"]
    en = client.get(f"{API}/projects/recommendations-api?lang=en").get_json()["data"]
    assert es["slug"] == en["slug"] == "recommendations-api"
    assert es["id"] == en["id"]
    assert es["title"] != en["title"]


def test_project_tags_are_counted(client, seeded):
    tags = {
        row["tag"]: row["count"] for row in client.get(f"{API}/tags").get_json()["data"]
    }
    assert tags["postgresql"] == 2
    assert tags["react"] == 1


def test_data_is_the_translated_body(client, seeded):
    """`data` replaced `description`: it is a translated column, one value per row."""
    es = client.get(f"{API}/projects?lang=es").get_json()["data"]
    en = client.get(f"{API}/projects?lang=en").get_json()["data"]

    by_slug_es = {item["slug"]: item["data"] for item in es}
    by_slug_en = {item["slug"]: item["data"] for item in en}

    assert by_slug_es["recommendations-api"].startswith("Servicio backend")
    assert by_slug_en["recommendations-api"].startswith("Backend recommendation")
    assert "description" not in es[0]
    assert "summary" not in es[0]
