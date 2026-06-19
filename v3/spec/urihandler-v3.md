# urihandler v3

`urihandler v3` defines a universal URI routing model for dispatching logical URI addresses to heterogeneous execution targets such as local functions, HTTP services, CLI tools, shell commands, MQTT topics, artifacts, and other runtime adapters.

## Core principle

URI is an address, not an implementation.

Execution is resolved in three stages:

1. Parse URI to a normalized descriptor
2. Resolve descriptor against a registry tree
3. Execute through an adapter chosen by route metadata

## Canonical URI form

```txt
[package]://[target]/[resource]/[operation]/[arg1]/[arg2]/...
```

Examples:

- `device://device-01/led/set/on`
- `log://app/info/user-created`
- `service://api/user/create/basic`
- `cli://local/git/status`
- `shell://local/system/restart/nginx`
- `mqtt://broker/publish/home/kitchen/light/on`
- `artifact://build/frontend/release`

## Normalized descriptor

```json
{
  "package": "device",
  "target": "device-01",
  "segments": ["led", "set", "on"],
  "query": {},
  "fragment": null,
  "raw": "device://device-01/led/set/on",
  "normalized": "device://device-01/led/set/on"
}
```

## Translation rules

For a normalized descriptor:

```json
{
  "package": "device",
  "target": "device-01",
  "segments": ["led", "set", "on"]
}
```

translate to:

```json
{
  "route": ["device", "led", "set"],
  "args": ["on"],
  "package": "device",
  "target": "device-01",
  "resource": "led",
  "operation": "set"
}
```

Recommended dispatch contract:

```txt
registry[package][resource][operation] => route entry
```

`target` is the receiver or execution context. It is passed to the executor but
is not part of the default route lookup key. For example,
`service://api/user/create/basic` resolves route `service.user.create`, target
`api`, and args `["basic"]`.

## Route entry

A route entry describes how a URI route is executed.

```json
{
  "kind": "function",
  "adapter": "local-function",
  "config": {},
  "ref": "optional runtime reference",
  "policy": {
    "allowArgs": true,
    "allowPayload": true,
    "cacheable": true
  }
}
```

### Required fields

- `kind`: execution category
- `adapter`: executor name
- `config`: adapter-specific configuration

### Optional fields

- `ref`: local callable or symbolic reference
- `policy`: validation and execution rules
- `meta`: docs, labels, telemetry hints

## Supported kinds

Recommended built-in kinds:

- `function`
- `http`
- `cli`
- `shell`
- `mqtt`
- `artifact`
- `process`
- `event`

## Example registry tree

```json
{
  "device": {
    "led": {
      "set": {
        "kind": "function",
        "adapter": "local-function",
        "ref": "device.led.set"
      }
    }
  },
  "service": {
    "user": {
      "create": {
        "kind": "http",
        "adapter": "fetch",
        "config": {
          "method": "POST",
          "url": "http://user-service.local/api/users"
        }
      }
    }
  },
  "cli": {
    "git": {
      "status": {
        "kind": "cli",
        "adapter": "spawn",
        "config": {
          "command": ["git", "status"]
        }
      }
    }
  }
}
```

## Executor contract

Each executor receives a resolved invocation context:

```json
{
  "routeEntry": {},
  "descriptor": {},
  "translation": {},
  "target": "string",
  "args": ["string"],
  "payload": {}
}
```

## Executor selection

Dispatch algorithm:

1. Parse URI
2. Normalize URI
3. Translate to route key
4. Resolve route entry from registry tree
5. Select executor using `routeEntry.adapter` or fallback by `routeEntry.kind`
6. Execute adapter with invocation context

## `.urihandler` cache

Persistent cache stores:

- normalized URI
- translation result
- route metadata snapshot
- validation result

Runtime cache stores:

- hash -> route entry
- hash -> callable reference

Recommended key:

```txt
sha256(normalized_uri)
```

## Security guidance

- Prefer `cli` with argument arrays over raw shell strings.
- Use `shell` only with strict templates and validation.
- Never allow arbitrary module or function lookup outside explicit registry.
- Validate `kind`, `adapter`, and argument policies before execution.
- Keep service URLs or broker routes in registry config, not in free-form args.

## `log://` support

`log://` should normally resolve to `kind=function`, `kind=event`, or `kind=http` depending on architecture.

Example:

```json
{
  "log": {
    "info": {
      "user-created": {
        "kind": "function",
        "adapter": "local-function",
        "ref": "log.info.userCreated"
      }
    }
  }
}
```

with URI:

```txt
log://app/info/user-created
```

## Language portability

Portability comes from sharing:

- URI grammar
- normalized descriptor
- translation rules
- route entry schema
- executor contract

Each language only reimplements adapters and runtime resolution.
