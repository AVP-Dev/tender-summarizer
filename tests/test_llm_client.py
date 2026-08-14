import pytest

from app.llm_client import build_extraction_prompt, summarize


def test_prompt_asks_for_readable_sections():
    prompt = build_extraction_prompt()
    assert "Сумма контракта" in prompt
    assert "Сроки выполнения" in prompt
    assert "Ключевые требования" in prompt
    assert "Штрафы и санкции" in prompt


@pytest.mark.anyio
async def test_summarize_ollama_uses_provided_host_and_model(monkeypatch):
    """summarize() should send the request to the given host/model."""
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"response": "ok"}

    class FakeClient:
        def __init__(self, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def post(self, url, json=None):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    result = await summarize(
        "текст документа",
        "инструкция",
        provider="ollama",
        host="http://192.168.1.5:11434",
        model="llama3.2:3b",
    )
    assert result == "ok"
    assert captured["url"] == "http://192.168.1.5:11434/api/generate"
    assert captured["json"]["model"] == "llama3.2:3b"
    assert "инструкция" in captured["json"]["prompt"]
