# Dokumentacja Projektowa: Asystent Rekrutacyjny Politechniki Warszawskiej (2026/2027)

## 1. Cel projektu
Celem projektu jest stworzenie zaawansowanego systemu opartego na architekturze RAG i agentach LLM, który pełni rolę wirtualnego asystenta dla kandydatów na Politechnikę Warszawską na rok akademicki 2026/2027.

System ma za zadanie:
1. Precyzyjnie odpowiadać na pytania informacyjne dotyczące harmonogramów, wymaganych dokumentów i procedur dla studiów I i II stopnia, a także (w mniejszym, ogólnym zakresie) studiów doktorskich, podyplomowych i kursów.
2. Działać jako inteligentny kalkulator w etapie agentowym (E3) - wyliczać wskaźnik rekrutacyjny z matur dla studiów I stopnia i jednolitych magisterskich na podstawie wag przedmiotowych oraz porównywać go z historycznymi progami punktowymi.
3. Precyzyjnie identyfikować zapytania wykraczające poza zakres (m.in. dotyczące Wydziału Architektury) i bezpiecznie odmawiać odpowiedzi, kierując użytkownika do właściwych źródeł, zapobiegając w ten sposób halucynacjom.

## Ręczna ocena odpowiedzi

Metryki automatyczne (`refusal_ok`, `url_ok`, `citation_hit`) sprawdzają zachowanie modelu, a nie prawdziwość odpowiedzi, dlatego odpowiedzi z `make eval ARGS=--generate` oceniamy także ręcznie.

- [docs/ocena_reczna.md](docs/ocena_reczna.md) - procedura oceny, dozwolone oceny (`poprawna`, `poprawna_odmowa`, `zbedna_odmowa`, `bledna`) i reguły dla poszczególnych kategorii pytań.
- [scripts/manual_review.py](scripts/manual_review.py) - skrypt z dwoma poleceniami:
  - `uv run python scripts/manual_review.py export eval/results/<plik>.json` tworzy `<plik>_ocena.csv` z pustymi kolumnami `ocena` i `komentarz` (istniejącego pliku nie nadpisuje bez `--force`),
  - `uv run python scripts/manual_review.py summary eval/results/<plik>_ocena.csv` wypisuje tabelę podsumowującą (po `expected` i kategorii) i zapisuje ją obok CSV jako `.md`.
- [docs/etap_E1.md](docs/etap_E1.md) - opis etapu E1 z wynikami pomiaru bazowego.