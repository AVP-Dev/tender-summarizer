from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_returns_html_with_upload_form():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "input" in response.text
    assert "summarize" in response.text


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
