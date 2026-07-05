# Resolve-First Control Plane — realokacja: vdisplay / vql / kvm / urivision / readiness

Status: **propozycja do akceptacji** (2026-07-05). Powstało z incydentu, w którym runner
computer-use, mając w `browser_sessions` zalogowany profil LinkedIn, mimo to otworzył
throwaway debug-Chrome → konflikt okien + porażka auth. Root-cause: **planowanie na
założeniach zamiast na rozpoznanym stanie środowiska**. Zasada docelowa: **resolve surface
first, act last**.

Ten dokument mapuje, **który pakiet co wystawia jako proces URI** i **jak readiness kernel je
składa** — zanim napiszemy kod cross-repo.

---

## 1. Zasada główna: z „act first" na „resolve surface first"

Dziś (błędnie):
```
zobacz ekran → kliknij / wpisz → sprawdź
```
Docelowo:
```
query env → resolve surface → check auth/session → acquire focus/lease
          → plan → act → verify → trace
```
Przed jakimkolwiek wejściem system MUSI odpowiedzieć (twarda bramka `ready://`, nie sugestia):
na której powierzchni działam · który profil jest zalogowany · czy mam jednoznaczne okno ·
czy wolno mi przejąć fokus · czy mam stabilną metodę wejścia · czy istnieje lepsza warstwa niż HID.

---

## 2. Co JUŻ istnieje (i było dublowane ad hoc)

| Pakiet | Czym jest | Kluczowe, czego kvm NIE ma |
|---|---|---|
| **vdisplay** (`~/github/wronai/vdisplay`) | Cross-platform virtual-display + orkiestracja okien/monitorów. Okna/monitory z polem **`nl`** (opis NL). | **Multi-backend enumeracja okien** (atspi/uia/ax/xdotool/browser + **vision**) — WIDZI okna Chrome, gdzie atspi zawiódł. Broker sesji CDP (`browser_session_store`). `control/policy.py` = readiness backendów wejścia per host (Wayland/X11). |
| **vql** (`~/github/oqlos/vql`) | Visual Query Language: obraz → struktura regionów/obiektów; render zwrotny. | Strukturalna analiza sceny (`adopt/window.py`, `adopt/capture_screen.py`, `adopt/capture_policy.py`). |
| **urivision / VURI** (`~/github/if-uri/urivision`) | DecisionCard z obrazu: decyzja + dowody, nie opis. | Warstwa 3 percepcji — decyzja LLM z kotwicami. |
| **urirun-connector-kvm** | HID (uinput klawiatura/mysz), capture (ciepły screencast), OCR host-side, CDP DOM verbs, readiness kernel MVP. | Prymitywy wykonania + capture. |

**Diagnoza:** kvm dorobił ad hoc enumerację okien (atspi, ślepy na Chrome), OCR i introspekcję
sesji — czyli **zdublował vdisplay/vql**. To ten sam wzorzec błędu co throwaway: użycie tego, co
pod ręką, zamiast rozpoznania, co już istnieje.

**Luka mostów URI:** `uri2vdisplay` i `uri2vql` to CIENKIE translatory `uri→DSL` (string), a NIE
natywne connectory urirun — brak `conn.handler`, `urirun_bindings()`, serwowanych tras. Nie da
się ich deployować na węzeł ani komponować w flow/readiness jak kvm.

---

## 3. Docelowa realokacja odpowiedzialności

```
                          ┌─────────────────────────────┐
User/Voice/Text → Intent →│      CURI process (.curi)    │
                          └──────────────┬──────────────┘
                                         ▼
                          ┌─────────────────────────────┐
                          │      READINESS KERNEL        │  ready://<task>
                          │  składa sygnały z warstw:     │  → ready|blockers|
                          └───┬───────┬───────┬──────────┘    recommended_surface|forbidden
                              ▼       ▼       ▼
             vdisplay://   vql://   secret://   (sygnały: okna/sesje/env, analiza wizualna, auth)
                              │
                              ▼
                    ┌───────────────────┐
                    │  SURFACE RESOLVER  │  ranking: api > browser-existing-auth
                    │  + POLICY GATE     │        > browser-cdp > os-accessibility > kvm-hid
                    └─────────┬─────────┘  forbid: throwaway, cookie-copy-linux-keyring
                              ▼
     ┌──────────────┬─────────────────┬──────────────────┬──────────────┐
     ▼              ▼                 ▼                  ▼              ▼
 connector://   browser-ext://   browser-cdp://    os-accessibility  kvm-hid://
  (linkedin,     (native msg)     (istniejąca         (vdisplay)      (ostatnia
   gmail…)                         sesja)                              warstwa)
     └──────────────┴─────────────────┴──────────────────┴──────────────┘
                              ▼
                         VURI/urivision verify → ActionTrace (artifact://runs/{id})
```

### Kto co wystawia jako URI (docelowo)

- **vdisplay** = natywny connector percepcji środowiska:
  - `vdisplay://host/windows/query/list` — okna (multi-backend + `nl`), z pewnością enumeracji
  - `vdisplay://host/monitors/query/list` — monitory
  - `vdisplay://host/session/query/resolve` — który profil/przeglądarka zalogowany do usługi, `cdp_port`
  - `vdisplay://host/surface/query/policy` — używalny backend wejścia per host (Wayland/X11)
  - `vdisplay://host/window/command/focus|raise` — jednoznaczne podniesienie okna
- **vql** = natywny connector analizy wizualnej:
  - `vql://image/query/analyze` — obraz → struktura scen/regionów
  - `vql://image/query/find` — lokalizacja elementu w strukturze
- **urivision / VURI** = warstwa decyzji: `view://…/decision-card` (już URI-first).
- **kvm** = kurczy się do prymitywów: HID (`input/*`), capture (`screen/*`), CDP DOM (`cdp/page/*`).
  Enumeracja okien / sesje / policy wejścia → **przeniesione do vdisplay** (kvm je konsumuje).
- **readiness kernel** = obecny MVP w kvm (`ready/query/resolve`); docelowo **konsumuje
  vdisplay/vql/secret** zamiast ad-hoc atspi+browser_sessions. Po przełączeniu
  `window_enumeration_degraded` znika (vdisplay ma vision-backend).

---

## 4. Twin rozszerzony o stan pracy (nie tylko capabilities)

Obecny twin modeluje zdolności (capture/ocr/uinput/cdp). Za mało. Docelowo twin modeluje też
**stan sesji/auth/okien/fokusu/aktywności usera** — źródłem tych sekcji są trasy vdisplay:

```yaml
twin:
  capabilities: { capture, ocr, uinput, cdp }        # jak dziś
  sessions:                                          # z vdisplay://session/resolve
    linkedin: { authenticated: true, profile: .../Default, source: vdisplay, confidence: 0.94 }
  surfaces:                                           # z vdisplay://surface/policy + vql
    active: { kind, app, title, focus_confidence }
    candidates: [browser-cdp, remotedesktop-portal, kvm-hid]
  focus:                                              # z vdisplay://windows
    owner_known: bool, ambiguous_windows: bool, competing_chrome_windows: bool
  safety: { user_active, destructive_action, secrets_required }
```

Zasada: `authenticated=true` NIGDY jako fakt ogólny — zawsze przypięte do profilu/procesu/okna/connectora.

---

## 5. Zasady projektowe (twarde)

1. Model nigdy nie wybiera bezpośrednio warstwy wykonania — robi to surface resolver + policy.
2. Planner NIE MOŻE otworzyć throwaway browser, jeśli istnieje zalogowana sesja.
3. KVM/HID jest OSTATNIĄ warstwą, chyba że policy mówi inaczej.
4. Copy cookies NIE jest produkcyjną strategią auth (na Linuksie klucz w keyring — kruche).
5. Każda akcja ma precondition, receipt i verification.
6. Każdy run ma `lease://` i cleanup (throwaway kaskaduje — patrz incydent).
7. Twin modeluje capabilities ORAZ auth/session/focus/windows/user-activity.
8. Brak pewności = **block**, nie zgadywanie.

---

## 6. Plan etapowy (do akceptacji)

**Etap 1 — fundament resolve-first** (część już jest):
- [x] `ready/query/resolve` (readiness kernel MVP w kvm) — DZIAŁA na żywo, gate throwaway/cookie-copy.
- [ ] `urirun-connector-vdisplay` — natywny connector (conn.handler + urirun_bindings nad
      `application.executor` vdisplay): windows/monitors/session/surface. **Największa wartość:
      naprawia enumerację Chrome, której kvm nie umie.**
- [ ] Przełączyć readiness kernel na konsumpcję vdisplay zamiast atspi+browser_sessions.
- [ ] `lease://run` + cleanup; `action-trace.v1` schema; `curictl doctor`/`curictl ready`.

**Etap 2 — trwały input daemon:** persistent uinput daemon + input transaction API
(`input://keyboard/session/{start,type,commit,close}`) + focus probe + ActionReceipt.
(Rozwiązuje gubienie znaków przy per-batch klawiaturze.)

**Etap 3 — browser extension / native messaging:** własna warstwa
`browser-extension://chrome/current-tab/dom/{query,fill,click}` — realna zalogowana sesja bez
kopiowania cookies.

**Etap 4 — connector-first:** `linkedin://`, `gmail://`, `drive://`, `slack://` — gdzie jest API,
nie używać UI. (`linkedin://post/command/publish` JUŻ istnieje.)

**Etap 5 — produkt KVMAT/CyberMysz:** node z HDMI capture + USB HID + urirun node + CURI runner +
VURI verifier + trace + dashboard.

**vql** natywny connector: równolegle do Etapu 1/2, gdy analiza wizualna wchodzi jako warstwa
percepcji obok urivision.

---

## 7. Przykładowy `.curi` (docelowy)

```txt
proc control://linkedin/post/publish

require ready://service/linkedin/auth
require ready://surface/linkedin/post-composer
require policy://no-throwaway-browser
require policy://human-confirm-before-publish

resolve surface for task://linkedin/post/publish prefer api,browser-existing,kvm-hid

if surface == connector://linkedin/api
  act linkedin://post/publish content=artifact://drafts/post.md
  verify linkedin://post/query/latest contains artifact://drafts/post.hash
else if surface == browser://existing
  act browser://dom/fill target="post-composer" content=artifact://drafts/post.md
  act browser://dom/click target="publish-button" confirm=user://approval
else if surface == kvm://hid
  inspect capture://screen for aspect://linkedin/composer
  focus input via focus://tab-probe
  type artifact://drafts/post.md
  verify capture://screen contains draft

emit artifact://runs/linkedin-post.trace.json as schema://control/action-trace.v1
```

---

## 8. Reuse z Oqlos/hardware gateway (mapowanie mentalne)

```
hardware health   → surface health         plugin gateway → action adapter gateway
hardware diagnose → environment diagnose    event store    → action trace store
preflight hw      → readiness kernel         doctor        → computer-use doctor
```

Docelowe CLI: `curictl doctor|surfaces|sessions|ready <task>|run <.curi> --dry-run|trace last`.

---

## 9. Najbliższa decyzja

Etap 1, krok „natywny connector vdisplay" ma najwyższy stosunek wartość/koszt: reużywa gotową,
multi-backendową enumerację okien vdisplay (naprawia lukę Chrome), nie duplikuje logiki, daje
wzorzec dla vql. Po akceptacji tego dokumentu — implementacja `urirun-connector-vdisplay` +
przełączenie readiness kernela.
