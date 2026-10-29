"""Infrastructure endpoint."""

import pytest
from app import create_app
from app.config import ProductionConfig

API = "/api/v1"


def test_health(client):
    response = client.get(f"{API}/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "db": "ok"}


def test_production_refuses_placeholder_secrets(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "change-me")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app("production")
