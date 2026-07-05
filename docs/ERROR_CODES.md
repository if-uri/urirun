# Error Codes — the ONE canonical list

> Generated from `urirun/adapters/python/urirun_runtime/errors.py` (the single source of truth).
> Regenerate: `python urirun/docs/gen_error_codes.py`. Do not hand-edit this file.

Every failure envelope carries `error.category` (a **gRPC canonical status code**), `error.status`
(**HTTP status, RFC 9110**), `error.severity` (**syslog severity, RFC 5424**) and a stable
`error.code` (`E-<hash>` of the message, for cross-referencing a specific occurrence).
Connectors NEVER invent categories — they call `urirun.fail(msg, ...)`, and the runtime maps the
exception/errno/message to one of the categories below (`classify_error`).

| category (gRPC) | HTTP (RFC 9110) | severity (RFC 5424) | meaning |
|---|---|---|---|
| `INVALID_ARGUMENT` | 400 | error | Malformed or invalid input, regardless of system state. |
| `FAILED_PRECONDITION` | 400 | error | System is not in the state the operation requires. |
| `OUT_OF_RANGE` | 400 | error | Operation attempted past the valid range. |
| `UNAUTHENTICATED` | 401 | warning | No valid authentication credentials. |
| `PERMISSION_DENIED` | 403 | warning | Caller is not allowed to run this route (policy gate). |
| `NOT_FOUND` | 404 | error | A requested entity (file, route, binary) was not found. |
| `ALREADY_EXISTS` | 409 | warning | The entity the caller tried to create already exists. |
| `ABORTED` | 409 | error | Operation aborted, e.g. a concurrency conflict. |
| `RESOURCE_EXHAUSTED` | 429 | warning | A quota or resource limit was exhausted. |
| `CANCELLED` | 499 | notice | Operation was cancelled by the caller. |
| `DATA_LOSS` | 500 | critical | Unrecoverable data loss or corruption. |
| `UNKNOWN` | 500 | error | Unknown error; usually an unmapped exception. |
| `INTERNAL` | 500 | error | Internal invariant broken; a bug. |
| `UNIMPLEMENTED` | 501 | error | No adapter/executor implements this route. |
| `UNAVAILABLE` | 503 | error | A dependency or transport is unavailable; retry later. |
| `DEADLINE_EXCEEDED` | 504 | error | Operation timed out before completing. |

Default when unmapped: `UNKNOWN` (HTTP 500).

## Mapping sources (also in errors.py)
- **POSIX errno → category** (`_ERRNO_CATEGORY`): e.g. `ENOENT`→`NOT_FOUND`, `EACCES`→`PERMISSION_DENIED`.
- **Python exception type → category** (`_TYPE_CATEGORY`): e.g. `FileNotFoundError`→`NOT_FOUND`,
  `TimeoutError`→`DEADLINE_EXCEEDED`, `PermissionError`→`PERMISSION_DENIED`.
- **Message substrings → category** (`_MESSAGE_RULES`): last-resort heuristic.

## Discover at runtime
`error://local/<code>/query/info` (`error.uri` in every failure envelope) resolves the
human help URL. The catalog itself is `errors.CATEGORIES`.
