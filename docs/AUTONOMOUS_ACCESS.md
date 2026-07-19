# Autonomous Access Acquisition Loop

<!-- docs-nav -->
📖 **Dokumentacja urirun:** [← README](../README.md) · [Architektura](ARCHITECTURE.md) · [Autonomia](AUTONOMY_ARCHITECTURE.md) · **Dostęp autonomiczny** · [Sekrety](SECRETS.md)
<!-- /docs-nav -->

## Zasada

```text
human ustanawia authority przez standing contract AQL
→ Subactor deklaruje AccessRequirement
→ urirun odkrywa trasę i metodę acquisition
→ AQL zezwala na discover/acquire/delegate/use
→ connector pozyskuje dostęp i zapisuje sekret w vault
→ runtime przekazuje handle i scope proof, nie plaintext
→ child execution grant wiąże operację z plan_hash
→ apply / verify / rollback / revoke tworzą evidence
```

Nie ma już bezwarunkowej blokady browser-assisted acquisition. Provider
`secret://browser/<acquirer>/<target>#<field>` deleguje operację do
zarejestrowanego connectora, jeżeli stojący kontrakt AQL zezwala na
`ALLOW_DISCOVER`, `ALLOW_ACQUIRE` i `ALLOW_USE`. Brak authority albo connectora
zwraca typowany blocker. Sam rdzeń nie implementuje uniwersalnego scrapera.

## Wersjonowane kontrakty

- [`aql-access-v1.schema.json`](../v2/spec/aql-access-v1.schema.json) — standing contract;
- [`access-requirement-v1.schema.json`](../v2/spec/access-requirement-v1.schema.json) — żądanie capability;
- [`aql-execution-grant-v1.schema.json`](../v2/spec/aql-execution-grant-v1.schema.json) — krótki child grant.

AQL rozróżnia:

```text
ALLOW_DISCOVER
ALLOW_ACQUIRE
ALLOW_USE
ALLOW_DELEGATE
ALLOW_ROTATE
ALLOW_REVOKE
ALLOW_MUTATE
ALLOW_SPEND
ALLOW_ACCEPT_TERMS
```

`urirun_runtime.access.evaluate_access()` dopasowuje aktora, środowisko,
providera, capability, target, działania, TTL i koszt. Funkcja
`resolve_required_access()` zwraca między innymi:

```text
READY
AUTO_ACQUIRABLE
AQL_ALLOW_REQUIRED
PROVIDER_CONSENT_REQUIRED
MFA_REQUIRED
ROOT_CREDENTIAL_MISSING
```

Nie używa ogólnego `needs_human_input`. Consent providera i MFA pozostają
typowanymi krokami URI; zgodny grant `per-env` nie wymaga ponownego pytania przy
każdym wykonaniu.

Resolver jest również wbudowanym connectorem i pojawia się w discovery
`/routes` po instalacji pakietu:

```text
access://host/requirement/query/evaluate
access://host/requirement/query/resolve
access://host/grant/command/compile
```

Pierwsza trasa ocenia standing contract, druga wybiera następny krok
acquisition, a trzecia kompiluje ograniczony grant związany z `plan_hash`.
Żadna z nich nie przyjmuje ani nie zwraca wartości sekretu.

## Developerski standing ALLOW

[`development-autonomy.json`](../examples/policies/development-autonomy.json) jest
jawnym, opt-in kontraktem do lokalnych testów automatyzacji wielu aplikacji. Ma
szeroki `*://**`, wszystkie działania access i wszystkie wspierane referencje
sekretów. Nie jest ładowany domyślnie i nie powinien być używany jako kontrakt
produkcji.

```bash
urirun run app://host/example/command/test registry.json \
  --execute --policy examples/policies/development-autonomy.json
```

W automatycznych testach connector rejestruje bridge:

```python
from urirun.runtime import secrets

def acquire(request):
    value, handle = browser_or_vault_bootstrap(request)
    return secrets.BrowserCredential(
        value=value,
        credential_handle=handle,
        provider="my-browser-connector",
        scopes=("app:test",),
        secret_value_visible=False,
    )

secrets.register_browser_acquirer("my-browser", acquire)
```

Wartość zostaje opakowana w `SecretStr` i materializowana tylko na granicy
injection. Wynik, log, JSON i LLM widzą `****`, `credential_handle`, scope i
evidence — nie wartość.

## Pełny test developerski i CI

Workflow [`examples-compatibility.yml`](../.github/workflows/examples-compatibility.yml)
odtwarza czysty układ wielu repozytoriów i uruchamia trzy profile:

```text
unit   → runtime + Twin + Domain Monitor
host   → runtime + declarative + wszystkie connectory wymagane przez przykłady
docker → runtime + contract + flow + router + Domain Monitor
```

Zależności są pobierane płytko i równolegle przez
[`checkout_ci_dependencies.py`](../scripts/checkout_ci_dependencies.py):

```bash
python scripts/checkout_ci_dependencies.py host /tmp/urirun-ci --jobs 8
python scripts/checkout_ci_dependencies.py docker /tmp/urirun-ci --jobs 8
```

Deterministyczny zestaw nie wymaga sekretów i testuje discovery, standing
ALLOW, provisioning, registry, transport HTTP, Docker oraz recovery
executor/validator/twin/teacher. Scenariusze oznaczone `external-secret`,
`hardware` albo `self-hosted` pozostają jawnie sklasyfikowane, ponieważ wymagają
odpowiednio prawdziwego providera, urządzenia albo kontrolowanego desktopu; nie
są raportowane jako wykonany test produkcyjny.

GitHub Actions:
<https://github.com/if-uri/urirun/actions/workflows/examples-compatibility.yml>.
Standardowa macierz nie kopiuje lokalnego `.env`. Live OpenRouter powinien
otrzymać `OPENROUTER_API_KEY` jako GitHub Actions secret, a flow powinien używać
referencji `getv://OPENROUTER_API_KEY` objętej `secretAllow`, nigdy plaintextu w
YAML, artefakcie lub logu.

## Connector auth conformance

Connector posiadający autoryzację powinien docelowo udostępniać:

```text
{provider}://{account}/auth/query/status
{provider}://{account}/auth/query/scopes
{provider}://{account}/auth/query/acquisition-methods
{provider}://{account}/auth/command/bootstrap
{provider}://{account}/auth/command/refresh
{provider}://{account}/auth/command/delegate
{provider}://{account}/auth/command/rotate
{provider}://{account}/auth/command/revoke
{provider}://{account}/capability/query/report
{provider}://{account}/doctor/query/report
```

`auth/query/status` zwraca wyłącznie metadane:

```json
{
  "authenticated": true,
  "credential_handle": "cred_01",
  "credential_type": "delegated_api_token",
  "scopes": ["resource.read", "resource.write:bounded-target"],
  "expires_at": "2026-07-20T10:00:00Z",
  "refreshable": true,
  "delegatable": false,
  "secret_value_visible": false,
  "evidence": {
    "provider_probe": true,
    "scope_probe": true
  }
}
```

## Granica produkcyjna

Produkcja korzysta z węższych standing contracts. System może sam pozyskiwać,
odnawiać i delegować dostęp, ale nie może sam rozszerzyć własnego AQL. Native
OAuth consent, MFA, KYB, podpis i pierwszy root of trust pozostają zewnętrznym
potwierdzeniem, a nie wielodniową ręczną listą TODO.
