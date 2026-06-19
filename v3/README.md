# urihandler v3

Universal URI dispatch using a registry tree and executor adapters.

## Route entry schema

Each route resolves to metadata:

```json
{
  "kind": "function|http|cli|shell|mqtt|artifact|process|event",
  "adapter": "executor-name",
  "config": {}
}
```

## Pipeline

```txt
URI -> descriptor -> route entry -> executor adapter -> runtime target
```

## Included examples

- local function dispatch
- HTTP service dispatch
- CLI dispatch
- shell template dispatch
- log namespace dispatch

In v3 the default route lookup is `registry[package][resource][operation]`.
The URI target is passed to the executor as receiver/context.
