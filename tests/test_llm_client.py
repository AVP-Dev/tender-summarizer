import pytest

from app.llm_client import LlmError, parse_llm_json


def test_parse_clean_json():
    raw = '{"contract_amount": "1 200 000 руб.", "deadlines": "60 дней", "key_requirements": ["опыт от 3 лет"], "penalties": ["0.1% в день"]}'
    result = parse_llm_json(raw)
    assert result["contract_amount"] == "1 200 000 руб."
    assert result["key_requirements"] == ["опыт от 3 лет"]


def test_parse_json_wrapped_in_markdown_fence():
    raw = '```json\n{"contract_amount": null, "deadlines": null, "key_requirements": [], "penalties": []}\n```'
    result = parse_llm_json(raw)
    assert result["contract_amount"] is None
    assert result["key_requirements"] == []


def test_parse_json_with_leading_trailing_text():
    raw = 'Вот результат анализа:\n{"contract_amount": "500000", "deadlines": "30 дней", "key_requirements": [], "penalties": []}\nНадеюсь, это поможет!'
    result = parse_llm_json(raw)
    assert result["contract_amount"] == "500000"


def test_parse_invalid_json_raises_llm_error():
    with pytest.raises(LlmError):
        parse_llm_json("это вообще не json")


def test_parse_empty_string_raises_llm_error():
    with pytest.raises(LlmError):
        parse_llm_json("")
