# Plan Kolejnych Kroków - 2026-07-02

## Priorytety po refaktoryzacji z dnia 2026-07-02

### Faza 1: Stabilizacja i Testowanie (Wysoki priorytet)

#### 1.1 Testy jednostkowe dla nowych modułów
**Status:** Brakujące
**Szacowany czas:** 2-3 dni

**Zadania:**
- [ ] Dodanie testów dla `urirun_connector_router/routing.py`
  - Test `parse_uri()` z różnymi formatami URI
  - Test `uri_is_denied()` z unsafe patterns
  - Test `route_class()` dla wszystkich klas tras
  - Test `routes_from_registry()` z różnymi rejestrami
  - Test `diagnose_plan()` z poprawnymi i błędnymi planami
  - Test `diagnose_targets()` z różnymi stanami węzłów
  - Test `accept_plan()` z walidacją

- [ ] Dodanie testów dla `urirun_connector_router/target_resolution.py`
  - Test `selected_nodes_from_targets()` z różnymi inputami
  - Test `prompt_says_local()` z promptami w różnych językach
  - Test `resolve_selected_targets()` z aliasami
  - Test `filter_mesh_for_targets()` z różnymi konfiguracjami mesh
  - Test `with_local_host_routes()` z merge'owaniem tras

- [ ] Dodanie testów dla `urirun_flow/diagnostics.py`
  - Test `diagnose()` z różnymi błędami
  - Test `fit_to_environment()` z różnymi konfiguracjami
  - Test reguł playbook'a (ui-target-not-located, cdp-debugger-down, itp.)

- [ ] Dodanie testów dla `urirun_flow/recovery.py`
  - Test `normalize_error()` z różnymi typami błędów
  - Test `exception_error()` z różnymi wyjątkami
  - Test `recovery_plan()` z różnymi scenariuszami
  - Test `can_retry_step()` z różnymi kategoriami błędów
  - Test `apply_auto_remediation()` z automatycznymi remediacjami

- [ ] Dodanie testów dla `urirun/host/screen_capture.py`
  - Test `capture_screen()` z różnymi parametrami
  - Test `base64_encode()` z różnymi plikami
  - Test fallback gdy Pillow nie jest dostępny
  - Test `route()` i `bindings()` struktur

**Kryteria sukcesu:**
- Pokrycie kodu > 80% dla nowych modułów
- Wszystkie testy przechodzą w CI/CD
- Brak regresji w istniejących testach

#### 1.2 Testy integracyjne
**Status:** Brakujące
**Szacowany czas:** 2 dni

**Zadania:**
- [ ] Test integracji `urirun_connector_router` z `urirun_flow`
- [ ] Test integracji screen capture z dispatch system
- [ ] Test endpointu `/api/health` w dashboard API
- [ ] Test end-to-end flow z nowymi modułami
- [ ] Test phone scanner service management

**Kryteria sukcesu:**
- Flow planning i execution działają poprawnie z nowymi modułami
- Screen capture działa natywnie bez zewnętrznego connectora
- Dashboard API health endpoint zwraca poprawne dane

#### 1.3 Performance testing
**Status:** Brakujące
**Szacowany czas:** 1 dzień

**Zadania:**
- [ ] Benchmark routing z nowym `urirun_connector_router`
- [ ] Benchmark flow planning z nowym `urirun_flow`
- [ ] Porównanie performance przed/po refaktoryzacji
- [ ] Identyfikacja potencjalnych bottlenecków

**Kryteria sukcesu:**
- Brak regresji performance > 10%
- Dokumentacja wyników benchmarków

### Faza 2: Dokumentacja (Średni priorytet)

#### 2.1 Dokumentacja API nowych modułów
**Status:** Brakująca
**Szacowany czas:** 2 dni

**Zadania:**
- [ ] Dokumentacja `urirun_connector_router/routing.py`
  - Opis każdej funkcji publicznej
  - Przykłady użycia
  - Parametry i return values
  - Wyjątki

- [ ] Dokumentacja `urirun_connector_router/target_resolution.py`
  - Opis algorytmów resolucji celów
  - Przykłady selekcji węzłów
  - Dokumentacja języków wspieranych w promptach

- [ ] Dokumentacja `urirun_flow/diagnostics.py`
  - Opis playbook'a diagnostycznego
  - Dokumentacja reguł (failure-signature → remediation)
  - Jak dodawać nowe reguły

- [ ] Dokumentacja `urirun_flow/recovery.py`
  - Opis strategii odzyskiwania
  - Dokumentacja automatycznych remediacji
  - Jak rozszerzać recovery plan

- [ ] Dokumentacja `urirun/host/screen_capture.py`
  - Opis wbudowanej obsługi zrzutów ekranu
  - Jak używać `kvm://host/screen/query/capture`
  - Wymagania (Pillow)

#### 2.2 Aktualizacja dokumentacji użytkownika
**Status:** Częściowo zaktualizowana
**Szacowany czas:** 1 dzień

**Zadania:**
- [ ] Aktualizacja README.md z informacjami o nowych modułach
- [ ] Aktualizacja COMPONENTS.md z nową architekturą
- [ ] Dodanie sekcji o screen capture w dokumentacji
- [ ] Aktualizacja ARCHITECTURE.md z nową strukturą modułów

#### 2.3 Przykłady i tutorial
**Status:** Brakujące
**Szacowany czas:** 1 dzień

**Zadania:**
- [ ] Przykład użycia `urirun_connector_router` w skrypcie
- [ ] Przykład tworzenia custom flow z `urirun_flow`
- [ ] Tutorial: Dodawanie własnych reguł diagnostycznych
- [ ] Tutorial: Rozszerzanie recovery plan

### Faza 3: Migracja i Deprecation (Średni priorytet)

#### 3.1 Identyfikacja kodu do migracji
**Status:** Nie rozpoczęte
**Szacowany czas:** 1 dzień

**Zadania:**
- [ ] Przeszukanie codebase'u pod kątem użycia starej logiki routing
- [ ] Identyfikacja miejsc gdzie można użyć nowych modułów
- [ ] Lista plików do migracji

#### 3.2 Migracja istniejącego kodu
**Status:** Nie rozpoczęte
**Szacowany czas:** 2-3 dni

**Zadania:**
- [ ] Migracja kodu używającego starej logiki routing do `urirun_connector_router`
- [ ] Migracja kodu używającego starej logiki flow do `urirun_flow`
- [ ] Aktualizacja importów
- [ ] Testy po migracji

#### 3.3 Deprecation starego kodu
**Status:** Nie rozpoczęte
**Szacowany czas:** 1 dzień

**Zadania:**
- [ ] Oznaczenie starej logiki jako deprecated
- [ ] Dodanie warnings przy użyciu starego API
- [ ] Plan usunięcia starego kodu w przyszłej wersji

### Faza 4: Ulepszenia i Rozszerzenia (Niski priorytet)

#### 4.1 Rozszerzenie playbook'a diagnostycznego
**Status:** Nie rozpoczęte
**Szacowany czas:** Ongoing

**Zadania:**
- [ ] Dodanie reguł dla nowych typów błędów
- [ ] Dodanie reguł dla specyficznych scenariuszy
- [ ] Uczenie z field experience i dodawanie reguł

#### 4.2 Ulepszenia screen capture
**Status:** Nie rozpoczęte
**Szacowany czas:** 1-2 dni

**Zadania:**
- [ ] Dodanie wsparcia dla innych backendów (np. mss, pyautogui)
- [ ] Dodanie opcji selekcji regionu ekranu
- [ ] Dodanie wsparcia dla multiple monitors
- [ ] Optymalizacja performance

#### 4.3 Ulepszenia flow planning
**Status:** Nie rozpocęte
**Szacowany czas:** 2-3 dni

**Zadania:**
- [ ] Ulepszenie heurystycznego planowania
- [ ] Dodanie więcej intencji
- [ ] Ulepszenie integracji z LLM
- [ ] Dodanie cache'owania planów

#### 4.4 Ulepszenia recovery
**Status:** Nie rozpoczęte
**Szacowany czas:** 2 dni

**Zadania:**
- [ ] Dodanie więcej strategii odzyskiwania
- [ ] Ulepszenie automatycznych remediacji
- [ ] Dodanie learningu z poprzednich prób

### Faza 5: Monitoring i Maintenance (Ongoing)

#### 5.1 Monitoring
**Status:** Nie rozpoczęte
**Szacowany czas:** Ongoing

**Zadania:**
- [ ] Dodanie metrics dla nowych modułów
- [ ] Monitoring error rates
- [ ] Monitoring performance
- [ ] Alerting na anomalie

#### 5.2 Maintenance
**Status:** Nie rozpoczęte
**Szacowany czas:** Ongoing

**Zadania:**
- [ ] Regularne przeglądy playbook'a diagnostycznego
- [ ] Aktualizacja dokumentacji
- [ ] Refactoring code smell
- [ ] Optymalizacja performance

## Harmonogram

### Tydzień 1 (2026-07-03 - 2026-07-09)
- [ ] Testy jednostkowe dla `urirun_connector_router`
- [ ] Testy jednostkowe dla `urirun_flow/diagnostics` i `recovery`
- [ ] Testy jednostkowe dla `screen_capture`
- [ ] Rozpoczęcie dokumentacji API

### Tydzień 2 (2026-07-10 - 2026-07-16)
- [ ] Testy integracyjne
- [ ] Performance testing
- [ ] Dokończenie dokumentacji API
- [ ] Aktualizacja dokumentacji użytkownika

### Tydzień 3 (2026-07-17 - 2026-07-23)
- [ ] Identyfikacja kodu do migracji
- [ ] Migracja istniejącego kodu
- [ ] Przykłady i tutorial

### Tydzień 4 (2026-07-24 - 2026-07-30)
- [ ] Deprecation starego kodu
- [ ] Rozszerzenie playbook'a diagnostycznego
- [ ] Ulepszenia screen capture
- [ ] Setup monitoring

## Ryzyka i Mitigacje

### Ryzyko 1: Regresja w istniejącym kodzie
**Mitigacja:**
- Kompleksowe testy przed wdrożeniem
- Canary deployment
- Quick rollback plan

### Ryzyko 2: Niska adopcja nowych modułów
**Mitigacja:**
- Dokumentacja i przykłady
- Tutorial
- Migration guide
- Support dla developerów

### Ryzyko 3: Performance degradation
**Mitigacja:**
- Performance testing przed wdrożeniem
- Benchmarking
- Monitoring po wdrożeniu
- Optymalizacja hotspotów

### Ryzyko 4: Brak zasobów
**Mitigacja:**
- Priorytetyzacja zadań
- Iteracyjne podejście
- MVP dla najważniejszych funkcji

## Success Metrics

### Krótkoterminowe (1 miesiąc)
- Pokrycie testów > 80% dla nowych modułów
- Brak krytycznych bugów po wdrożeniu
- Performance bez regresji > 10%
- Dokumentacja kompletna

### Średnioterminowe (3 miesiące)
- Migracja 80% kodu do nowych modułów
- Adopcja nowych modułów przez zespół
- Zmniejszenie liczby bugów związanych z routing/flow
- Zwiększenie produktywności deweloperów

### Długoterminowe (6 miesięcy)
- Pełna migracja do nowych modułów
- Usunięcie starego kodu
- Rozszerzenie playbook'a diagnostycznego
- Ulepszenia performance i funkcjonalności

## Zasoby

### Wymagane
- 1-2 developerów dla testów i migracji
- 1 technical writer dla dokumentacji
- CI/CD infrastructure dla testów
- Monitoring infrastructure

### Opcjonalne
- Performance engineer
- UX designer dla tutoriali
- Additional developers dla ulepszeń

## Decyzje do podjęcia

1. **Kiedy usunąć stary kod?** (np. w wersji X.Y.Z)
2. **Czy dodać breaking changes w kolejnej wersji?**
3. **Jakie są priority dla poszczególnych zadań?**
4. **Czy zatrudnić dodatkowe zasoby?**
5. **Jak często aktualizować playbook diagnostyczny?**

## Kontakt

Pytania i uwagi: [Team Lead / Architect]
Review: [Code Review Team]
Approval: [Project Manager]
