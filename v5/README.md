# urihandler v5

v5 is the simple scanner layer for existing projects.

It scans project artifacts into a flat binding document, then compiles those bindings to the existing v4 registry format.

## Scan a project

```bash
PYTHONPATH=adapters/python python -m urihandler.v5 scan v5/examples/project \
  --out /tmp/urihandler-v5.bindings.json \
  --registry-out /tmp/urihandler-v5.registry.json
```

## Compile and call

```bash
PYTHONPATH=adapters/python python -m urihandler.v5 compile /tmp/urihandler-v5.bindings.json \
  --out /tmp/urihandler-v5.registry.json

PYTHONPATH=adapters/python python -m urihandler.v5 call 'cli://local/npm/test' \
  --registry /tmp/urihandler-v5.registry.json
```

## Scan a GitHub repo

```bash
PYTHONPATH=adapters/python python -m urihandler.v5 scan-github https://github.com/tellmesh/urihandler.git \
  --out /tmp/urihandler-github.bindings.json
```

## Sources

v5 scans:

- binding manifests,
- `package.json`,
- `pyproject.toml`,
- `Makefile`,
- shell scripts,
- Python `@uri_handler(...)`,
- JavaScript `withUriRoute(...)`,
- Docker Compose labels,
- OpenAPI JSON,
- shallow GitHub checkouts.

See `v5/spec/urihandler-v5.md`.
