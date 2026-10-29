import io

from PIL import Image

API = "/api/v1"


def _png_bytes(size=(40, 30), color=(120, 180, 90)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def _upload(client, auth_headers, name="photo.png", **kwargs):
    return client.post(
        f"{API}/admin/media",
        headers=auth_headers,
        data={"file": (_png_bytes(**kwargs), name)},
        content_type="multipart/form-data",
    )


def test_upload_requires_auth(client):
    assert client.post(f"{API}/admin/media", data={}).status_code == 401


def test_upload_stores_dimensions_and_serves_file(client, auth_headers):
    response = client.post(
        f"{API}/admin/media",
        headers=auth_headers,
        data={"file": (_png_bytes(), "photo.png"), "alt_text": "A green square"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_json()
    media = response.get_json()["data"]
    assert (media["width"], media["height"]) == (40, 30)
    assert media["mime_type"] == "image/png"
    assert media["alt"] == "A green square"

    served = client.get(media["url"].replace("/static/uploads", f"{API}/files"))
    assert served.status_code == 200


def test_upload_strips_exif_and_applies_rotation(client, auth_headers):
    exif = Image.Exif()
    exif[0x0112] = 6  # orientation: rotate 90° clockwise to display
    exif[0x8825] = {2: (41.0, 23.0, 0.0)}  # GPSInfo: latitude
    buffer = io.BytesIO()
    Image.new("RGB", (40, 30), (200, 80, 80)).save(buffer, format="JPEG", exif=exif)
    buffer.seek(0)

    response = client.post(
        f"{API}/admin/media",
        headers=auth_headers,
        data={"file": (buffer, "phone.jpg")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_json()
    media = response.get_json()["data"]
    assert (media["width"], media["height"]) == (30, 40)

    served = client.get(media["url"].replace("/static/uploads", f"{API}/files"))
    with Image.open(io.BytesIO(served.data)) as stored:
        assert stored.size == (30, 40)
        assert not stored.getexif()


def test_upload_rejects_non_image_disguised_as_png(client, auth_headers):
    fake = io.BytesIO(b"this is not an image at all")
    response = client.post(
        f"{API}/admin/media",
        headers=auth_headers,
        data={"file": (fake, "evil.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_IMAGE"


def test_identical_upload_is_deduplicated(client, auth_headers):
    first = _upload(client, auth_headers, "a.png")
    second = _upload(client, auth_headers, "b.png")
    assert second.status_code == 200
    assert first.get_json()["data"]["id"] == second.get_json()["data"]["id"]


def test_cover_media_cannot_be_deleted(client, auth_headers):
    upload = _upload(client, auth_headers, "cover.png", size=(10, 10), color=(1, 2, 3))
    media = upload.get_json()["data"]

    client.post(
        f"{API}/admin/projects",
        headers=auth_headers,
        json={
            "cover_id": media["id"],
            "translations": {"es": {"title": "Con portada"}},
        },
    )

    response = client.delete(f"{API}/admin/media/{media['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert response.get_json()["error"]["details"]["referenced_by"] == "project"


def test_gallery_media_cannot_be_deleted(client, auth_headers):
    upload = _upload(client, auth_headers, "shot.png", size=(12, 12), color=(9, 9, 9))
    media = upload.get_json()["data"]

    created = client.post(
        f"{API}/admin/projects",
        headers=auth_headers,
        json={
            "translations": {
                "es": {
                    "title": "Con galería",
                    "images": [
                        {"media_id": media["id"], "caption": "Pantalla principal"}
                    ],
                }
            }
        },
    )
    assert created.status_code == 201, created.get_json()
    gallery = created.get_json()["data"]["images"]
    # The url is resolved at write time, so reads need no extra query.
    assert gallery[0]["url"] == media["url"]
    assert gallery[0]["caption"] == "Pantalla principal"

    response = client.delete(f"{API}/admin/media/{media['id']}", headers=auth_headers)
    assert response.status_code == 409
    assert response.get_json()["error"]["details"]["referenced_by"] == "project.images"


def test_gallery_rejects_unknown_media(client, auth_headers):
    response = client.post(
        f"{API}/admin/projects",
        headers=auth_headers,
        json={
            "translations": {
                "es": {
                    "title": "Galería inválida",
                    "images": [{"media_id": "00000000-0000-4000-8000-000000000000"}],
                }
            }
        },
    )
    assert response.status_code == 404


def test_missing_translation_falls_back_and_flags_it(client, auth_headers):
    client.post(
        f"{API}/admin/projects",
        headers=auth_headers,
        json={"translations": {"es": {"title": "Solo en español"}}},
    )
    payload = client.get(f"{API}/projects?lang=en").get_json()
    assert payload["data"][0]["title"] == "Solo en español"
    assert payload["data"][0]["language"] == "es"
    assert payload["meta"]["lang_fallback"] is True
    assert payload["meta"]["lang"] == "en"


def test_no_fallback_flag_when_translation_exists(client, seeded):
    payload = client.get(f"{API}/projects?lang=en").get_json()
    assert "lang_fallback" not in payload["meta"]
