import importlib


def _reload_llm_client():
    import app.llm_client as llm_client

    importlib.reload(llm_client)
    return llm_client


def test_defaults_to_ollama(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    import app.llm_client as llm_client

    importlib.reload(llm_client)
    assert llm_client.OLLAMA_HOST == "http://localhost:11434"
    assert llm_client.OLLAMA_MODEL == "llama3.1:8b"


def test_nvidia_defaults(monkeypatch):
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_BASE_URL", raising=False)
    monkeypatch.delenv("NVIDIA_MODEL", raising=False)
    import app.llm_client as llm_client

    importlib.reload(llm_client)
    assert llm_client.NVIDIA_API_KEY == ""
    assert llm_client.NVIDIA_BASE_URL == "https://integrate.api.nvidia.com/v1"
    assert llm_client.NVIDIA_MODEL == "stepfun-ai/step-3.7-flash"


def test_deepseek_defaults(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    import app.llm_client as llm_client

    importlib.reload(llm_client)
    assert llm_client.DEEPSEEK_API_KEY == ""
    assert llm_client.DEEPSEEK_BASE_URL == "https://api.deepseek.com"
    assert llm_client.DEEPSEEK_MODEL == "deepseek-ai/deepseek-v4-flash"
