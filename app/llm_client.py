"""LLM client abstraction.

Supports several backends, chosen per-request by the API client:
  - "ollama": fully local, no API key, no data leaves the machine.
  - "nvidia": NVIDIA NIM API (OpenAI-compatible), free key from
    build.nvidia.com — default model stepfun-ai/step-3.7-flash
    (multilingual, supports Russian).
  - "deepseek": DeepSeek API (OpenAI-compatible, api.deepseek.com).

Environment variables provide defaults; the web UI can override them
per request (provider, model, API key, Ollama host).
"""

from __future__ import annotations

import os

import httpx

REQUEST_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "stepfun-ai/step-3.7-flash")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-ai/deepseek-v4-flash")


class LlmError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns an error."""


async def summarize(
    document_text: str,
    prompt: str,
    *,
    provider: str = "ollama",
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    host: str | None = None,
) -> str:
    """Send the document text + instruction prompt to the chosen backend.

    Truncates very long documents defensively — most tender packages have
    the commercially relevant terms in the first several thousand tokens,
    and smaller models have limited context windows.

    provider: "ollama" | "nvidia" | "deepseek". model/api_key/base_url/host
    optionally override the environment defaults (the web UI sends them).
    """
    max_chars = 24_000
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars]

    full_prompt = f"{prompt}\n\n---\nДОКУМЕНТ:\n{document_text}"

    if provider == "nvidia" or provider == "deepseek":
        return await _summarize_openai_compatible(
            full_prompt,
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,
        )
    return await _summarize_ollama(full_prompt, host=host, model=model)


async def _summarize_ollama(
    full_prompt: str,
    *,
    host: str | None = None,
    model: str | None = None,
) -> str:
    ollama_host = host or OLLAMA_HOST
    ollama_model = model or OLLAMA_MODEL
    payload = {
        "model": ollama_model,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{ollama_host}/api/generate", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LlmError(
            f"Could not reach Ollama at {ollama_host}. "
            f"Make sure `ollama serve` is running and the model "
            f"`{ollama_model}` is pulled (`ollama pull {ollama_model}`)."
        ) from exc

    data = response.json()
    return data.get("response", "").strip()


async def _summarize_openai_compatible(
    full_prompt: str,
    *,
    provider: str,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> str:
    """Call an OpenAI-compatible endpoint (NVIDIA NIM / DeepSeek) via httpx.

    Each provider has its own defaults: API key, base URL and model are
    never shared between providers. Plain non-streaming call with
    explicit timeout.
    """
    if provider == "deepseek":
        key = api_key if api_key is not None else DEEPSEEK_API_KEY
        url = (base_url or DEEPSEEK_BASE_URL).rstrip("/") + "/chat/completions"
        model_name = model or DEEPSEEK_MODEL
    else:
        key = api_key if api_key is not None else NVIDIA_API_KEY
        url = (base_url or NVIDIA_BASE_URL).rstrip("/") + "/chat/completions"
        model_name = model or NVIDIA_MODEL

    if not key:
        raise LlmError(
            f"API key is required for provider '{provider}'. "
            "Get a key at the provider's site, paste it in the web UI, "
            "or switch to the local Ollama option."
        )

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.1,
        "top_p": 0.95,
        "max_tokens": 16384,
        "seed": 42,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS)) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
    except httpx.TimeoutException:
        raise LlmError(f"{provider} request timed out after {REQUEST_TIMEOUT_SECONDS}s.")
    except httpx.HTTPStatusError as exc:
        raise LlmError(f"{provider} returned HTTP {exc.response.status_code}: {exc.response.text[:300]}") from exc
    except httpx.HTTPError as exc:
        raise LlmError(f"{provider} request failed: {exc}") from exc

    data = resp.json()
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise LlmError(f"{provider} returned empty content. Raw: {data}")
    return content.strip()


def build_extraction_prompt() -> str:
    """Instruction prompt asking for a human-readable summary.

    Kept as a plain string (not an f-string template scattered across the
    codebase) so it's easy to iterate on prompt wording during testing
    without touching the client or API code.
    """
    return (
        "Ты помощник, который анализирует документацию по государственным "
        "тендерам. Внимательно прочитай документ ниже и составь краткую "
        "структурированную выжимку на русском языке. Используй такие разделы:\n\n"
        "1. Сумма контракта\n"
        "2. Сроки выполнения\n"
        "3. Ключевые требования к исполнителю\n"
        "4. Штрафы и санкции\n\n"
        "Пиши короткими тезисами, по делу, без воды. Если какой-то информации "
        "в документе нет — так и напиши «не указано», не выдумывай данные."
    )
