import os

import pytest
from sqlalchemy import text

os.environ.setdefault("FLASK_ENV", "testing")

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import AdminUser  # noqa: E402


@pytest.fixture(scope="session")
def app():
    application = create_app("testing")
    with application.app_context():
        _db.session.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        _db.session.commit()
        _db.drop_all()
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(autouse=True)
def _clean_tables(app):
    """Truncate between tests so each one starts from a known state.

    The session must be released first: an open transaction on the session
    scoped connection holds row locks and TRUNCATE would block on itself.
    """
    yield
    _db.session.rollback()
    _db.session.remove()
    tables = ",".join(f'"{table.name}"' for table in _db.metadata.sorted_tables)
    with _db.engine.begin() as connection:
        connection.execute(text("SET LOCAL lock_timeout = '5s'"))
        connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded(app):
    """Load the real frontend content. Runs in the session app context on purpose:
    a nested one would open a second connection and fight the truncate fixture."""
    from seeds import seed_initial

    seed_initial.run()
    _db.session.remove()


@pytest.fixture
def admin(app):
    user = AdminUser(email="admin@example.com", full_name="Admin")
    user.set_password("supersecret123")
    _db.session.add(user)
    _db.session.commit()
    _db.session.remove()
    return {"email": "admin@example.com", "password": "supersecret123"}


@pytest.fixture
def auth_headers(client, admin):
    response = client.post("/api/v1/auth/login", json=admin)
    assert response.status_code == 200, response.get_json()
    return {"Authorization": f"Bearer {response.get_json()['access_token']}"}
