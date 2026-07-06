# URI-proces: reverse ORAZ validate-if-done (luka autonomii)

> Notatka problemowa z sesji nad panelem `/work`. Opisuje klasę problemu, na który
> natrafiliśmy budując autonomiczną pętlę, i asymetrię w standardzie URI-procesu.

## Teza (potwierdzona empirycznie)

Każdy URI-proces mutujący powinien nieść **dwie** symetryczne cechy:

1. **`inverse` — jak to ODWRÓCIĆ** (reversibility). *Jest* w standardzie.
2. **`verify` / `postcondition` — jak SPRAWDZIĆ, że NAPRAWDĘ się wykonało** (done-validation). *Brak.*

Dowód z `urirun/docs/URI_COMMAND_STANDARD.md`:

| pojęcie | wystąpień w standardzie |
|---|---|
| `inverse` / `reverse` | **2** (`command … SHOULD return an inverse`; checklist: „a reversible command returns an inverse") |
| `postcondition` / `verify` / `validate` / `acceptance` / done-check | **0** |

Standard mówi, jak **cofnąć** akcję, ale **nie** mówi, jak **potwierdzić, że osiągnęła cel**.

## Dlaczego to zabija autonomię

> „Jeśli nie da się zwalidować, czy zadanie zostało wykonane, to nie ma sensu go robić."

Autonomiczna pętla to `OBSERWUJ → ZDECYDUJ → DZIAŁAJ → ZWERYFIKUJ → …`. Bez ostatniego
ogniwa (`ZWERYFIKUJ`) pętla nie może:
- odróżnić **wykonane** od **udawane** (pseudo-praca),
- domknąć ticketu (kiedy `done`?),
- zdecydować o następnym kroku (retry vs dalej vs eskaluj).

Efekt zaobserwowany na żywo: koru pętlił `IFURI-033` — status `in_progress`, ale **0 realnej
pracy** (checkpoint pusty, `git status` czysty). „Reverse" tu nie pomaga; brakuje **oracle
„czy zrobione"**.

## To jest JEDNA luka na DWÓCH poziomach

| poziom | ma reverse | ma done-validation | co jest |
|---|---|---|---|
| **URI-proces** (Contract) | `inverse` (opcjonalne) | ❌ | `out` + `conform()` sprawdzają KSZTAŁT odpowiedzi, nie STAN świata |
| **Ticket** (planfile) | — | ❌ | `acceptance_criteria = []` w **6/6** otwartych ticketów |

Kluczowe: `conform()` (contract-gate) waliduje, że odpowiedź pasuje do `out` — ale odpowiedź
może być poprawna kształtem, a cel nieosiągnięty. Np. `email://…/message/command/move` zwraca
`{ok:true, moved:[…]}`, lecz **czy mail faktycznie trafił do Junk** — tego kontrakt nie
sprawdza. To jest różnica między **walidacją schematu** a **walidacją postcondition (celu)**.

## Atrybuty pojedynczego URI-procesu (stan obecny)

Standard: `urirun/docs/URI_COMMAND_STANDARD.md` + `URI_NATIVE_CONNECTOR_CHECKLIST.md` (część
projektu **urirun**). Proces / `Contract` niesie:

- **class/effect** — `query` (bez efektu, powtarzalny) vs `command` (mutuje),
- **isolation** — in-process vs isolated,
- **inp / out** — schematy wejścia/wyjścia,
- **errors**, **examples**,
- **`inverse`** — URI odwracające (reversibility),
- brak: **`verify` / `postcondition`** — oracle „czy osiągnięto cel".

## Propozycja (symetria reverse ↔ verify)

1. **Standard URI-procesu:** dodać pole **`verify` / `postcondition`** obok `inverse` —
   URI-check (lub predykat), który potwierdza efekt. Checklist: „a mutating command SHOULD
   return an `inverse` AND declare a `verify`".
2. **Contract:** obok `out` (kształt) dodać `postcondition` (world-state oracle).
3. **Ticket:** wymagać `acceptance_criteria` jako sprawdzalnych URI (np.
   `verify://tests/pass`, `email://…/query/count?folder=Junk`) — bez nich ticket jest
   nie-wykonywalny autonomicznie.
4. **Pętla:** bramka — `ticket → done` TYLKO gdy `verify` zielone; inaczej `blocked` + gap.

## Co zbudowaliśmy w tej sesji (stos autonomii, który OBNAŻA tę lukę)

Panel `/work` + connectory URI-native (wszystkie editable, testy zielone):

| Connector / warstwa | Rola | Odkrycie |
|---|---|---|
| **watchdog** (`watch://`) | wykrywa zapętlenia + rootcause + oscylację; **circuit-break** (auto-diagnoza jako ticket) | koru pętli bez wykonawcy |
| **agents** (`agent://`) | realny executor (`claude -p`…); host most `agent_admin` + blokada współbieżności | 5 narzędzi headless dostępnych; `claude -p` **gated** (plan, nie zapis) |
| **continuity** (`gap://`) | `ready`/`verify`/`analyze`/`scan` — obnaża per-ticket luki | **6/6 ticketów bez acceptance_criteria → Done nieweryfikowalny** |
| **loop** (`loop://`) | zamknięta pętla: czyta gap+watch, stosuje akcję (SAFE auto, run-agent gated) | domyka OBSERWUJ→DZIAŁAJ; brak ZWERYFIKUJ blokuje pełną autonomię |
| **cron** (`cron://`) | harmonogram + kalendarz + eksport .ics/Google | cykliczne odpalanie pętli |
| panel `/work` | okna: operacje, logi URI, konsola shell, watchdog, luki, pętla; pełne **API** (`/api/work/actions`) | całość sterowalna przez API |

**Wniosek:** mamy `OBSERWUJ` (watchdog/gap), `ZDECYDUJ` (loop policy), `DZIAŁAJ` (agent). Brakuje
**`ZWERYFIKUJ`** — i to nie z powodu braku kodu, lecz braku **cechy `verify`/`postcondition`
w standardzie URI-procesu i `acceptance_criteria` na ticketach**. To jest korzeń „dlaczego
nadal nie działa w pełni autonomicznie".

## Następny krok

Dodać `verify://` jako pierwszej klasy cechę procesu (symetryczną do `inverse`) + wymóg
`acceptance_criteria` na ticketach → wtedy pętla ma czym domknąć `DZIAŁAJ → ZWERYFIKUJ → done`.
