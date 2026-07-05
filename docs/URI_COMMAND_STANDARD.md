# URI Command Standard — naming, classes, and how a manifest declares capability

The point: anyone reading a `scheme://` URI (or a connector manifest) knows, without reading
code, **what the command does, whether it mutates, what it returns, and how it can fail.**

## 1. URI shape

```
<scheme>://<host>/<resource>/<class>/<verb>[?query]
   │         │        │          │        └ the action, kebab-case (capture, dom-fill, list)
   │         │        │          └ the CLASS (see §2) — read vs mutate vs stateful
   │         │        └ the noun the action operates on (screen, input, image, windows)
   │         └ target: `host` (this node's machine) or a named node
   └ connector id (kvm, vql, vdisplay, urivision, linkedin, …)
```

Examples: `kvm://host/screen/query/capture`, `vql://host/image/query/regions`,
`kvm://host/input/command/type`, `vdisplay://host/window/query/find`.

## 2. Command CLASS — the second-to-last segment (mandatory)

The class is a **contract**, not decoration. It tells the caller and the runtime how the route
behaves. Only these four are allowed:

| class | meaning | side effects | isolation | HTTP verb feel |
|---|---|---|---|---|
| `query` | read / inspect state | NONE (pure) | in-process (`isolated=False`) | GET |
| `command` | mutate / actuate | YES | isolated subprocess (`isolated=True`) | POST |
| `session` | open/close/drive a stateful session | manages a resource lifecycle | isolated | POST |
| `event` | subscribe to / emit a stream | append-only | streaming | — |

Rules:
- A `query` route MUST be safe to call repeatedly with no observable effect. It runs in-process
  for speed. If it captures/reads only, it is a query even if it touches hardware (e.g. capture).
- A `command` route may change the world (type, click, launch, delete). It runs isolated so a
  crash cannot take the node down, and SHOULD return an `inverse` when the mutation is reversible.
- Pick the CLASS by effect, not by cost. `screen/query/capture` is a query (read-only) even
  though it is expensive; `input/command/type` is a command even though it is cheap.

## 3. Verb conventions (last segment)

kebab-case, imperative, specific. Reuse these where they fit so verbs mean the same across
connectors: `list`, `find`, `read`, `info`, `report`, `status`, `capture`, `analyze`, `diagnose`
(queries); `run`, `type`, `key`, `click`, `move`, `fill`, `navigate`, `launch`, `close`,
`install`, `publish` (commands); `ensure`, `open`, `close` (sessions).

## 4. Errors, status, severity — from existing standards, in ONE place

Do not invent error codes. Every failure envelope uses the canonical taxonomy in
[`ERROR_CODES.md`](ERROR_CODES.md) (generated from `urirun_runtime/errors.py`):

- `error.category` — a **gRPC canonical status code** (`NOT_FOUND`, `PERMISSION_DENIED`, …)
- `error.status` — **HTTP status, RFC 9110** (404, 403, …)
- `error.severity` — **syslog severity, RFC 5424** (`error`, `warning`, `critical`, …)
- `error.code` — a stable `E-<hash>` of the message for referencing one occurrence
- `error.uri` — `error://local/<code>/query/info`, resolves the human help URL

A connector calls `urirun.fail(msg, connector=…, action=…)`; the runtime classifies the
exception/errno/message into a category. Nodes and logs speak the same vocabulary.

## 5. Logs

Log lines are structured JSON events with the same severity vocabulary (RFC 5424) and carry the
`runId`, `uri`, and (on failure) `error.code` — so a log entry cross-references the envelope and
the error catalog. Emit via `log://<node>/session/command/write`; never `print()` in a handler.

## 6. Declaring capability in the manifest

`connector.manifest.json` carries prose (`summary`, `useCases`, `flowExample`). To make EACH URI
self-describing, the connector also exposes a generated `routes` capability list (from its
bindings + handler meta) via `connector_manifest()`:

```json
"routes": [
  { "uri": "vql://host/image/query/analyze", "class": "query", "verb": "analyze",
    "summary": "Analyze a screenshot into a structured VQL scene (regions + title)",
    "mutates": false, "errors": ["INVALID_ARGUMENT", "NOT_FOUND", "UNAVAILABLE"] }
]
```

- `class`/`verb` are parsed from the URI (they MUST match §2).
- `summary` comes from the handler's `meta.label`.
- `mutates` = (class == command/session).
- `errors` lists the categories this route can plausibly return (a hint for callers), drawn from
  the ONE catalog — never ad-hoc strings.

This is generated, not hand-maintained, so it can't drift from the served routes. `curictl`/the
dashboard render it so a user sees every URI's capability without reading code.

## 7. Checklist for a new route

- [ ] `resource/class/verb`, class ∈ {query, command, session, event}, verb kebab-case
- [ ] class matches effect (query = no side effects, command = mutates)
- [ ] `meta={"label": "<one-line what it does>"}` — becomes the manifest summary
- [ ] returns a urirun envelope; failures via `urirun.fail` (never a bespoke error shape)
- [ ] a reversible command returns an `inverse`
- [ ] no hardcoded host/port/path — read from env with a documented default
