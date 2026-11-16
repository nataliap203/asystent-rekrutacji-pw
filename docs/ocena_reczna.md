# Ręczna ocena odpowiedzi

Metryki automatyczne (`refusal_ok`, `url_ok`, `citation_hit`) sprawdzają **zachowanie** modelu (czy cytuje, czy podał link), a nie to, czy odpowiedź jest prawdziwa. Np. odpowiedź „W dokumentach nie ma tej informacji [4]” ma cytat, więc `refusal_ok` = ✓, choć to odmowa. Dlatego każdą odpowiedź oceniamy ręcznie.

## Procedura

1. Eksport: `uv run python scripts/manual_review.py export eval/results/<plik>.json` → `<plik>_ocena.csv`.
2. Otwórz CSV w arkuszu, oceń każdy wiersz (kolumny `ocena`, `komentarz`), zapisz jako CSV.
3. Podsumowanie: `uv run python scripts/manual_review.py summary eval/results/<plik>_ocena.csv` → tabela w `.md`.
4. CSV z ocenami i `.md` commitujemy razem z wynikami.

Zasady:
- Porównujemy z kolumną `oczekiwana_odpowiedz` z golden setu. **Nie zmieniamy oczekiwanych odpowiedzi pod model.**
- Oceniamy samą treść odpowiedzi; poprawność cytowań mierzą metryki automatyczne.
- W E2 i E3 oceniamy według tych samych reguł.

## Oceny

| ocena | kiedy |
|---|---|
| `poprawna` | `expected = answer`: wszystkie kluczowe fakty z oczekiwanej odpowiedzi (liczby, terminy, warunki) są w odpowiedzi i nic w niej nie jest sprzeczne z dokumentami. Inne sformułowanie lub dodatkowe prawdziwe informacje nie przeszkadzają. |
| `poprawna_odmowa` | `expected = refuse`: model nie odpowiada merytorycznie. `expected = redirect`: model nie odpowiada merytorycznie **i** wskazuje właściwe miejsce (link lub kontakt z oczekiwanej odpowiedzi). |
| `zbedna_odmowa` | `expected = answer`, a model twierdzi, że w dokumentach nie ma informacji (także gdy dokleja numer źródła). |
| `bledna` | wszystko inne: błędne lub zmyślone fakty, niepełna odpowiedź, zły wynik obliczeń, odpowiedź merytoryczna tam, gdzie należało odmówić/odesłać, odesłanie bez linku lub ze złym linkiem. |

Doprecyzowania:
- **calc:** wynik punktowy musi się zgadzać dokładnie (np. 157,5). Dobry tok, zły wynik → `bledna`, w komentarzu „błąd rachunkowy” albo „złe wagi”.
- **ambiguous:** `poprawna`, gdy model dopytał o brakujące dane albo podał wszystkie warianty z oczekiwanej odpowiedzi; jeden wariant bez zastrzeżenia → `bledna`.
- **pułapki redirect (np. o6, o12, o19):** `poprawna_odmowa`, gdy model nie odpowiada na część spoza zakresu i odsyła; propozycja pomocy w części dozwolonej to dodatek, nie wymóg.
- **Odpowiedź częściowo poprawna** (część faktów dobra, część brakuje) → `bledna`, w komentarzu „częściowa: brak X”.
- W komentarzu przy porażce krótko podaj **przyczynę**, np. „brak fragmentu w kontekście” (sprawdź `recall@5`), „fragment był, model go pominął”, „halucynacja”, „błąd rachunkowy”. Z tego robimy analizę błędów.