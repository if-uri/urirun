# URI-Native Connector Checklist — jak owinąć bibliotekę w proces URI

Status: standard roboczy (2026-07-05). Wyprowadzony z budowy `urirun-connector-vdisplay`
(owinięcie pakietu `vdisplay`) i z anty-wzorców, które ta budowa ujawniła. Dotyczy KAŻDEJ
biblioteki, którą chcemy udostępnić jako proces URI (vdisplay, vql, i kolejne).

Cel: biblioteka staje się **komponowalna w flow, deployowalna na węzeł i widoczna dla
readiness kernela** — a nie tylko wołalna z Pythona albo przez cienki most `uri→DSL`.

---

## 0. Test dojrzałości: most vs connector

Najpierw sprawdź, co pakiet już ma:

| Ma | To jest | Wystarcza? |
|---|---|---|
| `lib.func()` (API Pythona) | biblioteka | NIE — nie ma powierzchni URI |
| `uri2lib` / `cli2lib` (uri→string DSL) | **cienki most** | NIE — nie serwowalny na węźle, nie komponowalny |
| `conn.handler` + `urirun_bindings` entry point | **natywny connector** | TAK |

`uri2vdisplay`/`uri2vql` to cienkie mosty (`uri_to_dsl()` → string). To NIE są natywne
connectory. Owinięcie = dodanie powierzchni connectora obok istniejącej biblioteki, reużywając
jej API — nie przepisywanie logiki.

---

## 1. Struktura pakietu (minimalna)

```
urirun-connector-<lib>/
  pyproject.toml                         # entry point urirun.bindings + scripts
  urirun_connector_<lib>/
    __init__.py                          # re-export publicznych handlerów
    core.py                              # conn.handler + urirun_bindings + main
    connector.manifest.json              # id/name/summary/useCases/flowExample/requires
  tests/
    test_<lib>.py                        # bindings + lazy-import guard + envelope
  README.md
```

`pyproject.toml` MUSI mieć:
```toml
[project.entry-points."urirun.bindings"]
<lib> = "urirun_connector_<lib>.core:urirun_bindings"
[project.scripts]
urirun-<lib> = "urirun_connector_<lib>.core:main"
dependencies = ["urirun>=0.4.14", "<lib>>=..."]
```

---

## 2. Zasady, których łamanie boli (nauczki z vdisplay)

### 2a. LAZY imports — biblioteka importowana TYLKO w handlerze
`import <lib>` na szczycie modułu = każdy import connectora, generowanie bindings i sam węzeł
płacą koszt (i ryzyko) ciężkich zależności. **vdisplay przy imporcie potrafi ściągnąć
playwright.** Rozwiązanie: import wewnątrz funkcji-akcesora.
```python
def _api():
    from <lib> import something   # lazy — nie na szczycie modułu
    return something
```
Guard testem: `test_lazy_import_no_<lib>_at_module_top` — po `import connector.core`
`<lib>` NIE może być w `sys.modules`. (vdisplay: import `payloads` 0,06 s bez playwright.)

### 2b. Handler NIGDY nie rzuca — zawsze koperta urirun
```python
try:
    data = _api().do(...)
except Exception as exc:            # noqa: BLE001
    return urirun.fail(str(exc), connector=CONNECTOR_ID, action="...")
return urirun.ok(connector=CONNECTOR_ID, action="...", **data)
```
Dzięki temu brak biblioteki na węźle degraduje się do `ok:false` z powodem, nie do crasha —
konsument (readiness) robi graceful fallback.

### 2c. Read-only = in-process (`isolated=False`); mutacje = izolowane
Zapytania bez efektów ubocznych (enumeracja okien, diagnoza) → `isolated=False` (szybko,
w procesie węzła). Akcje mutujące/HID → `isolated=True` (crash nie zdejmuje węzła). Patrz
lekcja z kvm: capture in-process, input izolowany.

### 2d. NIE auto-instaluj ciężkich zależności (ANTY-WZORZEC vdisplay)
vdisplay auto-instaluje playwright — to blokuje czyste wdrożenie na węzeł i jest inwazyjne na
maszynie usera. Biblioteka URI-native musi mieć ciężkie deps **opcjonalne** (`extras`), a
ścieżka używana przez connector (tu: enumeracja okien) NIE może ich wymagać. **Wniosek do
vdisplay: wydzielić enumerację do ścieżki bez playwright.**

---

## 3. Wdrożenie na węzeł — ZWERYFIKOWANY mechanizm (lenovo 2026-07-05)

kvm flat-deployuje się przez `host deploy --code *.py` (jeden pakiet, bez ciężkich deps).
Biblioteki nie da się flat-deployować, ale connector owijający TAK — o ile biblioteka jest na
węźle. Sprawdzona procedura (skrypt: `urirun/scripts/deploy_lib_connector.sh`):

1. **Zainstaluj bibliotekę na węźle przez MESH** (bez SSH) — podpisaną trasą
   `node://<name>/package/command/install` (`spec`: string|array pip-spec; węzeł musi mieć
   `--manage` + key-auth). `urirun host run <url> node://<name>/package/command/install
   --payload '{"spec":["vql","pillow"]}' --identity ~/.ssh/id_ed25519` → `installed`+`returncode`.
   (vql 0.1.7 i vdisplay 0.1.53 SĄ na PyPI; instalacja bazowa nie ciąga playwright.)
2. **Flat-deploy connectora pod UNIKALNĄ nazwą modułu.** ⚠️ PUŁAPKA: `--code` wypycha pliki po
   BASENAME do jednego katalogu, więc każdy connector jako `core.py` KOLIDUJE — redeploy kvm
   nadpisał `core.py` vql, ref `core:image_diagnose` wskazał moduł kvm → *„local function ref is
   not callable"*. Lek: wypchnij `<id>_core.py` i przepisz `python.module` w bindings na
   `<id>_core`. Skrypt robi to automatycznie.

Konsekwencja: konsument node-side musi wołać connector przez TRASĘ (`vdisplay://…`), NIE przez
import pakietu (na węźle żyje jako flat `<id>_core`, nie `urirun_connector_<id>` → import padnie,
readiness degraduje do fallbacku).

**Zweryfikowane na lenovo:** kvm capture → `vql://image/query/analyze` (130 obiektów, 65 ms) →
`vql://image/query/regions` (klikalne center) — cały tor vision-grounding działa NA WĘŹLE.
`vdisplay://monitors` działa; `vdisplay://windows` uczciwie `ok:false` („xdotool not found" +
limit Wayland) — potwierdza, że vision (vql) jest właściwą ścieżką na Wayland, nie enumeracja okien.

---

## 4. Powierzchnia = trasy, które konsument realnie składa

Projektuj trasy pod to, co czyta readiness/flow, nie pod całe API biblioteki:
```
<lib>://host/<zasób>/query/<verb>     # read-only, isolated=False
<lib>://host/<zasób>/command/<verb>   # mutacja, isolated=True, z inverse jeśli się da
<lib>://host/diagnose/query/report    # „czy sygnał z tej warstwy można ufać tutaj"
```
vdisplay: `windows/query/list`, `monitors/query/list`, `window/query/find`,
`diagnose/query/report`. Każda zwraca koperty; `windows` niosą pole `nl` (grounding).

---

## 5. Testy obowiązkowe

1. `test_bindings_serializable_and_complete` — `set(bindings) == ROUTES`, `json.dumps(bindings)`
   (brak wycieku żywych referencji), read-only trasy mają adapter `local-function`.
2. `test_lazy_import_no_<lib>_at_module_top` — import connectora nie ciągnie biblioteki.
3. `test_<verb>_returns_envelope` — na żywej sesji zwraca kopertę, NIGDY nie rzuca.
4. walidacja wymaganych argumentów (`title` puste → `ok:false`).

---

## 6. Kolejni kandydaci do owinięcia (ten sam wzorzec)

| Biblioteka | Rola URI | Uwaga strukturalna |
|---|---|---|
| **vdisplay** | `vdisplay://` window/monitor/session (nl) | ✅ zrobione; TODO: playwright opcjonalny |
| **vql** | `vql://image/query/{analyze,regions,diagnose}` | ✅ zrobione (2. connector — checklist zwalidowany); grounding po geometrii/kolorze, NIE tekst |
| **urivision/VURI** | `urivision://process/{compile,run}` | ✅ zrobione (3. connector); miał DSL .vuri ale BRAK entry point bindings — owinięty |
| OCR/paddle/easyocr | `ocr://` (już jest connector) | wzorzec lazy-import ciężkiego modelu |
| smart-crop | `artifact://image/crop` | sprawdzić lazy PaddleOCR (mkldnn off) |

---

## 7. Definicja „gotowe" (Definition of Done) dla URI-native

- [ ] `conn.handler` trasy + `urirun_bindings` entry point (nie tylko most uri→DSL)
- [ ] lazy import biblioteki + test-guard
- [ ] każdy handler zwraca kopertę, nie rzuca
- [ ] read-only in-process / mutacje izolowane
- [ ] ciężkie deps opcjonalne; ścieżka connectora ich nie wymaga
- [ ] manifest.json (id/summary/useCases/flowExample/requires)
- [ ] testy: bindings + lazy-guard + envelope
- [ ] konsument importuje opcjonalnie + degraduje (brak biblioteki na węźle ≠ crash)
- [ ] plan wdrożenia na węzeł (pip install lub PyPI), nie flat-deploy ciężkiej biblioteki
