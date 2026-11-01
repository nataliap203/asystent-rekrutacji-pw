# Dokumentacja Projektowa: Asystent Rekrutacyjny Politechniki Warszawskiej (2026/2027)
## 1. Cel projektu
Celem projektu jest stworzenie zaawansowanego systemu opartego na architekturze RAG i agentach LLM, który pełni rolę wirtualnego asystenta dla kandydatów na Politechnikę Warszawską na rok akademicki 2026/2027.

System ma za zadanie:
1. Precyzyjnie odpowiadać na pytania informacyjne dotyczące harmonogramów, wymaganych dokumentów i procedur dla studiów I i II stopnia, a także (w mniejszym, ogólnym zakresie) studiów doktorskich, podyplomowych i kursów.
2. Działać jako inteligentny kalkulator w etapie agentowym (E3) - wyliczać wskaźnik rekrutacyjny z matur dla studiów I stopnia i jednolitych magisterskich na podstawie wag przedmiotowych oraz porównywać go z historycznymi progami punktowymi.
3. Precyzyjnie identyfikować zapytania wykraczające poza zakres (m.in. dotyczące Wydziału Architektury) i bezpiecznie odmawiać odpowiedzi, kierując użytkownika do właściwych źródeł, zapobiegając w ten sposób halucynacjom.
---
## 2. Zakres Danych (Baza Wiedzy)
*Uwaga techniczna: Wszystkie dane opierają się na oficjalnych regulaminach PW na rok 2026/2027. Treści ze stron internetowych zostaną przetworzone do statycznych plików `.md` i `.csv`, aby zapewnić niezmienność środowiska dla stałego zestawu testowego (Golden Set).*
### 2.1. Dane włączone do projektu (In-scope)

**Algorytmika i progi punktowe (Tylko I stopień i jednolite magisterskie):**
* `Przedmioty i współczynniki wagowe 2026_2027.pdf`(wagi dla studiów stacjonarnych i niestacjonarnych).
* `Zasady ustalania punktów kwalifikacyjnych 2026_2027.pdf`
* `Progi_punktowe_PW_2025_2026.csv` - plik utworzony ręcznie na podstawie oficjalnych komunikatów rekrutacyjnych PW z poprzedniego roku (dostępne dla studiów stacjonarnych I stopnia i jednolitych magisterskijch).

**Studia stacjonarne I stopnia i jednolite magisterskie:**
- `Studia stacjonarne I stopnia oraz jednolite studia magisterskie 2026_2027.pdf`
- Zrzut informacyjny `.md` z zakładki: https://www.pw.edu.pl/studia-i-stopnia/zasady-przyjec-na-studia-stacjonarne-i-stopnia
- **Wyniki rekrutacji (progi punktowe):**
	- `Progi_punktowe_PW_2025_2026.csv` - plik utworzony na podstawie oficjalnych komunikatów Międzywydziałowej Komisji Rekrutacyjnej PW (uwzględniający ostateczne wyniki po wszystkich turach ze strony https://www.pw.edu.pl/taxonomy/term/705).
	- Źródła, rekrutacja 25/26
		- https://www.pw.edu.pl/aktualnosci/komunikat-miedzywydzialowej-komisji-rekrutacyjnej-z-dnia-29082025-r
		- https://www.pw.edu.pl/aktualnosci/komunikat-miedzywydzialowej-komisji-rekrutacyjnej-z-25072025-r
		- https://www.pw.edu.pl/aktualnosci/komunikat-miedzywydzialowej-komisji-rekrutacyjnej-z-18072025-r

**Studia niestacjonarne I stopnia:**
- `Studia niestacjonarne I stopnia 2026_2027.pdf`
- Zrzut informacyjny `.md` z zakładki: https://www.pw.edu.pl/studia-i-stopnia/zasady-przyjec-na-studia-niestacjonarne-i-stopnia

**Studia stacjonarne II stopnia:**
- `Studia stacjonarne II stopnia 2026_2027.pdf`
- Zrzut informacyjny `.md` z zakładki: https://www.pw.edu.pl/studia-ii-stopnia/zasady-przyjec-na-studia-stacjonarne-ii-stopnia

**Studia niestacjonarne II stopnia:**
- `Studia niestacjonarne II stopnia 2026_2027.pdf`
- Zrzut informacyjny `.md` z zakładki: https://www.pw.edu.pl/studia-ii-stopnia/zasady-przyjec-na-studia-niestacjonarne-ii-stopnia

**Studia doktorskie:**
- Zrzut informacyjny `.md` z zakładki: https://www.pw.edu.pl/doktorat/zasady-przyjec-na-doktorat

**Studia podyplomowe:**
- Zrzut informacyjny `.md` z zakładki: https://www.pw.edu.pl/studia-podyplomowe/zasady-przyjec-na-studia-podyplomowe

**Kursy:**
- Zrzut informacyjny `.md` z zakładki dotyczący Kursów: https://www.pw.edu.pl/studia/zasady-rekrutacji

**Dokumenty uzupełniające:**
- `Certyfikaty potwierdzające znajomość języka angielskiego 2026_2027.pdf`
- `Kierunki studiowania oraz uznawane dyplomy potwierdzające uzyskanie kwalifikacji zawodowych na poziomie technika 2026_2027.pdf`
- `Uprawnienia uczestników olimpiad, konkursów i turniejów 2026_2027.pdf`

**Załączniki i wzory oświadczeń:**
* `Upoważnienie 2026_2027.pdf` (dla różnych stopni połączone w jeden kontekst).
* `Zgoda rodziców na podjęcie studiów przez osobę niepełnoletnią. Rekrutacja PW 2026_2027.pdf` - dotyczy studiów I stopnia (stacjonarnych i niestacjonarnych).
### 2.2. Dane wyłączone z projektu (Out-of-scope)
System ma za zadanie zidentyfikować poniższe intencje, przerwać proces wnioskowania (odmówić własnej odpowiedzi) i skierować użytkownika do odpowiedniego miejsca:
* **Rekrutacja na Wydział Architektury PW** - proces oparty na specjalistycznych sprawdzianach uzdolnień plastycznych; system odeśle kandydata na stronę: https://www.arch.pw.edu.pl/Kandydaci.
* **Regulamin Studiów Politechniki Warszawskiej** - dotyczy organizacji toku nauczania osób już przyjętych, a nie procesu rekrutacji; system odeśle kandydata na stronę: https://www.bip.pw.edu.pl/Sprawy-Studenckie/Regulamin-studiow-w-Politechnice-Warszawskiej2.
* **Kwestie socjalno-bytowe** - wnioskowanie o domy studenckie (akademiki), stypendia rekrutacyjne i socjalne; system odeśle kandydata odpowiednio na strony: https://www.bss.pw.edu.pl/Stypendia oraz https://akademiki.pw.edu.pl/.
* **Inne uczelnie wyższe** - brak wsparcia dla wyliczania progów na inne uniwersytety.
* **Sprawy obecnych studentów**  inne informacje dotyczące studiów, rejestracji na przedmioty itp.
---
## 3. Zakres Funkcjonalności i Kategorie Zapytań
### 3.1. Obsługiwane kategorie zapytań
1. **Pytania informacyjne (Q&A):** Odpowiadanie na pytania o harmonogramy, wymagane dokumenty, certyfikaty językowe i procedury kwalifikacyjne (w tym procedury zróżnicowane dla II stopnia).
2. **Kalkulator Rekrutacyjny I Stopnia (Logic/Math):** Wyliczanie przez agenta punktów z matur/dyplomów technika dla studiów stacjonarnych i niestacjonarnych I stopnia i zestawianie ich z historycznym progiem punktowym.
3. **Poprawna Odmowa (Refusal):** Rozpoznanie intencji wykraczającej poza zakres (np. "Ile punktów za rysunek na architekturę?") i wygenerowanie precyzyjnej odmowy z linkiem.

### 3.2. Różnice w logice dla stopni studiów
* **I stopień:** Model wykorzystuje twardy algorytm (narzędzie agentowe w Pythonie) do obliczania punktów (PK) z wyników matur.
* **II stopień:** Model odpowiada wyłącznie opisowo na podstawie RAG, tłumacząc proces rekrutacji (np. wymóg posiadania dyplomu inżyniera, minimalne oceny do preferencji, rozmowy kwalifikacyjne).
### 3.3. Funkcjonalności poza zakresem
- Doradztwo zawodowe (ocena, czy warto studiować dany kierunek lub przewidywanie trudności studiów).
* Pomoc w przygotowaniu portfolio lub zadania graficznego na kierunki Architektura i Architecture.
* Rozwiązywanie problemów technicznych z kontem w systemie IRK.
---
## 4. Ewaluacja i Zestaw Testowy (Golden Set)
System zostanie oceniony na podstawie rygorystycznego pomiaru **przed/po** (E1 vs E2 vs E3) na tym samym, zamrożonym zestawie zapytań (temperatura = 0).
* **Wielkość zbioru:** Minimum 100 zapytań przygotowanych *przed* etapami ulepszania.
* **Struktura testów (wejście -> oczekiwany wynik):**
	* *Pytania łatwe (Q&A):* Np. "Jakie certyfikaty zwalniają z angielskiego na II stopniu?"
	* *Pytania obliczeniowe (I stopień):* Np. "Mam 80% z rozszerzonej matematyki i 60% z fizyki. Ile będę mieć punktów na Informatykę Stosowaną"
	* *Pytania złożone:* Wymagające łączenia wiedzy z różnych dokumentów. Np. "Mam 80% z rozszerzonej matematyki i 60% z fizyki. Czy mam szansę na stacjonarną Informatykę Stosowaną?"
	* *Pytania spoza zakresu (Guardrails):* Np. "Jak wygląda sprawdzian predyspozycji na Architekturę?" (Oczekiwany wynik: Odmowa i link).
---
## 5. Harmonogram
#### Etap E1: System bazowy (Termin: 16 XI 2026)
* Stworzenie Zestawu Testowego (>100 pytań).
* Uruchomienie bazowego potoku RAG end-to-end na zebranych plikach.
* Pierwszy pomiar bazowy na przygotowanych przykładach (udokumentowanie m.in. halucynacji w obliczeniach matematycznych).
#### Etap E2: Zaawansowany RAG (Termin: 7 XII 2026)
* Wdrożenie ulepszeń bazy wiedzy (np. dodanie metadanych rozróżniających pliki I i II stopnia).
* Weryfikacja promptu systemowego (odrzucanie Architektury i zapytań out-of-scope).
* Drugi pomiar ewaluacyjny i wykazanie różnic przed/po.
#### Etap E3: Agent i Narzędzia / Tool Calling (Termin: 21 XII 2026)
* Wdrożenie Agenta wywołującego narzędzie (np. `kalkulator_wskaznika_rekrutacyjnego()`).
* Ostateczny pomiar ewaluacyjny wykazujący eliminację błędów matematycznych w stosunku do E1 i E2 na tym samym zestawie.
#### Demo Day (Termin: 11 I 2027)
-   Trzyminutowa prezentacja działającego systemu (showcase poprawnych obliczeń i poprawnej odmowy dla Architektury).
---