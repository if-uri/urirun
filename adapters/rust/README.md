# urirun — Rust SDK

Build `urirun.bindings.v2` documents from Rust (no dependencies).

```bash
cargo run --example hash_connector > bindings.json
urirun validate bindings.json && urirun compile bindings.json --out registry.json
```

Contract: https://docs.ifuri.com/generating-connectors.html
