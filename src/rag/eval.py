"""Ewaluacja retrievalu (i opcjonalnie generacji) na złotym zbiorze.

Format złotego zbioru (JSONL, jeden obiekt na linię):
    {"id": "q1", "question": "...", "answer": "...", "source_ids": ["plik.md#Sekcja"],
     "tags": ["easy"], "needs_review": false}

`source_ids` to identyfikatory źródeł niezależne od chunkingu (patrz `ingest.source_ids_for`).
Pusta lista oznacza pytanie spoza dokumentów - oczekujemy, że model odmówi odpowiedzi.

Metryki retrievalu (liczone tylko dla pytań z niepustym `source_ids`):
- recall@k: jaka część oczekiwanych źródeł pojawiła się w top-k chunkach,
- MRR (Mean Reciprocal Rank): średnia z 1/pozycja pierwszego trafnego chunka (0, gdy brak).
- ctx_chars: ile znaków kontekstu trafia do modelu (top-k chunków) - przy porównywaniu
  strategii chunkingu recall@k ma sens tylko obok tego budżetu (większe chunki = wyższy recall).

Metryki generacji (`--generate`):
- refusal_ok: zachowanie zgodne z `expected` ("answer": cytuje fragmenty, "refuse": niczego nie
  cytuje, "redirect": wszystkie `expected_urls` są w odpowiedzi),
- url_ok: odsetek pytań, w których wszystkie `expected_urls` występują w tekście odpowiedzi
  (podciąg; liczone tylko dla pytań z `expected_urls`),
- citation_hit: wśród cytowanych chunków jest oczekiwane źródło,
- inline_cited: odpowiedź ma w tekście znaczniki [n] przy twierdzeniach,
- latency_s: czas retrieval + generacja.
"""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from rag.config import Settings
from rag.generate import answer_question
from rag.retrieve import Hit, retrieve


@dataclass
class GoldItem:
    id: str
    question: str
    answer: str
    source_ids: list[str]
    tags: list[str] = field(default_factory=list)
    needs_review: bool = False
    expected: str = "answer"  # "answer" | "refuse" | "redirect"
    expected_urls: list[str] = field(default_factory=list)


def load_golden(path: Path) -> list[GoldItem]:
    """Wczytuje złoty zbiór z pliku JSONL (puste linie są pomijane)."""
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            items.append(GoldItem(**json.loads(line)))
    return items


# --------------------------------------------------------------------------- metryki


def recall_at_k(retrieved: list[list[str]], relevant: list[str], k: int) -> float:
    """Ułamek oczekiwanych źródeł obecnych w top-k (każdy chunk może mieć kilka source_ids)."""
    found = {sid for ids in retrieved[:k] for sid in ids}
    return len(found & set(relevant)) / len(relevant)


def reciprocal_rank(retrieved: list[list[str]], relevant: list[str]) -> float:
    """1 / pozycja pierwszego chunka zawierającego którekolwiek oczekiwane źródło."""
    for rank, ids in enumerate(retrieved, start=1):
        if set(ids) & set(relevant):
            return 1.0 / rank
    return 0.0


def urls_in_answer(answer: str, urls: list[str]) -> bool:
    """Czy KAŻDY oczekiwany adres występuje w tekście odpowiedzi (prosty test na podciąg).

    Nie rozróżniamy wielkości liter ani końcowego ukośnika. Zmyślony adres = brak oczekiwanego.
    """
    text = answer.lower()
    return all(url.lower().rstrip("/") in text for url in urls)


def behavior_ok(item: GoldItem, answered_from_context: bool, url_ok: bool | None) -> bool:
    """Czy zachowanie modelu zgadza się z `item.expected`.

    - "answer": model cytuje fragmenty kontekstu,
    - "refuse": model nic nie cytuje,
    - "redirect": wszystkie `expected_urls` są w odpowiedzi (`url_ok`); gdy pytanie nie ma
      adresów (odesłanie do kontaktu), wystarczy, że model oparł się na kontekście.
    """
    if item.expected == "answer":
        return answered_from_context
    if item.expected == "refuse":
        return not answered_from_context
    if item.expected == "redirect":
        return answered_from_context if url_ok is None else url_ok
    raise ValueError(f"Nieznane expected={item.expected!r} w pytaniu {item.id}. Dozwolone: answer, refuse, redirect.")


# --------------------------------------------------------------------------- przebieg


def evaluate(
    items: list[GoldItem],
    settings: Settings,
    ks: tuple[int, ...] = (1, 3, 5),
    generate: bool = False,
    collection: str | None = None,
) -> dict[str, Any]:
    """Liczy metryki dla całego złotego zbioru. Zwraca słownik z wynikami per pytanie i średnimi."""
    max_k = max(ks)
    rows: list[dict[str, Any]] = []
    for item in items:
        row: dict[str, Any] = {"id": item.id, "question": item.question, "tags": item.tags, "expected": item.expected}
        hits: list[Hit] = retrieve(item.question, settings, k=max_k, collection=collection)
        if generate:
            result = answer_question(item.question, settings, k=settings.top_k, collection=collection)
            cited = {sid for h in result.cited_hits() for sid in h.source_ids}
            url_ok = urls_in_answer(result.answer.answer, item.expected_urls) if item.expected_urls else None
            row |= {
                "answer": result.answer.answer,
                "citations": result.cited_numbers,
                "latency_s": result.retrieve_s + result.generate_s,
                "structured_mode": result.mode,
                # Zachowanie zgodne z `expected` (answer / refuse / redirect), nie z pustym source_ids.
                "refusal_ok": behavior_ok(item, result.answered_from_context, url_ok),
                # Tylko pytania z expected_urls: czy wszystkie adresy są w tekście odpowiedzi.
                "url_ok": url_ok,
                "citation_hit": bool(cited & set(item.source_ids)) if item.source_ids else None,
                # Czy odpowiedź ma znaczniki [n] w tekście (tylko dla pytań z odpowiedzią).
                "inline_cited": result.has_inline_citations if item.source_ids else None,
            }
        row["ctx_chars"] = sum(len(h.text) for h in hits[: settings.top_k])
        if item.source_ids:
            retrieved = [h.source_ids for h in hits]
            for k in ks:
                row[f"recall@{k}"] = recall_at_k(retrieved, item.source_ids, k)
            row["mrr"] = reciprocal_rank(retrieved, item.source_ids)
        rows.append(row)
    return {"rows": rows, "summary": summarize(rows, ks), "by_expected": summarize_by_expected(rows, ks)}


def _mean(rows: list[dict[str, Any]], key: str) -> float | None:
    values = [float(r[key]) for r in rows if r.get(key) is not None]
    return round(statistics.mean(values), 3) if values else None


def summarize(rows: list[dict[str, Any]], ks: tuple[int, ...]) -> dict[str, Any]:
    """Średnie metryk po wszystkich pytaniach."""
    summary: dict[str, Any] = {"questions": len(rows)}
    keys = ["mrr", "ctx_chars", "refusal_ok", "url_ok", "citation_hit", "inline_cited", "latency_s"]
    for key in [*(f"recall@{k}" for k in ks), *keys]:
        summary[key] = _mean(rows, key)
    return summary


def summarize_by_expected(rows: list[dict[str, Any]], ks: tuple[int, ...]) -> dict[str, dict[str, Any]]:
    """Osobne średnie dla każdej wartości `expected` (answer / redirect / refuse).

    Bez tego np. 15 odesłań i 95 zwykłych pytań zlałoby się w jedną liczbę `refusal_ok`,
    choć każda grupa mierzy co innego.
    """
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(row.get("expected", "answer"), []).append(row)
    return {name: summarize(group, ks) for name, group in sorted(groups.items())}


def to_markdown(results: dict[str, Any], title: str) -> str:
    """Tabela wyników w Markdownie (do wklejenia w raport / slajdy)."""
    rows, summary = results["rows"], results["summary"]
    cols = [c for c in summary if c != "questions" and summary[c] is not None]
    lines = [f"# {title}", "", "| id | pytanie | " + " | ".join(cols) + " |"]
    lines.append("|" + "---|" * (len(cols) + 2))
    for r in rows:
        values = " | ".join(format_cell(r.get(c)) for c in cols)
        lines.append(f"| {r['id']} | {r['question']} | {values} |")
    means = " | ".join(f"**{format_cell(summary[c])}**" for c in cols)
    lines.append(f"| **średnia** | {summary['questions']} pytań | {means} |")
    groups = results.get("by_expected", {})
    if len(groups) > 1:  # osobna średnia dla każdego expected, tylko gdy w zbiorze jest ich kilka
        for name, group in groups.items():
            values = " | ".join(f"**{format_cell(group[c])}**" for c in cols)
            lines.append(f"| **średnia: {name}** | {group['questions']} pytań | {values} |")
    return "\n".join(lines) + "\n"


def format_cell(value: Any) -> str:
    """Wartość metryki jako krótki tekst (tabela w terminalu i w Markdownie)."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "✓" if value else "✗"
    if isinstance(value, float):
        return f"{value:.0f}" if value >= 100 else f"{value:.2f}"
    return str(value)


def save_results(results: dict[str, Any], settings: Settings, out_dir: Path, label: str) -> Path:
    """Zapisuje wyniki do `eval/results/<timestamp>_<label>.json` (+ `.md`) i zwraca ścieżkę."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = out_dir / f"{stamp}_{label}.json"
    config = asdict(settings) | {"llm_api_key": "***", "embed_api_key": "***"}
    path.write_text(json.dumps({"config": config, **results}, ensure_ascii=False, indent=2), encoding="utf-8")
    title = f"{label} · {settings.llm_model} · {stamp}"
    path.with_suffix(".md").write_text(to_markdown(results, title), encoding="utf-8")
    return path
