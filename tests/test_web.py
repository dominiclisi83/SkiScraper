from fastapi.testclient import TestClient

from skiscraper.web import app


def test_config_requires_password_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_PASSWORD", "correct-horse")
    client = TestClient(app)
    assert client.get("/config").status_code == 401
    assert client.get("/config", auth=("admin", "wrong")).status_code == 401
    assert client.get("/config", auth=("admin", "correct-horse")).status_code == 200
