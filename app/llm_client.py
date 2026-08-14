"""LLM client abstraction.

Supports two zero-cost backends, selected via LLM_PROVIDER:
  - "ollama" (default): fully local, no API key, no data leaves the machine.
  - "nvidia": NVIDIA NIM free-tier API (OpenAI-compatible), useful when no
    local GPU is available — free API key from build.nvidia.com.

Paid providers (OpenAI/Anthropic) are intentionally not wired in: the task
allows any of the three, and both free options avoid billing entirely.
"""

from __future__ import annotations

import json
import os

import httpx

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
REQUEST_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "120"))

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
NVIDIA_MODEL = os.getenv("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")


class LlmError(RuntimeError):
    """Raised when the LLM backend is unreachable or returns an error."""


async def summarize(document_text: str, prompt: str) -> str:
    """Send the document text + instruction prompt to the configured backend.

    Truncates very long documents defensively — most tender packages have
    the commercially relevant terms in the first several thousand tokens,
    and smaller models have limited context windows.
    """
    max_chars = 24_000
    if len(document_text) > max_chars:
        document_text = document_text[:max_chars]

    full_prompt = f"{prompt}\n\n---\nДОКУМЕНТ:\n{document_text}"

    if LLM_PROVIDER == "nvidia":
        return await _summarize_nvidia(full_prompt)
    return await _summarize_ollama(full_prompt)


async def _summarize_ollama(full_prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LlmError(
            f"Could not reach Ollama at {OLLAMA_HOST}. "
            f"Make sure `ollama serve` is running and the model "
            f"`{OLLAMA_MODEL}` is pulled (`ollama pull {OLLAMA_MODEL}`)."
        ) from exc

    data = response.json()
    return data.get("response", "").strip()


async def _summarize_nvidia(full_prompt: str) -> str:
    if not NVIDIA_API_KEY:
        raise LlmError(
            "NVIDIA_API_KEY is not set. Get a free key at build.nvidia.com "
            "and export it, or switch LLM_PROVIDER back to 'ollama'."
        )

    payload = {
        "model": NVIDIA_MODEL,
        "messages": [{"role": "user", "content": full_prompt}],
        "temperature": 0.1,
        "max_tokens": 1024,
    }
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{NVIDIA_BASE_URL}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise LlmError(f"NVIDIA NIM request failed: {exc}") from exc

    data = response.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise LlmError(f"Unexpected NVIDIA NIM response shape: {data!r}") from exc


def build_extraction_prompt() -> str:
    """Instruction prompt asking for a strict JSON summary.

    Kept as a plain string (not an f-string template scattered across the
    codebase) so it's easy to iterate on prompt wording during testing
    without touching the client or API code.
    """
    return (
        "Ты помощник, который анализирует документацию по государственным "
        "тендерам. Внимательно прочитай документ ниже и верни ТОЛЬКО валидный "
        "JSON (без markdown-разметки, без пояснений до или после) со следующими "
        "полями:\n"
        '{\n'
        '  "contract_amount": "сумма контракта с валютой, или null если не указана",\n'
        '  "deadlines": "сроки выполнения работ, или null",\n'
        '  "key_requirements": ["список ключевых требований к исполнителю"],\n'
        '  "penalties": ["список штрафов и санкций за нарушение условий"]\n'
        "}\n\n"
        "Если какое-то поле невозможно найти в тексте — используй null или "
        "пустой список, не придумывай данные."
    )


def parse_llm_json(raw_response: str) -> dict:
    """Parse the model's response into a dict, tolerating minor formatting noise.

    Local models sometimes wrap JSON in ```json fences or add stray text
    despite instructions. This strips the common cases before failing loudly.
    """
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise LlmError(f"Model did not return JSON. Raw response: {raw_response!r}")

    try:
        return json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LlmError(f"Could not parse model JSON: {exc}. Raw: {raw_response!r}") from exc
