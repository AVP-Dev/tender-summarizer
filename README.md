# Tender Document Summarizer

Сервис на FastAPI для извлечения структурированной выжимки из PDF-документов
тендерной документации: сумма контракта, сроки выполнения, требования
к исполнителю и штрафные санкции. Текст извлекается из PDF и передаётся
LLM-модели; результат возвращается в виде человекочитаемого текста на русском.

## Возможности

- Загрузка PDF через веб-интерфейс (drag&drop) или HTTP API
- Три LLM-провайдера: Ollama (локально), NVIDIA NIM, DeepSeek
- Выбор провайдера, модели и API-ключа без изменения конфигурации
- Ограничение размера файла (20 МБ) и таймаут LLM-запроса
- История запросов в веб-интерфейсе (в рамках сессии браузера)

## Требования

- Python 3.10–3.12 (синтаксис `str | None`; pydantic 2.9 не собирается
  на Python 3.14)
- [uv](https://docs.astral.sh/uv/) — рекомендуется для управления окружением
- Для провайдера Ollama — установленный и запущенный [Ollama](https://ollama.com)
- Для облачных провайдеров — API-ключ соответствующего сервиса
- Для обработки сканированных PDF — Tesseract (системная установка):
  `brew install tesseract tesseract-lang`. pytesseract — Python-обёртка,
  устанавливается через pip в venv; бинарник Tesseract ставится brew
  системно и вызывается из venv как внешняя программа.

## Установка

```bash
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
```

## Запуск

```bash
python -m uvicorn app.main:app --reload
```

> На macOS не используйте `uvicorn` напрямую — multiprocessing spawn
> может подхватить системный Python вместо venv. Запуск через
> `python -m uvicorn` гарантирует использование интерпретатора из
> активированного окружения.

После запуска:

| Ресурс | Адрес |
| --- | --- |
| Веб-интерфейс | http://localhost:8000/ |
| Swagger UI (документация API) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

## LLM-провайдеры

Провайдер выбирается в веб-интерфейсе или передаётся параметром запроса.
Параметры каждого провайдера настраиваются независимо.

| Провайдер | Значение `provider` | Ключ API | Base URL по умолчанию | Модель по умолчанию |
| --- | --- | --- | --- | --- |
| Ollama (локально) | `ollama` | не требуется | `http://localhost:11434` | `llama3.1:8b` |
| NVIDIA NIM | `nvidia` | [build.nvidia.com](https://build.nvidia.com) | `https://integrate.api.nvidia.com/v1` | `stepfun-ai/step-3.7-flash` |
| DeepSeek | `deepseek` | [platform.deepseek.com](https://platform.deepseek.com) | `https://api.deepseek.com` | `deepseek-ai/deepseek-v4-flash` |

### Ollama

```bash
ollama pull llama3.1:8b
ollama serve
```

Если Ollama запущен на другой машине или порту, укажите адрес в поле
«Адрес» веб-интерфейса или через переменную `OLLAMA_HOST`.

### NVIDIA NIM

Получите бесплатный ключ на https://build.nvidia.com и вставьте его
в веб-интерфейсе при выборе провайдера NVIDIA NIM.

### DeepSeek

Получите ключ на https://platform.deepseek.com и вставьте его
в веб-интерфейсе при выборе провайдера DeepSeek.

API-ключи, введённые в веб-интерфейсе, передаются серверу только в момент
запроса и не сохраняются на диск.

## Конфигурация

Переменные окружения задают значения по умолчанию; параметры запроса
и веб-интерфейса имеют приоритет.

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `OLLAMA_HOST` | `http://localhost:11434` | Адрес сервера Ollama |
| `OLLAMA_MODEL` | `llama3.1:8b` | Модель Ollama |
| `NVIDIA_API_KEY` | — | Ключ API NVIDIA NIM |
| `NVIDIA_BASE_URL` | `https://integrate.api.nvidia.com/v1` | Базовый URL NVIDIA NIM |
| `NVIDIA_MODEL` | `stepfun-ai/step-3.7-flash` | Модель NVIDIA NIM |
| `DEEPSEEK_API_KEY` | — | Ключ API DeepSeek |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | Базовый URL DeepSeek |
| `DEEPSEEK_MODEL` | `deepseek-ai/deepseek-v4-flash` | Модель DeepSeek |
| `LLM_TIMEOUT_SECONDS` | `120` | Таймаут запроса к LLM |

## HTTP API

### POST /summarize

Загружает PDF-файл и возвращает выжимку, сформированную LLM.

Параметры (multipart/form-data):

| Параметр | Тип | Обязательный | Описание |
| --- | --- | --- | --- |
| `file` | file | да | PDF-файл (до 20 МБ) |
| `provider` | string | нет | `ollama` (по умолчанию), `nvidia` или `deepseek` |
| `model` | string | нет | Переопределяет модель провайдера |
| `api_key` | string | нет | API-ключ облачного провайдера |
| `base_url` | string | нет | Переопределяет base URL облачного провайдера |
| `host` | string | нет | Переопределяет адрес Ollama |

Примеры:

```bash
# Ollama
curl -F "file=@tender.pdf" -F "provider=ollama" http://localhost:8000/summarize

# NVIDIA NIM
curl -F "file=@tender.pdf" -F "provider=nvidia" \
     -F "api_key=YOUR_NVIDIA_KEY" http://localhost:8000/summarize

# DeepSeek
curl -F "file=@tender.pdf" -F "provider=deepseek" \
     -F "api_key=YOUR_DEEPSEEK_KEY" http://localhost:8000/summarize
```

Ответ `200 OK`:

```json
{
  "filename": "tender.pdf",
  "summary": "1. Сумма контракта: 1 200 000 руб.\n2. Сроки выполнения: 60 дней…"
}
```

Коды ошибок:

| Код | Причина |
| --- | --- |
| `400` | Файл не является PDF |
| `413` | Размер файла превышает 20 МБ |
| `422` | Из PDF не удалось извлечь текст (например, скан без текстового слоя) |
| `502` | Ошибка обращения к LLM-провайдеру (таймаут, неверный ключ, недоступный сервис) |

### GET /health

Проверка доступности сервиса.

```bash
curl http://localhost:8000/health
```

```json
{"status": "ok"}
```

## Тесты

```bash
uv pip install pytest
pytest
```

## Архитектура

| Модуль | Назначение |
| --- | --- |
| `app/main.py` | HTTP-эндпоинты, валидация загрузки, обработка ошибок |
| `app/pdf_reader.py` | Извлечение текста из PDF (pypdf) |
| `app/llm_client.py` | Клиенты Ollama / NVIDIA NIM / DeepSeek, промпт, таймауты |
| `app/schemas.py` | Pydantic-модели ответов |
| `app/web_ui.py` | Встроенная HTML-страница веб-интерфейса |

Разделение слоёв позволяет заменить парсер PDF (например, добавить OCR для
сканов) или добавить нового LLM-провайдера без изменения API-слоя.

## Ограничения

- Аутентификация и rate-limiting отсутствуют — сервис предназначен для
  локального использования

## Лицензия

MIT. Подробности см. в файле [LICENSE](LICENSE).
