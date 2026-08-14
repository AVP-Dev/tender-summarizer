import importlib


def test_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    import app.llm_client as llm_client

    importlib.reload(llm_client)
    assert llm_client.LLM_PROVIDER == "ollama"


def test_nvidia_requires_api_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "nvidia")
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    import app.llm_client as llm_client

    importlib.reload(llm_client)
    assert llm_client.NVIDIA_API_KEY == ""
