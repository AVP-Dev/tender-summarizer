# Tender Document Summarizer

Небольшой сервис на FastAPI: принимает PDF тендерной документации,
извлекает текст и с помощью LLM возвращает структурированную выжимку —
сумму контракта, сроки, ключевые требования к исполнителю и штрафы.

## Почему так

Задача допускает три варианта LLM-бэкенда: OpenAI, Anthropic или
локальную бесплатную модель. Выбраны два бесплатных пути без биллинга —
**Ollama** (полностью локально, данные не покидают машину) и
**NVIDIA NIM** (бесплатный API-ключ, если локального GPU нет под рукой).
Платные API намеренно не подключены — для тестового задания это не нужно.

- **Парсинг PDF вынесен в отдельный модуль** (`app/pdf_reader.py`), не
  завязан на FastAPI — если понадобится OCR-фолбэк для сканов, это
  отдельная точка расширения, не переписывание API-слоя.
- **Промпт живёт отдельной функцией** (`build_extraction_prompt`), не
  размазан по коду — с ним проще итерировать при тестировании на реальных
  документах.
- **Ответ модели парсится защитным образом** (`parse_llm_json`): модели
  иногда оборачивают JSON в markdown-фenced блоки или добавляют пояснения
  до/после — это не должно ломать эндпоинт.

## Быстрый старт

### Вариант 1: локально через Ollama

```bash
ollama pull llama3.1:8b
ollama serve
```

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # LLM_PROVIDER=ollama по умолчанию
uvicorn app.main:app --reload
```

### Вариант 2: через NVIDIA NIM (бесплатный ключ на build.nvidia.com)

Используется через официальный `openai` SDK (NIM — OpenAI-совместимый эндпоинт),
модель по умолчанию — `nvidia/nemotron-3.5-lightning-30b-a3b` (reasoning-модель;
её reasoning-трейс отбрасывается, в ответ идёт только финальный content).

```bash
cp .env.example .env
# в .env: LLM_PROVIDER=nvidia, NVIDIA_API_KEY=ваш_ключ
uvicorn app.main:app --reload
```

### Запрос

```bash
curl -F "file=@tender.pdf" http://localhost:8000/summarize
```

Ответ:

```json
{
  "filename": "tender.pdf",
  "summary": {
    "contract_amount": "1 200 000 руб.",
    "deadlines": "60 дней с даты подписания контракта",
    "key_requirements": ["опыт работы от 3 лет", "СРО-допуск"],
    "penalties": ["0.1% от суммы контракта за каждый день просрочки"]
  }
}
```

## Тесты

```bash
pip install pytest
pytest
```

## Что осознанно не сделано (cut list)

- **OCR для сканированных PDF** — задача про текстовые тендерные документы,
  большинство госзакупок публикуют текстовый PDF, а не скан. OCR-пайплайн
  увеличил бы скоуп без явной пользы для оценки задания.
- **Множественные LLM-провайдеры через фреймворк-абстракцию** (LangChain
  и т.п.) — два простых HTTP-клиента прозрачнее для ревью, чем ещё один
  слой поверх HTTP.
- **Аутентификация и rate-limiting** — не входит в условия задания.

## Структура

```
app/
  main.py          # FastAPI-эндпоинты
  pdf_reader.py    # извлечение текста из PDF
  llm_client.py    # вызов Ollama / NVIDIA NIM, парсинг JSON-ответа
  schemas.py       # Pydantic-модели ответа
tests/
  test_llm_client.py
  test_provider_selection.py
```
