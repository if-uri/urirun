# urirun — Perl SDK

Build `urirun.bindings.v2` documents from Perl (JSON::PP is core, no deps).

```bash
perl example/hash_connector.pl > bindings.json
urirun validate bindings.json && urirun compile bindings.json --out registry.json
```

Contract: https://docs.ifuri.com/generating-connectors.html
