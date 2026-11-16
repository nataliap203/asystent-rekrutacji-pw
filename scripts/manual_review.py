"""Ręczna ocena odpowiedzi z `make eval ARGS=--generate`.

Dwa kroki:

1. Eksport do CSV:

       uv run python scripts/manual_review.py export eval/results/<plik>.json

   Tworzy `eval/results/<plik>_ocena.csv` z kolumnami: pytanie, oczekiwana odpowiedź, odpowiedź
   modelu, metryki automatyczne oraz pustymi kolumnami `ocena` i `komentarz` do wypełnienia.
   Istniejącego pliku nie nadpisuje (żeby nie skasować ocen) - chyba że użyte jest --force.

2. Podsumowanie po wypełnieniu kolumny `ocena`:

       uv run python scripts/manual_review.py summary eval/results/<plik>_ocena.csv

   Wypisuje tabelę w Markdownie (do wklejenia w dokumentację) i zapisuje ją obok CSV (`.md`).

Dozwolone wartości `ocena` (reguły w docs/ocena_reczna.md):
    poprawna         - odpowiedź merytorycznie zgodna z oczekiwaną (expected = answer)
    poprawna_odmowa  - poprawna odmowa / odesłanie (expected = refuse / redirect)
    zbedna_odmowa    - model odmówił, choć odpowiedź była w dokumentach (expected = answer)
    bledna           - odpowiedź błędna, niepełna, zmyślona albo odpowiedź tam, gdzie należało odmówić
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

LABELS = ("poprawna", "poprawna_odmowa", "zbedna_odmowa", "bledna")
# Które oceny liczymy jako sukces dla danego `expected`.
SUCCESS = {"answer": {"poprawna"}, "refuse": {"poprawna_odmowa"}, "redirect": {"poprawna_odmowa"}}
CATEGORY_PREFIX = {"s": "easy", "c": "calc", "x": "complex", "a": "ambiguous", "o": "out_of_scope"}

COLUMNS = [
    "id", "kategoria", "expected", "pytanie", "oczekiwana_odpowiedz", "odpowiedz_modelu",
    "expected_urls", "refusal_ok", "url_ok", "citation_hit", "recall@5", "ocena", "komentarz",
]


def load_golden(path: Path) -> dict[str, dict]:
    items = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            items[item["id"]] = item
    return items


def category(item_id: str, tags: list[str]) -> str:
    """Kategoria pytania: z tagu, a gdy go brak - z prefiksu id (s/c/x/a/o)."""
    for tag in tags:
        if tag in CATEGORY_PREFIX.values():
            return tag
    return CATEGORY_PREFIX.get(item_id.rstrip("0123456789")[:1], "inne")


def fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def cmd_export(args: argparse.Namespace) -> None:
    results_path = Path(args.results)
    out = results_path.with_name(results_path.stem + "_ocena.csv")
    if out.exists() and not args.force:
        sys.exit(f"{out} już istnieje - nie nadpisuję (mogą tam być oceny). Użyj --force.")
    results = json.loads(results_path.read_text(encoding="utf-8"))
    golden = load_golden(Path(args.golden))
    rows = results["rows"]
    if "answer" not in rows[0]:
        sys.exit("W wynikach nie ma odpowiedzi modelu - uruchom ewaluację z --generate.")
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            gold = golden.get(row["id"], {})
            writer.writerow({
                "id": row["id"],
                "kategoria": category(row["id"], row.get("tags", [])),
                "expected": row.get("expected", "answer"),
                "pytanie": row["question"],
                "oczekiwana_odpowiedz": gold.get("answer", ""),
                "odpowiedz_modelu": row["answer"],
                "expected_urls": " ".join(gold.get("expected_urls", [])),
                "refusal_ok": fmt(row.get("refusal_ok")),
                "url_ok": fmt(row.get("url_ok")),
                "citation_hit": fmt(row.get("citation_hit")),
                "recall@5": fmt(row.get("recall@5")),
                "ocena": "",
                "komentarz": "",
            })
    print(f"Zapisano {out} ({len(rows)} pytań). Wypełnij kolumny `ocena` i `komentarz`.")


def read_reviews(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")  # arkusze zapisują czasem `;`
    rows = list(csv.DictReader(text.splitlines(), dialect=dialect))
    errors = []
    for r in rows:
        r["ocena"] = (r.get("ocena") or "").strip().lower().replace("ę", "e").replace(" ", "_")
        if r["ocena"] and r["ocena"] not in LABELS:
            errors.append(f"{r['id']}: nieznana ocena „{r['ocena']}” (dozwolone: {', '.join(LABELS)})")
    if errors:
        sys.exit("\n".join(errors))
    return rows


def table(groups: dict[str, list[dict]], title: str) -> list[str]:
    lines = [f"| {title} | pytań | ocenione | " + " | ".join(LABELS) + " | trafność |",
             "|---|---|---|" + "---|" * len(LABELS) + "---|"]
    for name, rows in groups.items():
        graded = [r for r in rows if r["ocena"]]
        counts = Counter(r["ocena"] for r in graded)
        ok = sum(1 for r in graded if r["ocena"] in SUCCESS[r["expected"]])
        acc = f"{ok / len(graded):.2f}" if graded else "-"
        lines.append(f"| {name} | {len(rows)} | {len(graded)} | "
                     + " | ".join(str(counts[label]) for label in LABELS) + f" | **{acc}** |")
    return lines


def cmd_summary(args: argparse.Namespace) -> None:
    path = Path(args.reviews)
    rows = read_reviews(path)
    by_expected: dict[str, list[dict]] = defaultdict(list)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_expected[r["expected"]].append(r)
        by_category[r["kategoria"]].append(r)
    lines = [f"## Ocena ręczna · {path.name}", "",
             "Trafność = poprawna (answer) lub poprawna_odmowa (refuse/redirect) / ocenione.", ""]
    lines += table({"wszystkie": rows, **dict(sorted(by_expected.items()))}, "expected") + [""]
    lines += table(dict(sorted(by_category.items())), "kategoria") + [""]
    # Zgodność automatycznej metryki z oceną ręczną - pokazuje, ile warte jest refusal_ok.
    mismatch = [r["id"] for r in rows if r["ocena"] and r["refusal_ok"] == "1"
                and r["ocena"] not in SUCCESS[r["expected"]]]
    lines.append(f"`refusal_ok` = ✓, a ocena ręczna = porażka: {len(mismatch)} pytań"
                 + (f" ({', '.join(mismatch)})" if mismatch else ""))
    missing = [r["id"] for r in rows if not r["ocena"]]
    if missing:
        lines.append(f"\nBez oceny: {len(missing)} ({', '.join(missing)})")
    report = "\n".join(lines) + "\n"
    print(report)
    path.with_suffix(".md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser("export", help="wyniki JSON → CSV do ręcznej oceny")
    p.add_argument("results")
    p.add_argument("--golden", default="eval/golden.jsonl")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_export)
    p = sub.add_parser("summary", help="podsumowanie wypełnionego CSV")
    p.add_argument("reviews")
    p.set_defaults(func=cmd_summary)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()