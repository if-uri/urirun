# urirun — Bash SDK

Build `urirun.bindings.v2` documents from pure shell — handy because connectors
are often shell tools. Pass valid JSON fragments for the schema and argv.

```bash
bash example/hash-connector.sh > bindings.json
urirun validate bindings.json && urirun compile bindings.json --out registry.json
```

For connectors with many routes or dynamic values, prefer a typed SDK or `jq`.
Contract: https://docs.ifuri.com/generating-connectors.html
