# BACKLOG-AGENT — zaległe prace do wykonania (przekazanie dla agenta)

Wygenerowano: 2026-07-04. Kontekst: zakończona sesja refaktoryzacyjna (szczegóły niżej).
Ten dokument jest samowystarczalny — zawiera zasady operacyjne, stan zastany i zadania
z krokami weryfikacji. Aktualizuj go po wykonaniu każdej pozycji (odhaczaj, dopisuj wnioski).

## Zasady operacyjne (przeczytaj ZANIM zaczniesz)

1. **NIGDY nie rób `git commit`/`git push`** — commity wykonuje wyłącznie Tom.
   Dodatkowo connect.ifuri.com **auto-commituje drzewo robocze urirun i urirun-flow co
   kilka minut** (commit message "refaktor") — twoje edycje znikają z `git status`, ale
   lądują w HEAD. Nie panikuj, gdy plik "sam" się zmieni; przeczytaj go ponownie przed edycją.
2. **Serwis chatu trzyma moduły w pamięci.** Po KAŻDEJ edycji źródeł urirun/urirun-flow,
   zanim przetestujesz na żywo:
   `./venv/bin/urirun-service-chat restart --project /home/tom/github/if-uri/urirun --db /home/tom/.urirun/host.db --host 127.0.0.1 --port 8194`
   Dashboard: http://127.0.0.1:8194/ · baza: `/home/tom/.urirun/host.db`.
3. **Mechanika przesłaniania importów** (źródło większości bólu w tym workspace):
   findery instalacji editable siedzą na KOŃCU `sys.meta_path`, więc dowolny wpis
   `sys.path` z pakietem o tej samej nazwie (cwd przy pytest, insert w confteście)
   wygrywa z instalacją editable. Diagnoza zawsze od `print(pakiet.__file__)`.
4. **Narzędzie diagnostyczne:** `venv/bin/python adapters/python/scripts/dev_deps_doctor.py`
   (`--fix` reinstaluje przestarzałe lokalne instalacje jako editable). Exit 1 = SHADOW/STALE.
   Jest wpięte jako bramka w `goal.yaml` (strategies.python.test) i jako testy
   `adapters/python/tests/test_dev_deps_doctor.py`. Serwis emituje event
   `urirun.host_dashboard.stale_local_deps` przy starcie, gdy wykryje dryf.
   UWAGA: sekcja "local.dev.txt pending fixes" w output może kłamać (patrz zadanie Z4) —
   ufaj sekcji "local file:// installs" liczonej na żywo.
5. **Testy:** urirun: `cd adapters/python && ../../venv/bin/python -m pytest tests/ -q`
   (stan zastany: 1714 passed / 0 failed). urirun-flow:
   `cd ~/github/if-uri/urirun-flow && ~/github/if-uri/urirun/venv/bin/python -m pytest tests/ -q`
   (139 passed). Po swoich zmianach oba muszą pozostać zielone.
6. **Pakiety zewnętrznie posiadane** (kod żyje w siostrzanym repo, NIE w adapters):
   `urirun_flow` → `~/github/if-uri/urirun-flow`, `urirun_connector_router` →
   `~/github/if-uri/urirun-connector-router`, `urirun_connector_scanner` →
   `~/github/if-uri/urirun-connector-scanner`. Conftesty (adapters/python/conftest.py
   i urirun-flow/conftest.py) wymuszają właściwą kolejność ścieżek — nie psuj tej logiki.

## Stan zastany (co już zrobiono — nie powtarzaj)

- Recall gate skraca znane intenty (33 s → 7–9 s); epizod zwalidowany env-fingerprintem
  omija replan `skip-when` (`_recalled_to_flow(env_validated=)` w chat_orchestrator).
- Uziemianie etykiet monitorów w `urirun-flow/urirun_flow/env_selection.py`: koercja
  `label`, `prompt-label`, `prompt-label-over-skip`, `prompt-label-over-explicit`
  + maskowanie parametrów domenowych w `_flow_normalize.py`. Testy w
  `urirun-flow/tests/test_env_selection.py`.
- Timingi: fazy w odpowiedzi `/api/chat/ask` (`timings`), per-krok `ms` w timeline
  (thin driver), log do host_db, w epizodach.
- Cache sond środowiska (`urirun-flow/urirun_flow/_env_probe_cache.py`, TTL 10 s):
  TYLKO `env/query/profile` + `display/query/info`; ścieżki pamięci Twin
  (drift/remember/known-good) mają `use_cache=False` — NIE zmieniaj tego bez zrozumienia
  testów `test_flow_twin.py`.
- Shimy skanera zredukowane do 9-liniowych aliasów `sys.modules`; twin widget w chacie
  pokazuje scoped przebieg (`/api/twin/state?prompt=...` → `focus`); menu Overview usunięte.
- 11 repo zależności dostało git init + baseline; manifesty `local.dev.txt` odświeżone;
  `urirun-declarative` przeinstalowane editable (finder zamiast legacy .pth).

## Zadania (priorytet malejący)

### Z1. [WYMAGA TOMA] Usunąć martwe snapshoty pakietów zewnętrznych
`git rm -r adapters/python/urirun_flow adapters/python/urirun_connector_router`
Agentowi może to zablokować klasyfikator uprawnień — wtedy poprosić Toma.
Weryfikacja: pełna suita urirun zielona; `dev_deps_doctor.py` bez SHADOW;
`test_dev_deps_doctor.py` przechodzi. Potem można UPROŚCIĆ conftesty (usunąć
czyszczenie cieni), ale dopiero PO usunięciu katalogów.

### Z2. [CZĘŚĆ AGENTOWA WYKONANA 2026-07-04] Wydmuszki urirun-cdp / urirun-connectors-toolkit / urirun-runtime
WYKONANO wariant (b) w zakresie venv: `pip uninstall` trzech NON-EDITABLE dystrybucji
z urirun/venv, if-uri/venv i urirun/.venv; moduły rozwiązują się teraz do źródeł w
adapters/python (editable). Zweryfikowano: doctor exit 0 bez sekcji NON-EDITABLE,
suita urirun 1715 passed, urirun-flow 139 passed. POZOSTAŁO (Tom): decyzja o kasacie
pustych katalogów repo. UWAGA sprzeczna z rekomendacją (b): urirun-runtime 0.2.0 i
urirun-connectors-toolkit 0.2.0 SĄ opublikowane na PyPI i harness multiplatform ich
używa w publicznej instalacji (PUBLIC_RUNTIME_DEPS) — przed kasatą katalogów sprawdzić,
skąd CI buduje te wydania.
Stan: trzy repo w `~/github/if-uri/` bez źródeł pakietu (tylko build/egg-info/testy),
zainstalowane NON-EDITABLE 0.2.0 w venv; prawdziwy kod żyje w `adapters/python/…`
i wygrywa przez finder dystrybucji urirun. Opcje:
(a) dokończyć ekstrakcję wzorem urirun-flow: przenieść źródła do repo siostrzanego,
    `exclude` w adapters/python/pyproject.toml, `pip install -e`, testy przenieść;
(b) `./venv/bin/pip uninstall -y urirun-cdp urirun-connectors-toolkit urirun-runtime`
    i skasować puste repo (decyzja Toma o kasacie katalogów).
Rekomendacja z sesji: (b), chyba że planowane są osobne wydania (wtedy (a) dla cdp).
Weryfikacja: doctor bez wpisów NON-EDITABLE dla tych nazw; suita zielona.

### Z3. Self-heal flow engine — dokończenie (największy wątek merytoryczny)
Z pamięci projektu, pozostałe elementy: reguła eskalacji surface, preflight,
feedback loop, goal-verify. Punkty zaczepienia: `urirun-flow/urirun_flow/flow_thin.py`
(_thin_driver, _thin_goal_verify, preflight), `urirun_flow/recovery.py`,
`urirun/host/decision_loop.py`. Wykonawca diagnose→remediate→retry już działa
(kind-guard + circuit-breaker gotowe). Zacznij od przeczytania
`~/.claude/.../memory/self-heal-flow-engine.md` — jeśli niedostępne, od testów
`tests/test_diagnostics.py` (klasa ThinDriverMemoryTests).

### Z4. [WYKONANE 2026-07-04] Naprawić detekcję statusu instalacji w ~/github/local.dev.sh
ROZWIĄZANE — raport nie kłamał, tylko mówił o INNYM venv niż doktor: local.dev.sh bierze
najbliższy venv w górę drzewa, więc dla adapters/python trafiał w pakietowy
`adapters/python/.venv`, który był (a) MARTWY (pip "required file not found" — zniknął
bazowy interpreter) i (b) miał stary planfile 0.1.103; doktor patrzy na urirun/venv.
Naprawy: martwy .venv odtworzony (editable urirun+contract/router/flow+planfile+radon+
pytest); local.dev.sh dopisuje teraz POCHODZENIE stanu instalacji do każdego wiersza
(`0.1.106 editable @if-uri/urirun/adapters/python/.venv`) — raport i doktor są jednoznacznie
porównywalne. Zweryfikowano: manifest zgodny z sekcją live doktora; `--check if-uri` OK.
Przy okazji local.dev.sh dostał tryby bramkowe `--check` / `--check-release`
(pytest lane tests/test_dep_health.py w urirun+kvm+ocr+camera; `make publish|release`
blokowane przy niespełnialnych zależnościach) — patrz ~/github/local.dev.md.

### Z5. Porządek w planfile (fork-widmo) — [ZŁAGODZONE 2026-07-04, kasata u Toma]
`~/github/semcod/2026/planfile` (0.1.48) to stary fork zaśmiecający manifesty;
żywe źródło to `~/github/semcod/planfile` (0.1.106, editable w venv urirun).
Zarchiwizować/skasować fork — decyzja i wykonanie po stronie Toma (poza if-uri).
TYMCZASEM: `semcod/2026`, `semcod/rebuild` i `maskservice/archive` są wykluczone ze
skanowania local.dev.sh przez `~/github/local.dev.ignore`, więc fork już nie zaśmieca
manifestów ani indeksu duplikatów.

### Z6. Latencja — dalsze cięcia (po pomiarach, nie na ślepo)
Dane per-faza są w `timings` każdej odpowiedzi chatu; per-krok w `timeline[].ms`.
Kandydaci wg pomiarów z sesji: `discover` ~0,95 s na zimno (cache discovery mesh
z krótkim TTL — uwaga na wykrywanie offline węzłów), `twinPreview` 0,4–0,6 s
(plan_generate sonduje własną ścieżką — rozważ podpięcie do _env_probe_cache),
capture 4 s przy 7360×3611 (parametr `max_width` w kontrakcie kvm capture —
preferencja użytkownika, nie zmieniaj domyślnie).

### Z7. Deploy hygiene (roadmapa)
Rozdzielenie auth od registry przy deploy, footgun `--merge`. Kontekst w pamięci
projektu (`urirun-optimization-plan`). Wymaga doprecyzowania zakresu z Tomem.

### Z8. [ZABLOKOWANE: node .201 offline] Konsolidacja kvm + walidacja na lenovo
Staged validation flow gotowy; czeka na powrót węzła 192.168.188.201:8766.
Deploy przez `--identity`; szczegóły w pamięci projektu (`kvm-connector-consolidation`,
`lenovo-node-201`).

### Z9. [WYKONANE 2026-07-04] Odświeżyć snapshot urirun-multiplatform-test/.work
Odświeżone przez `URIRUN_SOURCE_DIR=~/github/if-uri/urirun python3 scripts/install_urirun.py`
(bez env skrypt klonuje z GitHuba — UWAGA: `run_tests.py` też re-instaluje, więc pełny
przebieg z lokalnymi, niezacommitowanymi poprawkami wymaga eksportu URIRUN_SOURCE_DIR).
Świeży snapshot ujawnił i pozwolił naprawić PRODUKTOWY bug publicznej instalacji:
`urirun host add-node` (ścieżka advanced) importował `urirun.host_dashboard`, który
przy imporcie ciągnie shim skanera → ModuleNotFoundError bez urirun-connector-scanner.
Fix w `urirun/host/node_cli.py`: add-node używa lekkich `object_registry.node_add` +
`node_types` zamiast całego dashboardu. Dodatkowo `scripts/install_urirun.py`
PUBLIC_RUNTIME_DEPS += urirun-runtime>=0.2.0, urirun-connectors-toolkit>=0.2.0
(bez nich `host add-node` = "mesh not available"). Wynik: harness 49 passed / 0 failed
(było 2 failed / 47 passed); XFAIL test_host_mesh_works_without_source_pythonpath
potwierdza niezależnie warunek publikacyjny z Z-nowego niżej.

### Z10. [NOWE — CZEKA NA TOMA] Publikacja 8 pod-pakietów przed kolejnym wydaniem urirun
`local.dev.sh --check-release if-uri/urirun/adapters/python` (i XFAIL harnessu) pokazują:
następne wydanie urirun będzie NIEINSTALOWALNE, bo deklarowane zależności nie istnieją na
PyPI: urirun-contract, urirun-connector-router, urirun-flow>=0.2.2, urirun-connector-scanner,
urirun-declarative, urirun-openapi-import, urirun-uinput, urirun-widgets. Dystrybucje
wszystkich 8 są zbudowane + `twine check` PASSED w `dist/` ich repo; upload zablokowany
agentowi przez klasyfikator uprawnień (akcja publiczna). Komenda dla Toma:
`for r in urirun-contract urirun-connector-router urirun-flow urirun-connector-scanner \
   urirun-declarative urirun-openapi-import urirun-uinput urirun-widgets; do \
   (cd ~/github/if-uri/$r && ~/github/if-uri/urirun/venv/bin/python -m twine upload --skip-existing dist/*); done`
Po publikacji: `make release` w urirun samo potwierdzi gotowość (bramka dep-health-release),
a XFAIL w harnessie zacznie przechodzić (zdjąć marker).

## Weryfikacja końcowa po każdej sesji pracy

```bash
cd ~/github/if-uri/urirun/adapters/python && ../../venv/bin/python -m pytest tests/ -q      # 1714+ passed
cd ~/github/if-uri/urirun-flow && ~/github/if-uri/urirun/venv/bin/python -m pytest tests/ -q # 139+ passed
~/github/if-uri/urirun/venv/bin/python ~/github/if-uri/urirun/adapters/python/scripts/dev_deps_doctor.py  # exit 0
# restart serwisu (patrz zasada 2) + smoke:
curl -s -X POST http://127.0.0.1:8194/api/chat/ask -H 'Content-Type: application/json' \
  -d '{"prompt":"zrob zrzut ekranu","targets":["host"],"execute":true}' | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d.get('ok'), (d.get('generator') or {}).get('provider'), (d.get('timings') or {}).get('total'),'ms')"
# oczekiwane: True recall <10000 ms
```
