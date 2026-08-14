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


def test_summarize_rejects_non_pdf_content_type():
    response = client.post(
        "/summarize",
        files={"file": ("doc.txt", b"hello", "text/plain")},
        data={"provider": "ollama"},
    )
    assert response.status_code == 400
    assert "Expected a PDF file" in response.json()["detail"]


def test_index_contains_provider_options_and_history():
    response = client.get("/")
    assert response.status_code == 200
    assert "Ollama" in response.text
    assert "NVIDIA" in response.text
    assert "DeepSeek" in response.text
    assert "История" in response.text
