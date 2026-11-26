"""Regression tests for the model-card evaluator's pinned-selection scoring bugs."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import heretic_model_card_eval as hmce  # noqa: E402

TOKENIZER = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\source\tokenizer.json")
SELECTION = Path(r"H:\Strata\models\inkling2-heretic-bonsai2-pq2_0\evaluation\mmlu-sm120\selection.json")


def test_mmlu_token_selection_sends_decoded_question_to_server(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = json.loads(SELECTION.read_text(encoding="utf-8"))
    item = next(i for i in data["items"] if i["row"] == 187)
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({"items": [item]}), encoding="utf-8")
    prompts: list[str] = []

    def fake_chat(base_url: str, messages: list[dict[str, object]], **kwargs: object) -> tuple[dict[str, object], float]:
        prompts.append(str(messages[0]["content"]))
        return {"choices": [{"message": {"content": "B"}, "finish_reason": "stop"}]}, 0.01

    monkeypatch.setattr(hmce, "chat_completion", fake_chat)
    result = hmce.run_mmlu_subset("http://127.0.0.1:1", selection, 1, tokenizer_path=TOKENIZER)

    assert result["correct"] == 1
    assert "basketball player scored 18 points" in prompts[0]
    assert "18 = p" in prompts[0]


def test_mmlu_all_empty_responses_are_reported_as_not_measured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    data = json.loads(SELECTION.read_text(encoding="utf-8"))
    item = next(i for i in data["items"] if i["row"] == 187)
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({"items": [item]}), encoding="utf-8")
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}, 0.01),
    )
    result = hmce.run_mmlu_subset("http://127.0.0.1:1", selection, 1, tokenizer_path=TOKENIZER)
    assert result["measured"] is False
    assert "empty" in result["reason"].lower()
    assert result["records"][0]["response_chars"] == 0


def test_mmlu_selection_without_text_or_tokens_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    selection = tmp_path / "selection.json"
    selection.write_text(json.dumps({"items": [{"answer": 1}]}), encoding="utf-8")
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": "A"}, "finish_reason": "stop"}]}, 0.01),
    )
    with pytest.raises(ValueError, match="tokens|question"):
        hmce.run_mmlu_subset("http://127.0.0.1:1", selection, 1, tokenizer_path=TOKENIZER)


def test_aime_gold_accepts_aime25_prefixed_keys(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "test.jsonl").write_text(json.dumps({"id": "0", "problem": "2+2?"}) + "\n", encoding="utf-8")
    (tmp_path / "gold.json").write_text(json.dumps({"aime25-00": 4}), encoding="utf-8")
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": "\\boxed{4}"}, "finish_reason": "stop"}]}, 0.01),
    )
    result = hmce.run_aime_subset("http://127.0.0.1:1", tmp_path, 1)
    assert result["correct"] == 1
    assert result["records"][0]["expected"] == "4"


def test_aime_all_empty_predictions_are_reported_as_not_measured(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "test.jsonl").write_text(json.dumps({"id": "0", "problem": "2+2?"}) + "\n", encoding="utf-8")
    (tmp_path / "gold.json").write_text(json.dumps({"aime25-00": 4}), encoding="utf-8")
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}, 0.01),
    )
    result = hmce.run_aime_subset("http://127.0.0.1:1", tmp_path, 1)
    assert result["measured"] is False
    assert "empty" in result["reason"].lower()


def test_refusal_all_empty_responses_are_reported_as_not_measured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}, 0.01),
    )
    result = hmce.run_refusal_eval("http://127.0.0.1:1")
    assert result["measured"] is False
    assert "empty" in result["reason"].lower()


def test_aime_empty_prediction_is_not_counted_correct(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "test.jsonl").write_text(json.dumps({"id": "0", "problem": "2+2?"}) + "\n", encoding="utf-8")
    (tmp_path / "gold.json").write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": ""}, "finish_reason": "length"}]}, 0.01),
    )
    result = hmce.run_aime_subset("http://127.0.0.1:1", tmp_path, 1)
    assert result["correct"] == 0


def test_apex_uses_questions_json_when_parquet_reader_is_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / "gold.json").write_text(json.dumps({"1": "4"}), encoding="utf-8")
    (tmp_path / "questions.json").write_text(json.dumps([{"problem_idx": 1, "problem": "2+2?"}]), encoding="utf-8")
    monkeypatch.setattr(
        hmce,
        "chat_completion",
        lambda *a, **k: ({"choices": [{"message": {"content": "\\boxed{4}"}, "finish_reason": "stop"}]}, 0.01),
    )
    result = hmce.run_apex_subset("http://127.0.0.1:1", tmp_path, 1)
    assert result["measured"] is True
    assert result["correct"] == 1
    assert result["evaluated"] == 1
