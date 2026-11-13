import pytest

from rag.eval import (
    GoldItem,
    behavior_ok,
    recall_at_k,
    reciprocal_rank,
    summarize_by_expected,
    to_markdown,
    urls_in_answer,
)


def test_recall_at_k():
    retrieved = [["a"], ["b", "c"], ["d"]]
    assert recall_at_k(retrieved, ["a", "d"], k=1) == 0.5
    assert recall_at_k(retrieved, ["a", "d"], k=3) == 1.0
    assert recall_at_k(retrieved, ["c"], k=2) == 1.0


def test_reciprocal_rank():
    retrieved = [["x"], ["y"], ["a"]]
    assert reciprocal_rank(retrieved, ["a"]) == pytest.approx(1 / 3)
    assert reciprocal_rank(retrieved, ["zzz"]) == 0.0
    assert reciprocal_rank(retrieved, ["y", "a"]) == 0.5


def test_urls_in_answer():
    urls = ["https://akademiki.pw.edu.pl/", "https://www.bss.pw.edu.pl/Stypendia"]
    assert urls_in_answer("Zobacz https://akademiki.pw.edu.pl oraz https://www.BSS.pw.edu.pl/Stypendia.", urls)
    assert not urls_in_answer("Zobacz https://akademiki.pw.edu.pl/ (drugi adres zmyślony: https://bss.pw.pl)", urls)
    assert urls_in_answer("cokolwiek", [])


@pytest.mark.parametrize(
    "expected, answered, url_ok, ok",
    [
        ("answer", True, None, True),
        ("answer", False, None, False),
        ("refuse", False, None, True),
        ("refuse", True, None, False),
        ("redirect", True, True, True),
        ("redirect", True, False, False),  # cytuje, ale bez adresu
        ("redirect", False, True, True),  # liczy się adres w tekście
        ("redirect", True, None, True),  # bez expected_urls: wystarczy oparcie na kontekście
        ("redirect", False, None, False),
    ],
)
def test_behavior_ok(expected, answered, url_ok, ok):
    item = GoldItem("q", "?", "!", [], expected=expected)
    assert behavior_ok(item, answered, url_ok) is ok


def test_behavior_ok_rejects_unknown_expected():
    with pytest.raises(ValueError, match="Nieznane expected"):
        behavior_ok(GoldItem("q", "?", "!", [], expected="refus"), True, None)


def _rows():
    return [
        {"id": "a1", "expected": "answer", "refusal_ok": True, "mrr": 1.0},
        {"id": "a2", "expected": "answer", "refusal_ok": False, "mrr": 0.5},
        {"id": "r1", "expected": "redirect", "refusal_ok": True, "url_ok": True, "mrr": 1.0},
        {"id": "r2", "expected": "redirect", "refusal_ok": False, "url_ok": False, "mrr": 0.0},
        {"id": "f1", "expected": "refuse", "refusal_ok": True},
    ]


def test_summarize_by_expected_keeps_groups_apart():
    groups = summarize_by_expected(_rows(), ks=(1,))
    assert list(groups) == ["answer", "redirect", "refuse"]
    assert groups["answer"]["questions"] == 2 and groups["answer"]["refusal_ok"] == 0.5
    assert groups["redirect"]["url_ok"] == 0.5
    assert groups["refuse"]["refusal_ok"] == 1.0
    assert groups["refuse"]["mrr"] is None  # refuse nie ma retrievalu
    assert groups["answer"]["url_ok"] is None  # brak expected_urls


def test_row_without_expected_counts_as_answer():
    groups = summarize_by_expected([{"id": "x", "refusal_ok": True}], ks=(1,))
    assert list(groups) == ["answer"]


def test_markdown_has_group_rows_only_with_several_groups():
    rows = [{**r, "question": "?"} for r in _rows()]
    summary = {"questions": 5, "refusal_ok": 0.6, "url_ok": 0.5}
    many = to_markdown({"rows": rows, "summary": summary, "by_expected": summarize_by_expected(rows, (1,))}, "t")
    assert "średnia: answer" in many and "średnia: redirect" in many and "średnia: refuse" in many
    one = to_markdown({"rows": rows[:2], "summary": summary, "by_expected": summarize_by_expected(rows[:2], (1,))}, "t")
    assert "średnia:" not in one
