# urirun — Ruby SDK

Build `urirun.bindings.v2` documents from Ruby.

```bash
ruby example/hash_connector.rb > bindings.json
urirun validate bindings.json && urirun compile bindings.json --out registry.json
```

Contract: https://docs.ifuri.com/generating-connectors.html
