# Etap E1 - system bazowy

Termin: 16 XI 2026. Pomiar bazowy, z którym porównamy E2 (zaawansowany RAG) i E3 (agent z kalkulatorem).

## Co zrobiono

- Golden set: 120 pytań w `eval/golden.jsonl` (30 easy, 20 calc, 30 complex, 20 ambiguous, 20 out_of_scope).
- Bazowy potok RAG end-to-end na zebranych dokumentach, bez żadnych ulepszeń.
- Ewaluacja z `--generate` i ręczna ocena wszystkich odpowiedzi zgodnie z [ocena_reczna.md](ocena_reczna.md).

## Konfiguracja

| ustawienie | wartość |
|---|---|
| LLM | `qwen3.5:9b` (Ollama), temperatura 0, thinking wyłączony |
| embeddingi | `qwen3-embedding:0.6b` |
| chunking | `recursive`, 800 znaków, overlap 120 |
| retrieval | dense, `top_k = 5` |
| wyniki | `eval/results/20261116-144054_golden_docs_qwen3.5-9b.*` |

## Wyniki

Metryki automatyczne (cały zbiór): recall@5 = 0,30, MRR = 0,26, `refusal_ok` = 0,59, `url_ok` = 0,08, `citation_hit` = 0,28, średni czas odpowiedzi ok. 43 s.

Ocena ręczna (trafność = poprawna lub poprawna odmowa / wszystkie):

| kategoria | pytań | poprawna | poprawna_odmowa | zbedna_odmowa | bledna | trafność |
|---|---|---|---|---|---|---|
| easy | 30 | 11 | 0 | 9 | 10 | 0,37 |
| calc | 20 | 0 | 0 | 20 | 0 | 0,00 |
| complex | 30 | 0 | 0 | 20 | 10 | 0,00 |
| ambiguous | 20 | 1 | 0 | 12 | 7 | 0,05 |
| out_of_scope | 20 | 0 | 7 | 0 | 13 | 0,35 |
| **razem** | **120** | **12** | **7** | **61** | **40** | **0,16** |

Pełna tabela i lista pytań: [wyniki oceny ręcznej](../eval/results/20261116-144054_golden_docs_qwen3.5-9b_ocena.md), oceny i komentarze per pytanie w pliku `..._ocena.csv`.

## Wnioski

1. **Główny problem to retrieval, nie generowanie.** recall@5 wynosi tylko 0,30, więc w większości przypadków właściwego fragmentu nie ma w kontekście. Model wtedy odpowiada „w dokumentach nie ma informacji” (61 zbędnych odmów na 100 pytań `answer`).
2. **Pytania obliczeniowe: 0/20, ale nie przez halucynacje.** Model nie podaje błędnych wyników, tylko we wszystkich 20 przypadkach odmawia. Wzory i wagi są trudne do znalezienia w chunkach. Wniosek do E3: kalkulator musi mieć wagi i wzory poza retrievalem, a nie tylko w narzędziu.
3. **Metryka `refusal_ok` zawyża jakość.** W 53 pytaniach `refusal_ok` = ✓, a ocena ręczna to porażka, bo odmowa z doklejonym numerem źródła liczy się jako cytowanie.
4. **Pytania spoza zakresu:** 5 z 5 pytań `refuse` poprawnie, ale tylko 2 z 15 `redirect`. Model zwykle nie podaje linku ani kontaktu z `Kontakty_i_odeslania.md` (`url_ok` = 0,08). To cel dla E2 (prompt i metadane).
5. **Błędne odpowiedzi merytoryczne** (np. pomylone terminy zapisów w s8, s9, a20 albo nieaktualny wzór PK w s3) wynikają głównie z mieszania fragmentów z różnych stopni i form studiów. To cel dla E2 (metadane rozróżniające stopień i formę).
6. W pytaniach `ambiguous` model prawie nigdy nie dopytuje - odmawia albo podaje jeden wariant bez zastrzeżenia.

## Punkt odniesienia dla E2 i E3

E2 i E3 uruchamiamy na tym samym golden secie i tych samych regułach oceny. Cel: wzrost trafności przede wszystkim w `calc`, `complex` i `redirect`.
