# urirun

SUMD - Structured Unified Markdown Descriptor for AI-aware project refactorization

## Contents

- [Metadata](#metadata)
- [Architecture](#architecture)
- [Workflows](#workflows)
- [Call Graph](#call-graph)
- [Test Contracts](#test-contracts)
- [Refactoring Analysis](#refactoring-analysis)
- [Intent](#intent)

## Metadata

- **name**: `urirun`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: Makefile, testql(1), app.doql.less, goal.yaml, package.json, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: urirun;
  version: 0.1.0;
}

workflow[name="test"] {
  trigger: manual;
  step-1: depend target=version-check;
  step-2: depend target=slim-import;
  step-3: depend target=render-single-source;
  step-4: depend target=test-js;
  step-5: depend target=test-python;
  step-6: depend target=test-c;
  step-7: depend target=conformance;
  step-8: depend target=test-v1;
  step-9: depend target=test-v2;
}

workflow[name="version-check"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -c 'import json, pathlib, sys, tomllib; root = pathlib.Path("."); versions = {"VERSION": (root / "VERSION").read_text().strip(), "package.json": json.loads((root / "package.json").read_text())["version"], "adapters/python/VERSION": (root / "adapters/python/VERSION").read_text().strip(), "adapters/python/pyproject.toml": tomllib.loads((root / "adapters/python/pyproject.toml").read_text())["project"]["version"]}; print("urirun versions:", ", ".join(f"{k}={v}" for k, v in versions.items())); sys.exit(0 if len(set(versions.values())) == 1 else 1)';
}

workflow[name="sync-versions"] {
  trigger: manual;
  step-1: run cmd=bash scripts/sync-versions.sh;
}

workflow[name="release-bump"] {
  trigger: manual;
  step-1: run cmd=bash scripts/release-bump.sh $(V);
}

workflow[name="test-js"] {
  trigger: manual;
  step-1: run cmd=$(NODE) --test adapters/js/*.test.js;
}

workflow[name="heal"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) adapters/python/scripts/heal_future_imports.py adapters/python;
}

workflow[name="test-python"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s adapters/python/tests -p 'test_*.py';
}

workflow[name="test-c"] {
  trigger: manual;
  step-1: run cmd=$(CC) -Wall -Wextra -Werror -Iadapters/c adapters/c/urirun.c adapters/c/urirun_test.c -o /tmp/urirun-c-test;
  step-2: run cmd=/tmp/urirun-c-test;
}

workflow[name="conformance"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) adapters/conformance.py;
}

workflow[name="lint"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -m ruff check adapters/python/urirun;
}

workflow[name="complexity"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) scripts/cc_gate.py;
}

workflow[name="slim-import"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) -c "import sys; sys.path.insert(0, 'adapters/python/tests'); import test_core_import_smoke as t; t.test_bare_import_urirun_stays_slim(); print('slim-core OK: import urirun stays slim')";
}

workflow[name="render-single-source"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=adapters/python $(PYTHON) -c "import sys; sys.path.insert(0, 'adapters/python/tests'); import test_widgets as t; t.test_host_does_not_redefine_widget_render_single_source(); print('widget-render OK: host consumes urirun-widgets')";
}

workflow[name="docs-check"] {
  trigger: manual;
  step-1: run cmd=docval scan docs/ --project . --no-llm -o /tmp/urirun-docval.json;
  step-2: run cmd=$(PYTHON) -c "import json,sys; n=json.load(open('/tmp/urirun-docval.json'))['summary']['chunks_invalid']; print(f'docval: {n} stale doc reference(s) (dead symbol/import/CLI)'); sys.exit(1 if n else 0)";
}

workflow[name="dup-check"] {
  trigger: manual;
  step-1: run cmd=redup check adapters/python --max-groups 15 --max-lines 108;
}

workflow[name="lint-connectors"] {
  trigger: manual;
  step-1: run cmd=$(PYTHON) scripts/lint_connectors.py $(if $(STRICT),--strict,);
}

workflow[name="restart"] {
  trigger: manual;
  step-1: depend target=restart-chat;
}

workflow[name="restart-services"] {
  trigger: manual;
  step-1: depend target=restart-chat;
  step-2: depend target=restart-scanner;
}

workflow[name="restart-chat"] {
  trigger: manual;
  step-1: run cmd=test -x "$(CHAT_SERVICE)" || { echo "missing $(CHAT_SERVICE); install urirun-service-chat in the venv"; exit 1; };
  step-2: run cmd=mkdir -p "$(LOG_DIR)";
  step-3: run cmd=PYTHONPATH="$(DEV_PYTHONPATH):$${PYTHONPATH:-}" setsid "$(CHAT_SERVICE)" restart --project "$(CURDIR)" --db "$(HOST_DB)" --host "$(CHAT_HOST)" --port "$(CHAT_PORT)" $(NODE_URL_ARGS) $(FORCE_REPLACE_ARG) >"$(LOG_DIR)/chat.log" 2>&1 < /dev/null &;
  step-4: run cmd=for i in $$(seq 1 20); do curl -fsS --max-time 2 "http://$(CHAT_HOST):$(CHAT_PORT)/health" >/dev/null 2>&1 && break || sleep 0.5; done;
  step-5: run cmd=curl -fsS --max-time 2 "http://$(CHAT_HOST):$(CHAT_PORT)/health" >/dev/null || { echo "chat failed to start; log:"; tail -40 "$(LOG_DIR)/chat.log"; exit 1; };
  step-6: run cmd=echo "chat: http://$(CHAT_HOST):$(CHAT_PORT)/";
  step-7: run cmd=echo "log:  $(LOG_DIR)/chat.log";
}

workflow[name="restart-scanner"] {
  trigger: manual;
  step-1: run cmd=test -x "$(SCANNER_SERVICE)" || { echo "missing $(SCANNER_SERVICE); install urirun-service-scanner in the venv"; exit 1; };
  step-2: run cmd=mkdir -p "$(LOG_DIR)";
  step-3: run cmd=PYTHONPATH="$(DEV_PYTHONPATH):$${PYTHONPATH:-}" setsid "$(SCANNER_SERVICE)" restart --project "$(CURDIR)" --db "$(HOST_DB)" --host "$(SCANNER_HOST)" --port "$(SCANNER_PORT)" $(NODE_URL_ARGS) $(FORCE_REPLACE_ARG) >"$(LOG_DIR)/scanner.log" 2>&1 < /dev/null &;
  step-4: run cmd=for i in $$(seq 1 20); do curl -kfsS --max-time 2 "https://127.0.0.1:$(SCANNER_PORT)/api/scanner/live" >/dev/null 2>&1 && break || sleep 0.5; done;
  step-5: run cmd=curl -kfsS --max-time 2 "https://127.0.0.1:$(SCANNER_PORT)/api/scanner/live" >/dev/null || { echo "scanner failed to start; log:"; tail -40 "$(LOG_DIR)/scanner.log"; exit 1; };
  step-6: run cmd=echo "scanner: https://$(SCANNER_HOST):$(SCANNER_PORT)/scanner";
  step-7: run cmd=echo "log:     $(LOG_DIR)/scanner.log";
}

workflow[name="service-status"] {
  trigger: manual;
  step-1: run cmd=curl -fsS --max-time 2 "http://$(CHAT_HOST):$(CHAT_PORT)/health" >/dev/null && echo "chat: up http://$(CHAT_HOST):$(CHAT_PORT)/" || echo "chat: down http://$(CHAT_HOST):$(CHAT_PORT)/";
  step-2: run cmd=curl -kfsS --max-time 2 "https://127.0.0.1:$(SCANNER_PORT)/api/scanner/live" >/dev/null && echo "scanner: up https://127.0.0.1:$(SCANNER_PORT)/scanner" || echo "scanner: down https://127.0.0.1:$(SCANNER_PORT)/scanner";
}

workflow[name="test-v1"] {
  trigger: manual;
  step-1: run cmd=printf '%s\n' '{"bindings":{"media://local/video/transcode":{"kind":"cli","adapter":"spawn","command":["ffmpeg","-i","{input}","-vf","scale={width}:{height}","{output}"],"params":{"input":{"required":true},"output":{"required":true},"width":{"default":1280},"height":{"default":720}}}}}' >/tmp/urirun-v1.bindings.json;
  step-2: run cmd=$(PYTHON) -m json.tool /tmp/urirun-v1.bindings.json >/tmp/urirun-v1-bindings.pretty.json;
  step-3: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 compile /tmp/urirun-v1.bindings.json --out /tmp/urirun-v1.registry.json --generated-at 2026-06-19T00:00:00.000Z;
  step-4: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 run 'media://local/video/transcode' --registry /tmp/urirun-v1.registry.json --payload '{"input":"a.mp4","output":"b.mp4"}' >/tmp/urirun-v1-ffmpeg.json;
  step-5: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 list /tmp/urirun-v1.registry.json --allow 'media://**';
}

workflow[name="test-v2"] {
  trigger: manual;
  step-1: run cmd=printf '%s\n' '{"bindings":{"util://local/echo/message":{"kind":"command","adapter":"argv-template","inputSchema":{"type":"object","required":["text"],"properties":{"text":{"type":"string"}},"additionalProperties":false},"argv":["python3","-c","import sys; print(sys.argv[1])","{text}"]}}}' >/tmp/urirun-v2.bindings.json;
  step-2: run cmd=$(PYTHON) -m json.tool /tmp/urirun-v2.bindings.json >/tmp/urirun-v2-bindings.pretty.json;
  step-3: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 compile /tmp/urirun-v2.bindings.json --out /tmp/urirun-v2.registry.json;
  step-4: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_mcp tools /tmp/urirun-v2.registry.json >/tmp/urirun-v2-mcp.json;
  step-5: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_mcp card /tmp/urirun-v2.registry.json >/tmp/urirun-v2-a2a.json;
  step-6: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_adopt add-python-package pip --out /tmp/urirun-v2-adopt.bindings.json;
  step-7: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 compile /tmp/urirun-v2-adopt.bindings.json --out /tmp/urirun-v2-adopt.registry.json;
  step-8: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 run 'cli://pip/pip/run' --registry /tmp/urirun-v2-adopt.registry.json --payload '{"args":["--version"]}' >/tmp/urirun-v2-adopt-run.json;
}

workflow[name="build"] {
  trigger: manual;
  step-1: run cmd=# also remove build/ : `cd adapters/python && python -m build` puts cwd on sys.path, so a;
  step-2: run cmd=# stale ./build/ dir shadows PyPA build ("'build' is a package and cannot be directly executed").;
  step-3: run cmd=rm -rf adapters/python/dist adapters/python/build;
  step-4: run cmd=cd adapters/python && $(PYTHON) -m build;
}

workflow[name="dep-health-release"] {
  trigger: manual;
  step-1: run cmd=if [ -f "$(HOME)/github/local.dev.sh" ]; then \;
  step-2: run cmd=bash "$(HOME)/github/local.dev.sh" --check-release "$(CURDIR)/adapters/python"; \;
  step-3: run cmd=else echo "local.dev.sh absent — skipping dep-health (CI)"; fi;
}

workflow[name="publish"] {
  trigger: manual;
  step-1: run cmd=cd adapters/python && $(PYTHON) -m twine upload --skip-existing dist/*;
}

workflow[name="publish-meta"] {
  trigger: manual;
  step-1: run cmd=for pkg in $(META_PKGS); do \;
  step-2: run cmd=dir="$(MONO)/$$pkg"; \;
  step-3: run cmd=if [ ! -f "$$dir/pyproject.toml" ]; then echo "SKIP $$pkg (not found at $$dir)"; continue; fi; \;
  step-4: run cmd=echo "==> build $$pkg"; \;
  step-5: run cmd=rm -rf "$$dir/dist" "$$dir/build"; \;
  step-6: run cmd=cd "$$dir" && $(PYTHON) -m build --no-isolation && cd -; \;
  step-7: run cmd=echo "==> upload $$pkg"; \;
  step-8: run cmd=cd "$$dir" && $(PYTHON) -m twine upload --skip-existing dist/* && cd -; \;
  step-9: run cmd=echo "==> done $$pkg"; \;
  step-10: run cmd=done;
}

workflow[name="release"] {
  trigger: manual;
  step-1: run cmd=v=$$(cat adapters/python/VERSION); \;
  step-2: run cmd=if git rev-parse "v$$v" >/dev/null 2>&1; then echo "tag v$$v already exists"; exit 1; fi; \;
  step-3: run cmd=remote=$$(git remote | grep -qx origin && echo origin || git remote | head -n1); \;
  step-4: run cmd=git tag -a "v$$v" -m "urirun v$$v"; \;
  step-5: run cmd=git push "$$remote" "v$$v"; \;
  step-6: run cmd=echo "pushed tag v$$v to $$remote -> release.yml builds + publishes to PyPI";
}

workflow[name="test-published"] {
  trigger: manual;
  step-1: run cmd=bash scripts/test_pypi_install.sh $(V);
}

workflow[name="test-local"] {
  trigger: manual;
  step-1: run cmd=bash scripts/test_pypi_install.sh --local;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf node_modules .pytest_cache adapters/python/tests/__pycache__ adapters/python/urirun/__pycache__ adapters/python/*.egg-info adapters/python/build adapters/python/dist __pycache__;
}

tests {
  import: .claude/worktrees/agent-a0399c478743caf79/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a0a0ba9a614b7edea/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a0dacf4adceba1a5c/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a0e74720d5977d34a/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a0e9f76259d487c94/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a125f552bb991cc01/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a16cb19f6bcff43cf/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a26bbd6b5fd565094/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a285d5cb272046d20/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a3250ebc091006594/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a355fcdf0034d6b55/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a3d6c96d88beb1f1a/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a420143cd986cd276/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a4ac133586a0f296f/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a4af4bb0b0bc74e52/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a4c45cacc62ac8e54/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a4cae63dfd3e82f2a/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a513eb4c0685260a6/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a555612c5c420a446/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a588d5ecc717985ce/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a676b7b21b802a2da/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a681343def047bf07/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a6a95aea3d461c2d5/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a6f52e50cc8ebc3a7/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a700d03e40309d531/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a756818844e8cadbb/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a89e1161d2dc35bdf/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a8c44302c9f26e55c/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a91d5f3cdae8a81d2/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a9a6b6c80216c6d8b/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-a9b73bc0826cc0050/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aa01a99b8091b084c/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aa0a23c3a1a8896d8/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aae529c468daf2c5c/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aaf101f8eea8a024f/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ab94602a1e2bc885c/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aba8a6512bbdaddc3/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-abac611f8fd81cc1e/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-abe9f054e82cbbccc/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ac2883b942d10f087/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ac4ae72a2b8247f60/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ac4faa9996be76252/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ac56434ca36fe18e3/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aca2d3730b7c75c20/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-acb5dc53933d2880d/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ad2cac505627d4e1d/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ad62d9b5c4023f40e/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-ad964c3977bac9a8a/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-add8a12ebdfe870be/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aeac5f10e27f22a14/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-aec649e904565daff/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/agent-afe22aab2f6e35dd7/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-adopt-1782729623/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-chat-ask-1782728305/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-ensure-1782728245/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-ensure2-1782729735/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-nodecli-1782730186/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-orch-offline-1782733178/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-orchestrator2-cc-1782727595/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-precond-cc-1782727504/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-scanner-svc-1782731877/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-server2-1782732626/testql-scenarios/**/*.testql.toon.yaml;
  import: .claude/worktrees/worktree-worker2-1782730191/testql-scenarios/**/*.testql.toon.yaml;
  import: testql-scenarios/**/*.testql.toon.yaml;
}

env_vars {
  keys: OPENROUTER_API_KEY, LLM_MODEL, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_MAX_RETRIES, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_CREATE_BACKUPS;
}

deploy {
  target: docker;
}

environment[name="local"] {
  runtime: docker-compose;
  env_file: .env;
  vars: LLM_MODEL, OPENROUTER_API_KEY, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}
```

## Workflows

## Call Graph

*456 nodes · 500 edges · 52 modules · CC̄=4.3*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `print` *(in scripts.test_pypi_install)* | 0 | 244 | 0 | **244** |
| `list` *(in adapters.python.urirun.host.dashboard)* | 8 | 105 | 4 | **109** |
| `send_json` *(in adapters.python.urirun_node.server)* | 1 | 44 | 12 | **56** |
| `diagnose` *(in adapters.python.scripts.dev_deps_doctor)* | 26 ⚠ | 1 | 47 | **48** |
| `print_report` *(in scripts.extraction_audit)* | 12 ⚠ | 1 | 36 | **37** |
| `_get` *(in adapters.python.urirun_node.server.NodeHandler)* | 14 ⚠ | 4 | 28 | **32** |
| `main` *(in scripts.transport_swap_proof)* | 5 | 0 | 29 | **29** |
| `verify_connector` *(in adapters.python.urirun_connectors_toolkit.connector_lint)* | 6 | 1 | 27 | **28** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/urirun
# generated in 0.27s
# nodes: 456 | edges: 500 | modules: 52
# CC̄=4.3

HUBS[20]:
  scripts.test_pypi_install.print
    CC=0  in:244  out:0  total:244
  adapters.python.urirun.host.dashboard.list
    CC=8  in:105  out:4  total:109
  adapters.python.urirun_node.server.send_json
    CC=1  in:44  out:12  total:56
  adapters.python.scripts.dev_deps_doctor.diagnose
    CC=26  in:1  out:47  total:48
  scripts.extraction_audit.print_report
    CC=12  in:1  out:36  total:37
  adapters.python.urirun_node.server.NodeHandler._get
    CC=14  in:4  out:28  total:32
  scripts.transport_swap_proof.main
    CC=5  in:0  out:29  total:29
  adapters.python.urirun_connectors_toolkit.connector_lint.verify_connector
    CC=6  in:1  out:27  total:28
  adapters.python.urirun_node.server.apply_deploy
    CC=12  in:2  out:25  total:27
  adapters.python.urirun_runtime.v2_scan.validate_binding_document
    CC=12  in:3  out:24  total:27
  adapters.python.urirun_connectors_toolkit.resolver.resolve
    CC=12  in:1  out:24  total:25
  adapters.python.urirun_connectors_toolkit.connect_catalog._cmd_show
    CC=9  in:0  out:25  total:25
  scripts.publish_release_chain.main
    CC=13  in:0  out:24  total:24
  adapters.python.urirun_twin.twin_store.environment_fingerprint
    CC=9  in:2  out:22  total:24
  adapters.python.urirun_node.server.NodeHandler._handle_enroll
    CC=11  in:0  out:22  total:22
  adapters.python.scripts.dev_deps_doctor.local_install_health
    CC=9  in:2  out:20  total:22
  adapters.python.urirun_node.transport.http_json
    CC=8  in:11  out:11  total:22
  adapters.python.urirun_node.server._announce_node_started
    CC=9  in:1  out:20  total:21
  examples.matrix.verify.main
    CC=9  in:0  out:20  total:20
  adapters.python.urirun_connectors_toolkit.connect_catalog._cmd_list
    CC=9  in:0  out:20  total:20

MODULES:
  adapters.c.urirun  [4 funcs]
    copy_token  CC=2  out:1
    is_path_end  CC=3  out:0
    memcpy  CC=1  out:1
    parse_target  CC=7  out:1
  adapters.c.urirun_test  [2 funcs]
    assert  CC=1  out:0
    main  CC=2  out:3
  adapters.conformance  [7 funcs]
    _collect_outputs  CC=4  out:8
    _compare_to_python  CC=4  out:10
    _exec_check  CC=7  out:17
    _validate_contracts  CC=4  out:8
    essential  CC=3  out:12
    main  CC=2  out:6
    python_reference  CC=1  out:5
  adapters.go.urirun  [2 funcs]
    Bindings  CC=1  out:1
    BindingsJSON  CC=1  out:4
  adapters.js  [5 funcs]
    buildInvocation  CC=1  out:2
    dispatch  CC=3  out:4
    fn  CC=2  out:1
    match  CC=2  out:1
    parseUri  CC=8  out:9
  adapters.php.Urirun  [2 funcs]
    bindings  CC=1  out:0
    bindingsJson  CC=1  out:2
  adapters.python.scripts.dev_deps_doctor  [10 funcs]
    _dist_meta  CC=6  out:7
    _site_packages  CC=4  out:4
    _source_version  CC=4  out:7
    apply_fixes  CC=6  out:7
    diagnose  CC=26  out:47
    dist_owners  CC=7  out:14
    editable_owners  CC=4  out:9
    local_dev_statuses  CC=4  out:4
    local_install_health  CC=9  out:20
    resolve  CC=5  out:2
  adapters.python.scripts.heal_future_imports  [3 funcs]
    _heal_file  CC=7  out:12
    heal  CC=6  out:7
    main  CC=5  out:9
  adapters.python.scripts.validate_connectors  [1 funcs]
    main  CC=12  out:17
  adapters.python.urirun._connector  [2 funcs]
    handler  CC=1  out:5
    manifest  CC=11  out:13
  adapters.python.urirun.host.dashboard  [1 funcs]
    list  CC=8  out:4
  adapters.python.urirun.node.doctor  [11 funcs]
    _api_id  CC=8  out:9
    _api_protocol  CC=4  out:6
    _auth_configured  CC=7  out:8
    _check_api  CC=7  out:12
    _connector_installed  CC=2  out:2
    _parse_non_http_address  CC=4  out:2
    _probe_http  CC=3  out:2
    _probe_tcp  CC=3  out:2
    _probe_url  CC=6  out:4
    check_api_node  CC=5  out:6
  adapters.python.urirun.node.event_schema  [2 funcs]
    _step_inverse  CC=5  out:1
    step_category  CC=3  out:1
  adapters.python.urirun.node.paths  [3 funcs]
    deploy_dir  CC=5  out:7
    node_state_dir  CC=1  out:3
    node_token_path  CC=1  out:1
  adapters.python.urirun.node.skill  [14 funcs]
    _episode_for  CC=8  out:6
    _memory  CC=1  out:1
    _now  CC=1  out:2
    _uri_session_append  CC=6  out:6
    _uri_session_commit  CC=6  out:10
    _uri_session_events  CC=5  out:8
    _uri_session_export  CC=5  out:6
    _uri_session_promote  CC=7  out:8
    _uri_session_replay  CC=7  out:10
    _uri_session_start  CC=8  out:11
  adapters.python.urirun_connectors_toolkit.backend_registry  [7 funcs]
    missing  CC=5  out:2
    platform_ok  CC=2  out:1
    current_platform  CC=1  out:0
    dispatch  CC=11  out:17
    have_bin  CC=1  out:1
    have_mod  CC=2  out:1
    registry_report  CC=3  out:4
  adapters.python.urirun_connectors_toolkit.connect_catalog  [19 funcs]
    _cmd_check  CC=7  out:15
    _cmd_install  CC=7  out:7
    _cmd_list  CC=9  out:20
    _cmd_show  CC=9  out:25
    _connectors  CC=2  out:3
    _diff_install  CC=8  out:11
    _diff_scalar_fields  CC=5  out:6
    _diff_set_fields  CC=7  out:7
    _emit_json  CC=1  out:2
    _execute_pip_install  CC=4  out:6
  adapters.python.urirun_connectors_toolkit.connector_lint  [45 funcs]
    _adapter_drift  CC=5  out:7
    _build_route_from_decorator  CC=9  out:8
    _call_first_str_arg  CC=3  out:1
    _changed_machine_fields  CC=5  out:1
    _cli_subcommands  CC=10  out:9
    _collect_kernel_imports  CC=11  out:4
    _compute_drift  CC=3  out:2
    _connector_assignment  CC=7  out:6
    _connector_call_target  CC=6  out:2
    _connector_objects  CC=4  out:2
  adapters.python.urirun_connectors_toolkit.connector_sdk  [3 funcs]
    connector_cli  CC=5  out:11
    emit  CC=1  out:2
    manifest_routes  CC=10  out:12
  adapters.python.urirun_connectors_toolkit.resolver  [14 funcs]
    _build_connector_entry  CC=5  out:10
    _candidate_dirs  CC=1  out:4
    _iter_connector_dirs  CC=7  out:11
    _read_manifest  CC=3  out:4
    _roots_from_args  CC=2  out:2
    _schemes_from_code  CC=9  out:10
    _schemes_from_examples  CC=5  out:5
    _schemes_from_manifest  CC=5  out:7
    _schemes_from_routes  CC=5  out:6
    _terms  CC=3  out:3
  adapters.python.urirun_node._artifacts  [5 funcs]
    _artifact_extension  CC=9  out:5
    _decode_base64_artifact  CC=6  out:6
    _write_artifact  CC=3  out:12
    compact_result_artifacts  CC=3  out:4
    materialize_base64_artifacts  CC=1  out:16
  adapters.python.urirun_node._util  [6 funcs]
    _default_max_tokens  CC=5  out:3
    _should_retry_with_fewer_tokens  CC=2  out:2
    json_load  CC=1  out:3
    json_write  CC=1  out:4
    quiet_completion  CC=8  out:7
    slug  CC=2  out:3
  adapters.python.urirun_node._version  [5 funcs]
    _vtuple  CC=5  out:7
    current_version  CC=2  out:1
    latest_version  CC=5  out:16
    version_line  CC=3  out:1
    version_status  CC=5  out:4
  adapters.python.urirun_node.client  [6 funcs]
    __init__  CC=1  out:5
    deploy  CC=9  out:8
    get  CC=1  out:3
    routes  CC=1  out:3
    run  CC=6  out:5
    run_async  CC=4  out:5
  adapters.python.urirun_node.config  [16 funcs]
    _coerce_node_url  CC=5  out:4
    _node_name_from_url  CC=4  out:2
    add_node  CC=7  out:7
    config_with_transient_node_urls  CC=9  out:12
    default_host_config  CC=3  out:3
    default_node_config  CC=2  out:1
    find_workspace_root  CC=6  out:5
    host_config_for_args  CC=1  out:4
    host_config_path  CC=5  out:8
    init_host  CC=1  out:2
  adapters.python.urirun_node.formatting  [4 funcs]
    format_nodes  CC=8  out:14
    format_routes  CC=8  out:8
    format_table  CC=6  out:15
    format_tickets  CC=6  out:10
  adapters.python.urirun_node.keyauth  [11 funcs]
    _canonical  CC=2  out:3
    _normalize  CC=2  out:4
    _replay_seen  CC=4  out:3
    add_authorized  CC=3  out:9
    authorized_keys_path  CC=1  out:1
    fingerprint  CC=2  out:9
    is_authorized  CC=2  out:4
    load_authorized  CC=5  out:7
    sign  CC=2  out:13
    verify  CC=3  out:9
  adapters.python.urirun_node.manage  [33 funcs]
    _app_count  CC=5  out:4
    _augment_local_routes  CC=5  out:7
    _classify_source  CC=6  out:4
    _compositor  CC=9  out:11
    _connector_match  CC=2  out:2
    _derive_local_routes  CC=8  out:11
    _gpu_info  CC=9  out:8
    _install_policy  CC=9  out:15
    _installed_route_owners  CC=7  out:6
    _list_installed_connectors  CC=4  out:6
  adapters.python.urirun_node.preconditions  [9 funcs]
    _acquire_item  CC=3  out:1
    _satisfied_by  CC=4  out:1
    _try_auto_satisfy  CC=6  out:5
    _uri_ready_check  CC=3  out:3
    _uri_ready_ensure  CC=3  out:4
    _uri_ready_report  CC=1  out:1
    ensure  CC=8  out:5
    report  CC=4  out:5
    status  CC=5  out:3
  adapters.python.urirun_node.server  [62 funcs]
    publish  CC=3  out:4
    _dispatch_run_response  CC=6  out:8
    _get  CC=14  out:28
    _get_errors  CC=8  out:15
    _guarded  CC=3  out:3
    _handle_adopt  CC=9  out:15
    _handle_deploy  CC=5  out:9
    _handle_enroll  CC=11  out:22
    _handle_need  CC=9  out:14
    _handle_run  CC=4  out:9
  adapters.python.urirun_node.transport  [26 funcs]
    _annotate_deploy_allow_compat  CC=11  out:9
    _api_routes_for_one  CC=8  out:9
    _build_deploy_body  CC=9  out:0
    _build_deploy_headers  CC=3  out:1
    _configured_api_id  CC=8  out:9
    _configured_api_kind  CC=4  out:6
    _configured_api_routes  CC=7  out:11
    _configured_node_kind  CC=8  out:10
    _deploy_allow_list  CC=7  out:8
    _fetch_before_health  CC=4  out:3
  adapters.python.urirun_runtime.v2_scan  [1 funcs]
    validate_binding_document  CC=12  out:24
  adapters.python.urirun_runtime.worker  [1 funcs]
    _pool_executors  CC=1  out:8
  adapters.python.urirun_scanner._shim  [2 funcs]
    _add_monorepo_connector_path  CC=3  out:5
    load_connector_module  CC=5  out:4
  adapters.python.urirun_twin.capture_preferences  [7 funcs]
    _apply_pref_to_step  CC=11  out:15
    apply_capture_preferences  CC=7  out:4
    capture_payload_has_result_reference  CC=4  out:3
    capture_preference_fingerprint  CC=6  out:5
    capture_preference_from_payload  CC=8  out:6
    capture_step_node  CC=5  out:4
    remember_capture_preferences  CC=11  out:10
  adapters.python.urirun_twin.episode  [16 funcs]
    from_dict  CC=6  out:11
    _artifacts_from_dicts  CC=2  out:1
    _episode_from_dict_core  CC=6  out:6
    _make_episode_artifacts  CC=7  out:5
    _make_episode_outcome  CC=2  out:1
    _make_episode_plan  CC=4  out:3
    _make_episode_reality  CC=2  out:1
    _outcome_from_dict  CC=4  out:4
    _plan_from_dict  CC=4  out:4
    _proofs_from_dicts  CC=2  out:1
  adapters.python.urirun_twin.experience_retrieval  [3 funcs]
    _unwrap_retrieval  CC=7  out:6
    recall_env_fingerprint  CC=6  out:4
    retrieve_experience_context  CC=5  out:3
  adapters.python.urirun_twin.planner  [9 funcs]
    _action_matrix_hints  CC=11  out:9
    _adjust_plausibility_score  CC=7  out:10
    _best_surface_hint  CC=3  out:0
    _infeasible_constraints  CC=6  out:3
    _planner_facts  CC=5  out:11
    _planner_surface_guidance  CC=6  out:10
    _plausibility_level  CC=5  out:1
    planner_context  CC=6  out:9
    plausibility  CC=4  out:5
  adapters.python.urirun_twin.reversible  [19 funcs]
    execute  CC=8  out:14
    rollback_flow  CC=6  out:7
    rescan  CC=1  out:2
    scan  CC=2  out:5
    _build_ledger_transitions  CC=5  out:12
    _inner_value  CC=5  out:6
    _inverse_uri  CC=3  out:6
    _normalize_stuck  CC=8  out:10
    _rollback_from_ledger  CC=6  out:9
    _step_kind  CC=2  out:0
  adapters.python.urirun_twin.twin_store  [14 funcs]
    __init__  CC=5  out:5
    items  CC=1  out:2
    drift  CC=3  out:2
    recall_episode  CC=9  out:8
    recall_flow_by_intent  CC=8  out:8
    remember  CC=1  out:1
    session_append  CC=3  out:5
    session_steps  CC=3  out:3
    items  CC=1  out:3
    keys  CC=1  out:3
  adapters.ts.urirun  [2 funcs]
    document  CC=1  out:0
    toJSON  CC=1  out:2
  docs.gen_error_codes  [1 funcs]
    main  CC=2  out:8
  examples.matrix.verify  [2 funcs]
    essential  CC=2  out:11
    main  CC=9  out:20
  examples.node-file-transfer.fs_transfer  [4 funcs]
    _expand_path  CC=1  out:4
    _unique_path  CC=4  out:3
    read_b64  CC=4  out:11
    write_b64  CC=8  out:18
  scripts.cc_gate  [3 funcs]
    _iter_py  CC=8  out:6
    find_offenders  CC=6  out:7
    main  CC=3  out:10
  scripts.extraction_audit  [11 funcs]
    _allowed_down  CC=6  out:3
    _resolve_from  CC=4  out:3
    _selftest  CC=7  out:18
    audit  CC=5  out:13
    classify  CC=10  out:7
    discover_modules  CC=3  out:3
    edges_in_file  CC=9  out:12
    main  CC=7  out:15
    module_name  CC=3  out:4
    print_report  CC=12  out:36
  scripts.lint_connectors  [6 funcs]
    _flags  CC=5  out:11
    _lint_exit_code  CC=13  out:13
    _print_fleet_report  CC=4  out:8
    classify  CC=5  out:1
    lint_fleet  CC=6  out:16
    main  CC=2  out:12
  scripts.publish_release_chain  [4 funcs]
    _load_packages  CC=8  out:14
    _publish_one  CC=4  out:11
    _topo  CC=2  out:5
    main  CC=13  out:24
  scripts.repin_connectors  [7 funcs]
    _pypi_write_guard  CC=3  out:3
    _repin_one  CC=7  out:11
    classify  CC=3  out:2
    find_root  CC=5  out:9
    main  CC=11  out:16
    pypi_has  CC=3  out:5
    repin_text  CC=1  out:5
  scripts.test_pypi_install  [1 funcs]
    print  CC=0  out:0
  scripts.transport_swap_proof  [2 funcs]
    main  CC=5  out:29
    timed  CC=2  out:5
  security.mesh-probe.probe  [1 funcs]
    record  CC=2  out:2

EDGES:
  docs.gen_error_codes.main → scripts.test_pypi_install.print
  security.mesh-probe.probe.record → scripts.test_pypi_install.print
  examples.matrix.verify.essential → adapters.python.urirun.host.dashboard.list
  examples.matrix.verify.main → adapters.python.urirun_runtime.v2_scan.validate_binding_document
  examples.matrix.verify.main → examples.matrix.verify.essential
  examples.matrix.verify.main → scripts.test_pypi_install.print
  examples.node-file-transfer.fs_transfer.read_b64 → examples.node-file-transfer.fs_transfer._expand_path
  examples.node-file-transfer.fs_transfer.write_b64 → examples.node-file-transfer.fs_transfer._expand_path
  examples.node-file-transfer.fs_transfer.write_b64 → examples.node-file-transfer.fs_transfer._unique_path
  scripts.transport_swap_proof.main → scripts.test_pypi_install.print
  scripts.transport_swap_proof.main → scripts.transport_swap_proof.timed
  scripts.cc_gate.find_offenders → scripts.cc_gate._iter_py
  scripts.cc_gate.main → scripts.cc_gate.find_offenders
  scripts.cc_gate.main → scripts.test_pypi_install.print
  scripts.lint_connectors.lint_fleet → adapters.python.urirun_connectors_toolkit.connector_lint.lint_connector
  scripts.lint_connectors.lint_fleet → scripts.lint_connectors.classify
  scripts.lint_connectors._print_fleet_report → scripts.test_pypi_install.print
  scripts.lint_connectors._print_fleet_report → scripts.lint_connectors._flags
  scripts.lint_connectors._lint_exit_code → scripts.test_pypi_install.print
  scripts.lint_connectors.main → scripts.lint_connectors.lint_fleet
  scripts.lint_connectors.main → scripts.lint_connectors._lint_exit_code
  scripts.lint_connectors.main → scripts.test_pypi_install.print
  scripts.lint_connectors.main → scripts.lint_connectors._print_fleet_report
  scripts.publish_release_chain._publish_one → scripts.test_pypi_install.print
  scripts.publish_release_chain.main → scripts.publish_release_chain._load_packages
  scripts.publish_release_chain.main → scripts.test_pypi_install.print
  scripts.publish_release_chain.main → scripts.publish_release_chain._topo
  scripts.extraction_audit.module_name → adapters.python.urirun.host.dashboard.list
  scripts.extraction_audit.discover_modules → scripts.extraction_audit.module_name
  scripts.extraction_audit.edges_in_file → scripts.extraction_audit._resolve_from
  scripts.extraction_audit.classify → scripts.extraction_audit._allowed_down
  scripts.extraction_audit.audit → scripts.extraction_audit.discover_modules
  scripts.extraction_audit.audit → scripts.extraction_audit.resolve_package
  scripts.extraction_audit.audit → scripts.extraction_audit.classify
  scripts.extraction_audit.audit → scripts.test_pypi_install.print
  scripts.extraction_audit.print_report → scripts.test_pypi_install.print
  scripts.extraction_audit._selftest → scripts.extraction_audit.classify
  scripts.extraction_audit._selftest → scripts.extraction_audit._resolve_from
  scripts.extraction_audit._selftest → scripts.test_pypi_install.print
  scripts.extraction_audit.main → scripts.extraction_audit.audit
  scripts.extraction_audit.main → scripts.extraction_audit.print_report
  scripts.extraction_audit.main → scripts.test_pypi_install.print
  scripts.extraction_audit.main → scripts.extraction_audit._selftest
  scripts.repin_connectors._pypi_write_guard → scripts.repin_connectors.pypi_has
  scripts.repin_connectors._pypi_write_guard → scripts.test_pypi_install.print
  scripts.repin_connectors._repin_one → scripts.repin_connectors.classify
  scripts.repin_connectors._repin_one → scripts.repin_connectors.repin_text
  scripts.repin_connectors._repin_one → scripts.test_pypi_install.print
  scripts.repin_connectors.main → scripts.repin_connectors.find_root
  scripts.repin_connectors.main → scripts.test_pypi_install.print
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/if-uri/urirun
# generated in 0.27s
# nodes: 456 | edges: 500 | modules: 52
# CC̄=4.3

HUBS[20]:
  scripts.test_pypi_install.print
    CC=0  in:244  out:0  total:244
  adapters.python.urirun.host.dashboard.list
    CC=8  in:105  out:4  total:109
  adapters.python.urirun_node.server.send_json
    CC=1  in:44  out:12  total:56
  adapters.python.scripts.dev_deps_doctor.diagnose
    CC=26  in:1  out:47  total:48
  scripts.extraction_audit.print_report
    CC=12  in:1  out:36  total:37
  adapters.python.urirun_node.server.NodeHandler._get
    CC=14  in:4  out:28  total:32
  scripts.transport_swap_proof.main
    CC=5  in:0  out:29  total:29
  adapters.python.urirun_connectors_toolkit.connector_lint.verify_connector
    CC=6  in:1  out:27  total:28
  adapters.python.urirun_node.server.apply_deploy
    CC=12  in:2  out:25  total:27
  adapters.python.urirun_runtime.v2_scan.validate_binding_document
    CC=12  in:3  out:24  total:27
  adapters.python.urirun_connectors_toolkit.resolver.resolve
    CC=12  in:1  out:24  total:25
  adapters.python.urirun_connectors_toolkit.connect_catalog._cmd_show
    CC=9  in:0  out:25  total:25
  scripts.publish_release_chain.main
    CC=13  in:0  out:24  total:24
  adapters.python.urirun_twin.twin_store.environment_fingerprint
    CC=9  in:2  out:22  total:24
  adapters.python.urirun_node.server.NodeHandler._handle_enroll
    CC=11  in:0  out:22  total:22
  adapters.python.scripts.dev_deps_doctor.local_install_health
    CC=9  in:2  out:20  total:22
  adapters.python.urirun_node.transport.http_json
    CC=8  in:11  out:11  total:22
  adapters.python.urirun_node.server._announce_node_started
    CC=9  in:1  out:20  total:21
  examples.matrix.verify.main
    CC=9  in:0  out:20  total:20
  adapters.python.urirun_connectors_toolkit.connect_catalog._cmd_list
    CC=9  in:0  out:20  total:20

MODULES:
  adapters.c.urirun  [4 funcs]
    copy_token  CC=2  out:1
    is_path_end  CC=3  out:0
    memcpy  CC=1  out:1
    parse_target  CC=7  out:1
  adapters.c.urirun_test  [2 funcs]
    assert  CC=1  out:0
    main  CC=2  out:3
  adapters.conformance  [7 funcs]
    _collect_outputs  CC=4  out:8
    _compare_to_python  CC=4  out:10
    _exec_check  CC=7  out:17
    _validate_contracts  CC=4  out:8
    essential  CC=3  out:12
    main  CC=2  out:6
    python_reference  CC=1  out:5
  adapters.go.urirun  [2 funcs]
    Bindings  CC=1  out:1
    BindingsJSON  CC=1  out:4
  adapters.js  [5 funcs]
    buildInvocation  CC=1  out:2
    dispatch  CC=3  out:4
    fn  CC=2  out:1
    match  CC=2  out:1
    parseUri  CC=8  out:9
  adapters.php.Urirun  [2 funcs]
    bindings  CC=1  out:0
    bindingsJson  CC=1  out:2
  adapters.python.scripts.dev_deps_doctor  [10 funcs]
    _dist_meta  CC=6  out:7
    _site_packages  CC=4  out:4
    _source_version  CC=4  out:7
    apply_fixes  CC=6  out:7
    diagnose  CC=26  out:47
    dist_owners  CC=7  out:14
    editable_owners  CC=4  out:9
    local_dev_statuses  CC=4  out:4
    local_install_health  CC=9  out:20
    resolve  CC=5  out:2
  adapters.python.scripts.heal_future_imports  [3 funcs]
    _heal_file  CC=7  out:12
    heal  CC=6  out:7
    main  CC=5  out:9
  adapters.python.scripts.validate_connectors  [1 funcs]
    main  CC=12  out:17
  adapters.python.urirun._connector  [2 funcs]
    handler  CC=1  out:5
    manifest  CC=11  out:13
  adapters.python.urirun.host.dashboard  [1 funcs]
    list  CC=8  out:4
  adapters.python.urirun.node.doctor  [11 funcs]
    _api_id  CC=8  out:9
    _api_protocol  CC=4  out:6
    _auth_configured  CC=7  out:8
    _check_api  CC=7  out:12
    _connector_installed  CC=2  out:2
    _parse_non_http_address  CC=4  out:2
    _probe_http  CC=3  out:2
    _probe_tcp  CC=3  out:2
    _probe_url  CC=6  out:4
    check_api_node  CC=5  out:6
  adapters.python.urirun.node.event_schema  [2 funcs]
    _step_inverse  CC=5  out:1
    step_category  CC=3  out:1
  adapters.python.urirun.node.paths  [3 funcs]
    deploy_dir  CC=5  out:7
    node_state_dir  CC=1  out:3
    node_token_path  CC=1  out:1
  adapters.python.urirun.node.skill  [14 funcs]
    _episode_for  CC=8  out:6
    _memory  CC=1  out:1
    _now  CC=1  out:2
    _uri_session_append  CC=6  out:6
    _uri_session_commit  CC=6  out:10
    _uri_session_events  CC=5  out:8
    _uri_session_export  CC=5  out:6
    _uri_session_promote  CC=7  out:8
    _uri_session_replay  CC=7  out:10
    _uri_session_start  CC=8  out:11
  adapters.python.urirun_connectors_toolkit.backend_registry  [7 funcs]
    missing  CC=5  out:2
    platform_ok  CC=2  out:1
    current_platform  CC=1  out:0
    dispatch  CC=11  out:17
    have_bin  CC=1  out:1
    have_mod  CC=2  out:1
    registry_report  CC=3  out:4
  adapters.python.urirun_connectors_toolkit.connect_catalog  [19 funcs]
    _cmd_check  CC=7  out:15
    _cmd_install  CC=7  out:7
    _cmd_list  CC=9  out:20
    _cmd_show  CC=9  out:25
    _connectors  CC=2  out:3
    _diff_install  CC=8  out:11
    _diff_scalar_fields  CC=5  out:6
    _diff_set_fields  CC=7  out:7
    _emit_json  CC=1  out:2
    _execute_pip_install  CC=4  out:6
  adapters.python.urirun_connectors_toolkit.connector_lint  [45 funcs]
    _adapter_drift  CC=5  out:7
    _build_route_from_decorator  CC=9  out:8
    _call_first_str_arg  CC=3  out:1
    _changed_machine_fields  CC=5  out:1
    _cli_subcommands  CC=10  out:9
    _collect_kernel_imports  CC=11  out:4
    _compute_drift  CC=3  out:2
    _connector_assignment  CC=7  out:6
    _connector_call_target  CC=6  out:2
    _connector_objects  CC=4  out:2
  adapters.python.urirun_connectors_toolkit.connector_sdk  [3 funcs]
    connector_cli  CC=5  out:11
    emit  CC=1  out:2
    manifest_routes  CC=10  out:12
  adapters.python.urirun_connectors_toolkit.resolver  [14 funcs]
    _build_connector_entry  CC=5  out:10
    _candidate_dirs  CC=1  out:4
    _iter_connector_dirs  CC=7  out:11
    _read_manifest  CC=3  out:4
    _roots_from_args  CC=2  out:2
    _schemes_from_code  CC=9  out:10
    _schemes_from_examples  CC=5  out:5
    _schemes_from_manifest  CC=5  out:7
    _schemes_from_routes  CC=5  out:6
    _terms  CC=3  out:3
  adapters.python.urirun_node._artifacts  [5 funcs]
    _artifact_extension  CC=9  out:5
    _decode_base64_artifact  CC=6  out:6
    _write_artifact  CC=3  out:12
    compact_result_artifacts  CC=3  out:4
    materialize_base64_artifacts  CC=1  out:16
  adapters.python.urirun_node._util  [6 funcs]
    _default_max_tokens  CC=5  out:3
    _should_retry_with_fewer_tokens  CC=2  out:2
    json_load  CC=1  out:3
    json_write  CC=1  out:4
    quiet_completion  CC=8  out:7
    slug  CC=2  out:3
  adapters.python.urirun_node._version  [5 funcs]
    _vtuple  CC=5  out:7
    current_version  CC=2  out:1
    latest_version  CC=5  out:16
    version_line  CC=3  out:1
    version_status  CC=5  out:4
  adapters.python.urirun_node.client  [6 funcs]
    __init__  CC=1  out:5
    deploy  CC=9  out:8
    get  CC=1  out:3
    routes  CC=1  out:3
    run  CC=6  out:5
    run_async  CC=4  out:5
  adapters.python.urirun_node.config  [16 funcs]
    _coerce_node_url  CC=5  out:4
    _node_name_from_url  CC=4  out:2
    add_node  CC=7  out:7
    config_with_transient_node_urls  CC=9  out:12
    default_host_config  CC=3  out:3
    default_node_config  CC=2  out:1
    find_workspace_root  CC=6  out:5
    host_config_for_args  CC=1  out:4
    host_config_path  CC=5  out:8
    init_host  CC=1  out:2
  adapters.python.urirun_node.formatting  [4 funcs]
    format_nodes  CC=8  out:14
    format_routes  CC=8  out:8
    format_table  CC=6  out:15
    format_tickets  CC=6  out:10
  adapters.python.urirun_node.keyauth  [11 funcs]
    _canonical  CC=2  out:3
    _normalize  CC=2  out:4
    _replay_seen  CC=4  out:3
    add_authorized  CC=3  out:9
    authorized_keys_path  CC=1  out:1
    fingerprint  CC=2  out:9
    is_authorized  CC=2  out:4
    load_authorized  CC=5  out:7
    sign  CC=2  out:13
    verify  CC=3  out:9
  adapters.python.urirun_node.manage  [33 funcs]
    _app_count  CC=5  out:4
    _augment_local_routes  CC=5  out:7
    _classify_source  CC=6  out:4
    _compositor  CC=9  out:11
    _connector_match  CC=2  out:2
    _derive_local_routes  CC=8  out:11
    _gpu_info  CC=9  out:8
    _install_policy  CC=9  out:15
    _installed_route_owners  CC=7  out:6
    _list_installed_connectors  CC=4  out:6
  adapters.python.urirun_node.preconditions  [9 funcs]
    _acquire_item  CC=3  out:1
    _satisfied_by  CC=4  out:1
    _try_auto_satisfy  CC=6  out:5
    _uri_ready_check  CC=3  out:3
    _uri_ready_ensure  CC=3  out:4
    _uri_ready_report  CC=1  out:1
    ensure  CC=8  out:5
    report  CC=4  out:5
    status  CC=5  out:3
  adapters.python.urirun_node.server  [62 funcs]
    publish  CC=3  out:4
    _dispatch_run_response  CC=6  out:8
    _get  CC=14  out:28
    _get_errors  CC=8  out:15
    _guarded  CC=3  out:3
    _handle_adopt  CC=9  out:15
    _handle_deploy  CC=5  out:9
    _handle_enroll  CC=11  out:22
    _handle_need  CC=9  out:14
    _handle_run  CC=4  out:9
  adapters.python.urirun_node.transport  [26 funcs]
    _annotate_deploy_allow_compat  CC=11  out:9
    _api_routes_for_one  CC=8  out:9
    _build_deploy_body  CC=9  out:0
    _build_deploy_headers  CC=3  out:1
    _configured_api_id  CC=8  out:9
    _configured_api_kind  CC=4  out:6
    _configured_api_routes  CC=7  out:11
    _configured_node_kind  CC=8  out:10
    _deploy_allow_list  CC=7  out:8
    _fetch_before_health  CC=4  out:3
  adapters.python.urirun_runtime.v2_scan  [1 funcs]
    validate_binding_document  CC=12  out:24
  adapters.python.urirun_runtime.worker  [1 funcs]
    _pool_executors  CC=1  out:8
  adapters.python.urirun_scanner._shim  [2 funcs]
    _add_monorepo_connector_path  CC=3  out:5
    load_connector_module  CC=5  out:4
  adapters.python.urirun_twin.capture_preferences  [7 funcs]
    _apply_pref_to_step  CC=11  out:15
    apply_capture_preferences  CC=7  out:4
    capture_payload_has_result_reference  CC=4  out:3
    capture_preference_fingerprint  CC=6  out:5
    capture_preference_from_payload  CC=8  out:6
    capture_step_node  CC=5  out:4
    remember_capture_preferences  CC=11  out:10
  adapters.python.urirun_twin.episode  [16 funcs]
    from_dict  CC=6  out:11
    _artifacts_from_dicts  CC=2  out:1
    _episode_from_dict_core  CC=6  out:6
    _make_episode_artifacts  CC=7  out:5
    _make_episode_outcome  CC=2  out:1
    _make_episode_plan  CC=4  out:3
    _make_episode_reality  CC=2  out:1
    _outcome_from_dict  CC=4  out:4
    _plan_from_dict  CC=4  out:4
    _proofs_from_dicts  CC=2  out:1
  adapters.python.urirun_twin.experience_retrieval  [3 funcs]
    _unwrap_retrieval  CC=7  out:6
    recall_env_fingerprint  CC=6  out:4
    retrieve_experience_context  CC=5  out:3
  adapters.python.urirun_twin.planner  [9 funcs]
    _action_matrix_hints  CC=11  out:9
    _adjust_plausibility_score  CC=7  out:10
    _best_surface_hint  CC=3  out:0
    _infeasible_constraints  CC=6  out:3
    _planner_facts  CC=5  out:11
    _planner_surface_guidance  CC=6  out:10
    _plausibility_level  CC=5  out:1
    planner_context  CC=6  out:9
    plausibility  CC=4  out:5
  adapters.python.urirun_twin.reversible  [19 funcs]
    execute  CC=8  out:14
    rollback_flow  CC=6  out:7
    rescan  CC=1  out:2
    scan  CC=2  out:5
    _build_ledger_transitions  CC=5  out:12
    _inner_value  CC=5  out:6
    _inverse_uri  CC=3  out:6
    _normalize_stuck  CC=8  out:10
    _rollback_from_ledger  CC=6  out:9
    _step_kind  CC=2  out:0
  adapters.python.urirun_twin.twin_store  [14 funcs]
    __init__  CC=5  out:5
    items  CC=1  out:2
    drift  CC=3  out:2
    recall_episode  CC=9  out:8
    recall_flow_by_intent  CC=8  out:8
    remember  CC=1  out:1
    session_append  CC=3  out:5
    session_steps  CC=3  out:3
    items  CC=1  out:3
    keys  CC=1  out:3
  adapters.ts.urirun  [2 funcs]
    document  CC=1  out:0
    toJSON  CC=1  out:2
  docs.gen_error_codes  [1 funcs]
    main  CC=2  out:8
  examples.matrix.verify  [2 funcs]
    essential  CC=2  out:11
    main  CC=9  out:20
  examples.node-file-transfer.fs_transfer  [4 funcs]
    _expand_path  CC=1  out:4
    _unique_path  CC=4  out:3
    read_b64  CC=4  out:11
    write_b64  CC=8  out:18
  scripts.cc_gate  [3 funcs]
    _iter_py  CC=8  out:6
    find_offenders  CC=6  out:7
    main  CC=3  out:10
  scripts.extraction_audit  [11 funcs]
    _allowed_down  CC=6  out:3
    _resolve_from  CC=4  out:3
    _selftest  CC=7  out:18
    audit  CC=5  out:13
    classify  CC=10  out:7
    discover_modules  CC=3  out:3
    edges_in_file  CC=9  out:12
    main  CC=7  out:15
    module_name  CC=3  out:4
    print_report  CC=12  out:36
  scripts.lint_connectors  [6 funcs]
    _flags  CC=5  out:11
    _lint_exit_code  CC=13  out:13
    _print_fleet_report  CC=4  out:8
    classify  CC=5  out:1
    lint_fleet  CC=6  out:16
    main  CC=2  out:12
  scripts.publish_release_chain  [4 funcs]
    _load_packages  CC=8  out:14
    _publish_one  CC=4  out:11
    _topo  CC=2  out:5
    main  CC=13  out:24
  scripts.repin_connectors  [7 funcs]
    _pypi_write_guard  CC=3  out:3
    _repin_one  CC=7  out:11
    classify  CC=3  out:2
    find_root  CC=5  out:9
    main  CC=11  out:16
    pypi_has  CC=3  out:5
    repin_text  CC=1  out:5
  scripts.test_pypi_install  [1 funcs]
    print  CC=0  out:0
  scripts.transport_swap_proof  [2 funcs]
    main  CC=5  out:29
    timed  CC=2  out:5
  security.mesh-probe.probe  [1 funcs]
    record  CC=2  out:2

EDGES:
  docs.gen_error_codes.main → scripts.test_pypi_install.print
  security.mesh-probe.probe.record → scripts.test_pypi_install.print
  examples.matrix.verify.essential → adapters.python.urirun.host.dashboard.list
  examples.matrix.verify.main → adapters.python.urirun_runtime.v2_scan.validate_binding_document
  examples.matrix.verify.main → examples.matrix.verify.essential
  examples.matrix.verify.main → scripts.test_pypi_install.print
  examples.node-file-transfer.fs_transfer.read_b64 → examples.node-file-transfer.fs_transfer._expand_path
  examples.node-file-transfer.fs_transfer.write_b64 → examples.node-file-transfer.fs_transfer._expand_path
  examples.node-file-transfer.fs_transfer.write_b64 → examples.node-file-transfer.fs_transfer._unique_path
  scripts.transport_swap_proof.main → scripts.test_pypi_install.print
  scripts.transport_swap_proof.main → scripts.transport_swap_proof.timed
  scripts.cc_gate.find_offenders → scripts.cc_gate._iter_py
  scripts.cc_gate.main → scripts.cc_gate.find_offenders
  scripts.cc_gate.main → scripts.test_pypi_install.print
  scripts.lint_connectors.lint_fleet → adapters.python.urirun_connectors_toolkit.connector_lint.lint_connector
  scripts.lint_connectors.lint_fleet → scripts.lint_connectors.classify
  scripts.lint_connectors._print_fleet_report → scripts.test_pypi_install.print
  scripts.lint_connectors._print_fleet_report → scripts.lint_connectors._flags
  scripts.lint_connectors._lint_exit_code → scripts.test_pypi_install.print
  scripts.lint_connectors.main → scripts.lint_connectors.lint_fleet
  scripts.lint_connectors.main → scripts.lint_connectors._lint_exit_code
  scripts.lint_connectors.main → scripts.test_pypi_install.print
  scripts.lint_connectors.main → scripts.lint_connectors._print_fleet_report
  scripts.publish_release_chain._publish_one → scripts.test_pypi_install.print
  scripts.publish_release_chain.main → scripts.publish_release_chain._load_packages
  scripts.publish_release_chain.main → scripts.test_pypi_install.print
  scripts.publish_release_chain.main → scripts.publish_release_chain._topo
  scripts.extraction_audit.module_name → adapters.python.urirun.host.dashboard.list
  scripts.extraction_audit.discover_modules → scripts.extraction_audit.module_name
  scripts.extraction_audit.edges_in_file → scripts.extraction_audit._resolve_from
  scripts.extraction_audit.classify → scripts.extraction_audit._allowed_down
  scripts.extraction_audit.audit → scripts.extraction_audit.discover_modules
  scripts.extraction_audit.audit → scripts.extraction_audit.resolve_package
  scripts.extraction_audit.audit → scripts.extraction_audit.classify
  scripts.extraction_audit.audit → scripts.test_pypi_install.print
  scripts.extraction_audit.print_report → scripts.test_pypi_install.print
  scripts.extraction_audit._selftest → scripts.extraction_audit.classify
  scripts.extraction_audit._selftest → scripts.extraction_audit._resolve_from
  scripts.extraction_audit._selftest → scripts.test_pypi_install.print
  scripts.extraction_audit.main → scripts.extraction_audit.audit
  scripts.extraction_audit.main → scripts.extraction_audit.print_report
  scripts.extraction_audit.main → scripts.test_pypi_install.print
  scripts.extraction_audit.main → scripts.extraction_audit._selftest
  scripts.repin_connectors._pypi_write_guard → scripts.repin_connectors.pypi_has
  scripts.repin_connectors._pypi_write_guard → scripts.test_pypi_install.print
  scripts.repin_connectors._repin_one → scripts.repin_connectors.classify
  scripts.repin_connectors._repin_one → scripts.repin_connectors.repin_text
  scripts.repin_connectors._repin_one → scripts.test_pypi_install.print
  scripts.repin_connectors.main → scripts.repin_connectors.find_root
  scripts.repin_connectors.main → scripts.test_pypi_install.print
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 318f 50737L | python:235,json:18,shell:18,yaml:5,txt:5,javascript:5,go:4,csharp:4,yml:2,java:2,typescript:2,perl:2,toml:2,rust:2,php:2,ruby:2,c:1,cpp:1 | 2026-07-05
# generated in 0.20s
# CC̅=4.3 | critical:2/2768 | dups:0 | cycles:0

HEALTH[2]:
  🟡 CC    diagnose CC=26 (limit:15)
  🟡 CC    api_twin_state CC=16 (limit:15)

REFACTOR[1]:
  1. split 2 high-CC methods  (CC>15)

PIPELINES[919]:
  [1] Src [main]: main → print
      PURITY: 100% pure
  [2] Src [http]: http
      PURITY: 100% pure
  [3] Src [_attacker_key]: _attacker_key
      PURITY: 100% pure
  [4] Src [record]: record → print
      PURITY: 100% pure
  [5] Src [f]: f
      PURITY: 100% pure
  [6] Src [main]: main → validate_binding_document → expand_bindings → expand_binding
      PURITY: 100% pure
  [7] Src [read_b64]: read_b64 → _expand_path
      PURITY: 100% pure
  [8] Src [write_b64]: write_b64 → _expand_path
      PURITY: 100% pure
  [9] Src [ping]: ping
      PURITY: 100% pure
  [10] Src [main]: main → print
      PURITY: 100% pure
  [11] Src [main]: main → find_offenders → _iter_py
      PURITY: 100% pure
  [12] Src [main]: main → lint_fleet → lint_connector → _lint_gather_data → ...(4 more)
      PURITY: 100% pure
  [13] Src [main]: main → _load_packages
      PURITY: 100% pure
  [14] Src [main]: main → audit → discover_modules → module_name → ...(4 more)
      PURITY: 100% pure
  [15] Src [main]: main → find_root
      PURITY: 100% pure
  [16] Src [main]: main → _collect_outputs → python_reference
      PURITY: 100% pure
  [17] Src [result]: result
      PURITY: 100% pure
  [18] Src [path]: path
      PURITY: 100% pure
  [19] Src [segments]: segments
      PURITY: 100% pure
  [20] Src [descriptor]: descriptor
      PURITY: 100% pure
  [21] Src [invocation]: invocation
      PURITY: 100% pure
  [22] Src [mod]: mod
      PURITY: 100% pure
  [23] Src [command]: command
      PURITY: 100% pure
  [24] Src [bindingsJson]: bindingsJson
      PURITY: 100% pure
  [25] Src [main]: main
      PURITY: 100% pure
  [26] Src [Target]: Target
      PURITY: 100% pure
  [27] Src [Command]: Command
      PURITY: 100% pure
  [28] Src [BindingsJSON]: BindingsJSON → Bindings
      PURITY: 100% pure
  [29] Src [main]: main
      PURITY: 100% pure
  [30] Src [toJSON]: toJSON → document
      PURITY: 100% pure
  [31] Src [connector]: connector
      PURITY: 100% pure
  [32] Src [c]: c
      PURITY: 100% pure
  [33] Src [main]: main
      PURITY: 100% pure
  [34] Src [new]: new
      PURITY: 100% pure
  [35] Src [target]: target
      PURITY: 100% pure
  [36] Src [command]: command
      PURITY: 100% pure
  [37] Src [bindings_json]: bindings_json
      PURITY: 100% pure
  [38] Src [command]: command
      PURITY: 100% pure
  [39] Src [bindingsJson]: bindingsJson → bindings
      PURITY: 100% pure
  [40] Src [main]: main → assert
      PURITY: 100% pure
  [41] Src [parse_target]: parse_target → copy_token → memcpy → is_path_end
      PURITY: 100% pure
  [42] Src [load_connector_module]: load_connector_module → _add_monorepo_connector_path
      PURITY: 100% pure
  [43] Src [install_policy]: install_policy → _install_policy
      PURITY: 100% pure
  [44] Src [package_install]: package_install → _install_policy
      PURITY: 100% pure
  [45] Src [connector_install]: connector_install → _classify_source
      PURITY: 100% pure
  [46] Src [connector_discover]: connector_discover → _scan_local_connectors → _read_connector_manifest → _read_tellmesh_manifest
      PURITY: 100% pure
  [47] Src [registry_installed]: registry_installed
      PURITY: 100% pure
  [48] Src [capability_check]: capability_check → _scope_to_scheme → _scheme_of
      PURITY: 100% pure
  [49] Src [package_list]: package_list → _pip
      PURITY: 100% pure
  [50] Src [runtime_info]: runtime_info
      PURITY: 100% pure

LAYERS:
  scripts/                        CC̄=5.2    ←in:181  →out:2
  │ extraction_audit           364L  2C   12m  CC=12     ←0
  │ test_pypi_install.sh       281L  0C    2m  CC=0.0    ←40
  │ repin_connectors           176L  0C    7m  CC=11     ←0
  │ lint_connectors            140L  0C    6m  CC=13     ←0
  │ transport_swap_proof       118L  0C    5m  CC=6      ←0
  │ publish_release_chain      112L  0C    5m  CC=13     ←0
  │ cc_gate                     86L  0C    3m  CC=8      ←0
  │ deploy_lib_connector.sh     53L  0C    0m  CC=0.0    ←0
  │ dev-install.sh              53L  0C    0m  CC=0.0    ←0
  │ sync-sibling-floors.sh      44L  0C    0m  CC=0.0    ←0
  │ redeploy_all.sh             38L  0C    0m  CC=0.0    ←0
  │ release-bump.sh             29L  0C    0m  CC=0.0    ←0
  │ node-verbose.sh             29L  0C    0m  CC=0.0    ←0
  │ sync-versions.sh            25L  0C    0m  CC=0.0    ←0
  │
  xlang/                          CC̄=4.6    ←in:0  →out:8  !! split
  │ gate.go                    285L  1C   16m  CC=13     ←1
  │ contracts.json             229L  0C    0m  CC=0.0    ←0
  │ driver                      89L  0C    3m  CC=8      ←0
  │ contracts.kvm.json          71L  0C    0m  CC=0.0    ←0
  │ peer                        64L  0C    2m  CC=8      ←0
  │ emit_contracts              37L  0C    1m  CC=3      ←0
  │ run_wires.sh                35L  0C    0m  CC=0.0    ←0
  │ run3.sh                     35L  0C    0m  CC=0.0    ←0
  │ run_driver.sh               35L  0C    0m  CC=0.0    ←0
  │ placeholder_test.go         10L  0C    1m  CC=2      ←0
  │ peer.mjs                     0L  0C   25m  CC=12     ←0
  │ gate                         0L  0C    1m  CC=3      ←0
  │ gate.mjs                     0L  0C    9m  CC=12     ←0
  │
  adapters/                       CC̄=4.2    ←in:18  →out:12  !! split
  │ !! dashboard.js              3033L  0C  452m  CC=14     ←45
  │ !! scanner_bridge            1548L  0C    0m  CC=0.0    ←0
  │ !! host_dashboard            1446L  0C   70m  CC=11     ←2
  │ !! document_sync             1422L  0C    0m  CC=0.0    ←0
  │ !! chat_orchestrator         1307L  1C   54m  CC=14     ←0
  │ !! v2                        1288L  3C   81m  CC=11     ←7
  │ !! server                    1243L  3C   81m  CC=14     ←3
  │ !! node_cli                   933L  0C   60m  CC=12     ←1
  │ !! object_registry            876L  0C   45m  CC=12     ←1
  │ !! connector_lint             786L  0C   48m  CC=11     ←1
  │ !! cli                        748L  0C   13m  CC=2      ←1
  │ !! _registry                  723L  0C   47m  CC=11     ←1
  │ !! twin_bridge                686L  0C   33m  CC=16     ←1
  │ !! scanner.js                 681L  0C  121m  CC=14     ←0
  │ !! _scan                      675L  0C   41m  CC=12     ←0
  │ !! v2_cmds                    671L  0C   42m  CC=12     ←1
  │ !! _runtime                   655L  1C   39m  CC=11     ←2
  │ !! manage                     608L  0C   37m  CC=11     ←0
  │ !! errors                     580L  0C   33m  CC=10     ←1
  │ !! transport                  570L  0C   28m  CC=12     ←3
  │ !! preconditions              559L  1C   28m  CC=11     ←0
  │ !! client                     558L  1C   35m  CC=12     ←2
  │ !! host_db                    527L  0C   33m  CC=11     ←0
  │ !! v1                         510L  0C   34m  CC=11     ←4
  │ artifacts_admin            495L  0C    0m  CC=0.0    ←0
  │ codegen                    481L  0C   26m  CC=10     ←0
  │ document_metadata          471L  0C    0m  CC=0.0    ←0
  │ service_control            462L  0C   23m  CC=11     ←0
  │ __init__                   460L  0C   34m  CC=9      ←2
  │ _dashboard_post_handlers   456L  0C   25m  CC=13     ←1
  │ discovery                  415L  0C   35m  CC=12     ←2
  │ connector_scaffold         413L  0C   11m  CC=3      ←0
  │ v2_scan                    411L  0C   21m  CC=12     ←4
  │ reversible                 406L  8C   28m  CC=10     ←3
  │ twin_store                 401L  3C   45m  CC=9      ←0
  │ fs_transfer                392L  0C   19m  CC=11     ←5
  │ task_planner               376L  2C   16m  CC=12     ←0
  │ host_integrations          374L  0C   16m  CC=8      ←0
  │ task_cli                   367L  0C   29m  CC=10     ←0
  │ document_sync_chat         361L  0C    9m  CC=12     ←0
  │ _connector                 354L  1C   23m  CC=12     ←10
  │ dashboard_api              350L  0C   32m  CC=8      ←4
  │ node_dispatch              343L  0C   10m  CC=13     ←6
  │ scanner_service            342L  0C    0m  CC=0.0    ←0
  │ cdp                        339L  1C   24m  CC=8      ←0
  │ worker                     321L  3C   28m  CC=10     ←2
  │ _orchestrator_offline      311L  0C   12m  CC=9      ←1
  │ adopt_pack                 298L  0C   20m  CC=11     ←0
  │ planfile_adapter           290L  1C   27m  CC=9      ←0
  │ mesh                       279L  0C    4m  CC=4      ←0
  │ node_api                   278L  0C   14m  CC=10     ←0
  │ connector_admin            267L  0C   15m  CC=12     ←1
  │ node_types                 265L  0C    8m  CC=8      ←2
  │ secrets                    263L  1C   18m  CC=9      ←1
  │ connect_catalog            260L  0C   19m  CC=10     ←0
  │ node_health                260L  0C   15m  CC=9      ←0
  │ _dashboard_get_handlers    252L  0C   15m  CC=11     ←1
  │ screen_capability          251L  0C   15m  CC=10     ←1
  │ episode                    249L  6C   17m  CC=7      ←4
  │ !! dev_deps_doctor            246L  0C   14m  CC=26     ←0
  │ v2_mcp                     239L  0C   12m  CC=9      ←0
  │ dispatch                   236L  0C   10m  CC=12     ←1
  │ config                     226L  0C   17m  CC=9      ←4
  │ preconditions              224L  1C   15m  CC=8      ←0
  │ v2_grpc                    221L  0C   14m  CC=6      ←0
  │ v2_adopt                   213L  0C   13m  CC=7      ←0
  │ discovery                  202L  0C    9m  CC=9      ←0
  │ resolver                   200L  0C   14m  CC=12     ←0
  │ compat                     199L  0C    6m  CC=10     ←0
  │ _chat_attachments          193L  0C   13m  CC=8      ←1
  │ testing                    189L  0C    9m  CC=9      ←0
  │ dispatch_protocol          184L  0C    8m  CC=10     ←1
  │ keyauth                    182L  0C   16m  CC=6      ←0
  │ planner                    181L  0C    9m  CC=11     ←0
  │ dashboard_http             181L  0C   11m  CC=12     ←3
  │ new-connector.sh           168L  0C    1m  CC=0.0    ←0
  │ conformance                167L  0C    7m  CC=7      ←0
  │ android_node               167L  0C    8m  CC=12     ←3
  │ v2_service                 166L  0C    6m  CC=10     ←0
  │ capability                 160L  0C    6m  CC=12     ←0
  │ _node_builder              153L  0C   10m  CC=9      ←1
  │ scanner_net                153L  0C    0m  CC=0.0    ←0
  │ agent                      151L  0C    6m  CC=10     ←0
  │ daemon                     149L  0C    9m  CC=9      ←0
  │ decision_loop              143L  0C    7m  CC=11     ←2
  │ _node_auth                 140L  0C   11m  CC=12     ←1
  │ scheduler                  135L  0C    6m  CC=4      ←0
  │ backend_registry           129L  2C   10m  CC=11     ←0
  │ connector_sdk              126L  0C    4m  CC=10     ←2
  │ contracts                  119L  0C    8m  CC=5      ←0
  │ experience_retrieval       116L  0C    5m  CC=9      ←0
  │ introspect                 112L  0C    4m  CC=9      ←1
  │ _artifacts                 111L  0C    5m  CC=9      ←2
  │ _host_port                 111L  0C    7m  CC=1      ←1
  │ capture_preferences        108L  0C    7m  CC=11     ←0
  │ scanner_chat               108L  0C    1m  CC=10     ←0
  │ work_runs                  105L  0C    7m  CC=8      ←2
  │ exec                       104L  0C    3m  CC=11     ←0
  │ _shell_qr                  104L  0C    5m  CC=9      ←2
  │ pyproject.toml              98L  0C    0m  CC=0.0    ←0
  │ tree                        91L  0C    4m  CC=11     ←0
  │ progress                    89L  1C   11m  CC=3      ←0
  │ screen_capture              88L  0C    6m  CC=4      ←0
  │ heal_future_imports         84L  0C    3m  CC=7      ←0
  │ urirun.go                   80L  3C    5m  CC=3      ←0
  │ formatting                  80L  0C    4m  CC=8      ←2
  │ _util                       78L  0C    8m  CC=8      ←5
  │ __init__                    76L  2C    1m  CC=1      ←0
  │ _version                    76L  0C    5m  CC=5      ←1
  │ Urirun.php                  73L  1C    5m  CC=3      ←0
  │ project.assets.json         71L  0C    0m  CC=0.0    ←0
  │ urirun-connector.csproj.nuget.dgspec.json    66L  0C    0m  CC=0.0    ←0
  │ html_templates              57L  0C    1m  CC=3      ←0
  │ validate_connectors         55L  0C    1m  CC=12     ←0
  │ index.test.js               52L  0C    1m  CC=1      ←0
  │ Urirun.pm                   47L  0C    4m  CC=0.0    ←1
  │ urifix_bridge               45L  0C    1m  CC=12     ←1
  │ urirun.ts                   41L  2C    4m  CC=4      ←0
  │ domain_monitor              41L  0C    2m  CC=4      ←0
  │ lib.rs                      39L  1C    4m  CC=1      ←0
  │ urirun.rb                   39L  1C    4m  CC=4      ←0
  │ Urirun.java                 38L  1C    3m  CC=1      ←1
  │ _shim                       35L  0C    2m  CC=5      ←0
  │ index.js                    33L  0C   11m  CC=8      ←11
  │ Urirun.cs                   32L  1C    3m  CC=1      ←0
  │ cdp                         31L  0C    0m  CC=0.0    ←0
  │ main.go                     24L  0C    1m  CC=1      ←0
  │ urirun-connector.deps.json    23L  0C    0m  CC=0.0    ←0
  │ _chat_message               22L  0C    1m  CC=3      ←4
  │ urirun-connector.AssemblyInfo.cs    22L  0C    0m  CC=0.0    ←0
  │ widgets                     21L  1C    3m  CC=2      ←0
  │ local.dev.txt               20L  0C    0m  CC=0.0    ←0
  │ urirun_test.c               18L  0C    2m  CC=2      ←0
  │ urirun.sh                   17L  0C    2m  CC=0.0    ←0
  │ routing                     17L  0C    0m  CC=0.0    ←0
  │ urirun-connector.csproj.FileListAbsolute.txt    15L  0C    0m  CC=0.0    ←0
  │ package.json                14L  0C    0m  CC=0.0    ←0
  │ hash_connector.pl           14L  0C    0m  CC=0.0    ←0
  │ hash-connector.php          14L  0C    0m  CC=0.0    ←0
  │ urirun.h                    13L  0C    1m  CC=1      ←0
  │ hash_connector.rs           12L  0C    1m  CC=1      ←0
  │ urirun-connector.runtimeconfig.json    12L  0C    0m  CC=0.0    ←0
  │ HashConnector.java          11L  1C    1m  CC=1      ←0
  │ tsconfig.json               11L  0C    0m  CC=0.0    ←0
  │ __init__                    11L  0C    0m  CC=0.0    ←0
  │ v2                          11L  0C    0m  CC=0.0    ←0
  │ flow_thin                   11L  0C    0m  CC=0.0    ←0
  │ flow                        11L  0C    0m  CC=0.0    ←0
  │ hash-connector.ts           10L  0C    1m  CC=1      ←0
  │ Cargo.toml                  10L  0C    0m  CC=0.0    ←0
  │ contract_gate               10L  0C    0m  CC=0.0    ←0
  │ v2_service                  10L  0C    0m  CC=0.0    ←0
  │ progress                    10L  0C    0m  CC=0.0    ←0
  │ cli                         10L  0C    0m  CC=0.0    ←0
  │ v1                          10L  0C    0m  CC=0.0    ←0
  │ errors                      10L  0C    0m  CC=0.0    ←0
  │ daemon                      10L  0C    0m  CC=0.0    ←0
  │ codegen                     10L  0C    0m  CC=0.0    ←0
  │ introspect                  10L  0C    0m  CC=0.0    ←0
  │ v2                          10L  0C    0m  CC=0.0    ←0
  │ _runtime                    10L  0C    0m  CC=0.0    ←0
  │ v2_grpc                     10L  0C    0m  CC=0.0    ←0
  │ agent                       10L  0C    0m  CC=0.0    ←0
  │ v2_adopt                    10L  0C    0m  CC=0.0    ←0
  │ v2_mcp                      10L  0C    0m  CC=0.0    ←0
  │ adopt_pack                  10L  0C    0m  CC=0.0    ←0
  │ worker                      10L  0C    0m  CC=0.0    ←0
  │ _registry                   10L  0C    0m  CC=0.0    ←0
  │ compat                      10L  0C    0m  CC=0.0    ←0
  │ discovery                   10L  0C    0m  CC=0.0    ←0
  │ tree                        10L  0C    0m  CC=0.0    ←0
  │ _scan                       10L  0C    0m  CC=0.0    ←0
  │ secrets                     10L  0C    0m  CC=0.0    ←0
  │ hash-connector.sh            9L  0C    0m  CC=0.0    ←0
  │ package.json                 8L  0C    0m  CC=0.0    ←0
  │ v2_service                   8L  0C    0m  CC=0.0    ←0
  │ v1                           8L  0C    0m  CC=0.0    ←0
  │ errors                       8L  0C    0m  CC=0.0    ←0
  │ _runtime                     8L  0C    0m  CC=0.0    ←0
  │ v2_grpc                      8L  0C    0m  CC=0.0    ←0
  │ v2_adopt                     8L  0C    0m  CC=0.0    ←0
  │ v2_mcp                       8L  0C    0m  CC=0.0    ←0
  │ _registry                    8L  0C    0m  CC=0.0    ←0
  │ compat                       8L  0C    0m  CC=0.0    ←0
  │ _scan                        8L  0C    0m  CC=0.0    ←0
  │ node_cli                     8L  0C    0m  CC=0.0    ←0
  │ task_cli                     8L  0C    0m  CC=0.0    ←0
  │ hash_connector.rb            8L  0C    0m  CC=0.0    ←0
  │ composer.json                7L  0C    0m  CC=0.0    ←0
  │ contract_export              7L  0C    0m  CC=0.0    ←0
  │ Program.cs                   7L  0C    0m  CC=0.0    ←0
  │ declarative                  6L  0C    0m  CC=0.0    ←0
  │ routing                      6L  0C    0m  CC=0.0    ←0
  │ uinput                       6L  0C    0m  CC=0.0    ←0
  │ __init__                     6L  0C    0m  CC=0.0    ←0
  │ host_db                      5L  0C    0m  CC=0.0    ←0
  │ domain_monitor               5L  0C    0m  CC=0.0    ←0
  │ connector_sdk                5L  0C    0m  CC=0.0    ←0
  │ host_integrations            5L  0C    0m  CC=0.0    ←0
  │ connect_catalog              5L  0C    0m  CC=0.0    ←0
  │ scheduler                    5L  0C    0m  CC=0.0    ←0
  │ task_planner                 5L  0C    0m  CC=0.0    ←0
  │ mesh                         5L  0C    0m  CC=0.0    ←0
  │ host_dashboard               5L  0C    0m  CC=0.0    ←0
  │ connector_smoke              5L  0C    0m  CC=0.0    ←0
  │ planfile_adapter             5L  0C    0m  CC=0.0    ←0
  │ connector_scaffold           5L  0C    0m  CC=0.0    ←0
  │ dispatch_protocol            5L  0C    0m  CC=0.0    ←0
  │ __init__                     5L  0C    0m  CC=0.0    ←0
  │ event_schema                 4L  3C    2m  CC=5      ←1
  │ skill                        4L  0C   17m  CC=12     ←1
  │ doctor                       4L  0C   13m  CC=9      ←1
  │ paths                        4L  0C    3m  CC=5      ←4
  │ connector_smoke              4L  0C    3m  CC=6      ←0
  │ connector_contract           4L  1C   11m  CC=4      ←0
  │ openapi_import               4L  0C    0m  CC=0.0    ←0
  │ scanner_net                  4L  0C    0m  CC=0.0    ←0
  │ document_metadata            4L  0C    0m  CC=0.0    ←0
  │ document_sync                4L  0C    0m  CC=0.0    ←0
  │ artifacts_admin              4L  0C    0m  CC=0.0    ←0
  │ scanner_service              4L  0C    0m  CC=0.0    ←0
  │ scanner_bridge               4L  0C    0m  CC=0.0    ←0
  │ connector_lint               4L  0C    0m  CC=0.0    ←0
  │ backend_registry             4L  0C    0m  CC=0.0    ←0
  │ connector_sdk                4L  0C    0m  CC=0.0    ←0
  │ connect_catalog              4L  0C    0m  CC=0.0    ←0
  │ declarative                  4L  0C    0m  CC=0.0    ←0
  │ resolver                     4L  0C    0m  CC=0.0    ←0
  │ connector_scaffold           4L  0C    0m  CC=0.0    ←0
  │ _version                     4L  0C    0m  CC=0.0    ←0
  │ config                       4L  0C    0m  CC=0.0    ←0
  │ manage                       4L  0C    0m  CC=0.0    ←0
  │ keyauth                      4L  0C    0m  CC=0.0    ←0
  │ routing                      4L  0C    0m  CC=0.0    ←0
  │ _util                        4L  0C    0m  CC=0.0    ←0
  │ recovery                     4L  0C    0m  CC=0.0    ←0
  │ diagnostics                  4L  0C    0m  CC=0.0    ←0
  │ server                       4L  0C    0m  CC=0.0    ←0
  │ client                       4L  0C    0m  CC=0.0    ←0
  │ _artifacts                   4L  0C    0m  CC=0.0    ←0
  │ reversible                   4L  0C    0m  CC=0.0    ←0
  │ formatting                   4L  0C    0m  CC=0.0    ←0
  │ flow_verify                  4L  0C    0m  CC=0.0    ←0
  │ mesh                         4L  0C    0m  CC=0.0    ←0
  │ transport                    4L  0C    0m  CC=0.0    ←0
  │ flow_planner                 4L  0C    0m  CC=0.0    ←0
  │ twin_store                   4L  0C    0m  CC=0.0    ←0
  │ episode                      4L  0C    0m  CC=0.0    ←0
  │ .NETCoreApp,Version=v8.0.AssemblyAttributes.cs     4L  0C    0m  CC=0.0    ←0
  │ contract_reversible          2L  0C    0m  CC=0.0    ←0
  │ contract_jsonschema          2L  0C    0m  CC=0.0    ←0
  │ contract_lint                2L  0C    0m  CC=0.0    ←0
  │ contract_typescript          2L  0C    0m  CC=0.0    ←0
  │ __init__                     2L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ __init__                     1L  0C    0m  CC=0.0    ←0
  │ urirun-connector.sourcelink.json     1L  0C    0m  CC=0.0    ←0
  │ urirun.c                     0L  0C    6m  CC=7      ←0
  │
  examples/                       CC̄=4.1    ←in:0  →out:0
  │ docker-compose.yml         132L  0C    0m  CC=0.0    ←0
  │ run-matrix.sh               92L  0C    0m  CC=0.0    ←0
  │ fs-transfer.bindings.json    75L  0C    0m  CC=0.0    ←0
  │ fs_transfer                 71L  0C    4m  CC=8      ←0
  │ verify                      64L  0C    2m  CC=9      ←0
  │ flow                        30L  0C    0m  CC=0.0    ←0
  │ emit_python                 19L  0C    1m  CC=1      ←0
  │ hash.bindings.v2.json       19L  0C    0m  CC=0.0    ←0
  │ run.sh                      15L  0C    0m  CC=0.0    ←0
  │ mesh.json                    7L  0C    0m  CC=0.0    ←0
  │ Dockerfile.bash              6L  0C    0m  CC=0.0    ←0
  │ sample.txt                   1L  0C    0m  CC=0.0    ←0
  │ policy.json                  1L  0C    0m  CC=0.0    ←0
  │
  v1/                             CC̄=3.6    ←in:0  →out:0
  │ urirun-v1.js               343L  0C   57m  CC=12     ←4
  │
  security/                       CC̄=2.3    ←in:0  →out:0
  │ probe                      114L  0C    3m  CC=4      ←0
  │ node.bindings.json          20L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  19L  0C    0m  CC=0.0    ←0
  │ docker-compose.yml          17L  0C    0m  CC=0.0    ←0
  │
  docs/                           CC̄=2.0    ←in:0  →out:1
  │ NODE_CONNECTIONS_TASK_PLAN.yaml   202L  0C    0m  CC=0.0    ←0
  │ gen_error_codes             42L  0C    1m  CC=2      ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! planfile.yaml             1319L  0C    0m  CC=0.0    ←0
  │ !! tree.txt                   611L  0C    0m  CC=0.0    ←0
  │ !! goal.yaml                  540L  0C    0m  CC=0.0    ←0
  │ Makefile                   192L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ project.sh                  66L  0C    0m  CC=0.0    ←0
  │ requirements.txt            32L  0C    0m  CC=0.0    ←0
  │ package.json                27L  0C    0m  CC=0.0    ←0
  │ .codebase_audit_state.json    11L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    10L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     adapters/c/urirun.c                       0L
     xlang/gate.mjs                            0L
     xlang/gate.py                             0L
     xlang/peer.mjs                            0L

COUPLING:
                           adapters.python              scripts             adapters      examples.matrix                xlang                v1.js        adapters.java        adapters.perl                 docs  security.mesh-probe
      adapters.python                   ──                  156                   18                   ←2                   ←3                    6                    1                    1                                            hub
              scripts                    2                   ──                  ←11                   ←7                   ←5                                                                                  ←1                   ←1  hub
             adapters                    1                   11                   ──                                                                                                                                                     hub
      examples.matrix                    2                    7                                        ──                                                                                                                                !! fan-out
                xlang                    3                    5                                                             ──                                                                                                           !! fan-out
                v1.js                   ←6                                                                                                       ──                                                                                      hub
        adapters.java                   ←1                                                                                                                            ──                                                               
        adapters.perl                   ←1                                                                                                                                                 ──                                          
                 docs                                         1                                                                                                                                                 ──                     
  security.mesh-probe                                         1                                                                                                                                                                      ──
  CYCLES: none
  HUB: adapters/ (fan-in=18)
  HUB: scripts/ (fan-in=181)
  HUB: adapters.python/ (fan-in=8)
  HUB: v1.js/ (fan-in=6)
  SMELL: examples.matrix/ fan-out=9 → split needed
  SMELL: adapters/ fan-out=12 → split needed
  SMELL: adapters.python/ fan-out=182 → split needed
  SMELL: xlang/ fan-out=8 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 49 groups | 245f 41464L | 2026-07-05

SUMMARY:
  files_scanned: 245
  total_lines:   41464
  dup_groups:    49
  dup_fragments: 102
  saved_lines:   290
  scan_ms:       319194

HOTSPOTS[7] (files with most duplication):
  adapters/python/urirun_runtime/v2.py  dup=44L  groups=6  frags=7  (0.1%)
  adapters/python/urirun/__init__.py  dup=38L  groups=1  frags=3  (0.1%)
  adapters/python/urirun_runtime/v1.py  dup=33L  groups=5  frags=5  (0.1%)
  adapters/python/urirun/host/host_dashboard.py  dup=29L  groups=2  frags=4  (0.1%)
  adapters/python/urirun_twin/twin_store.py  dup=29L  groups=4  frags=7  (0.1%)
  adapters/python/urirun_node/server.py  dup=28L  groups=3  frags=5  (0.1%)
  adapters/python/urirun_twin/reversible.py  dup=23L  groups=2  frags=3  (0.1%)

DUPLICATES[49] (ranked by impact):
  [33a60905325bfc13] ! STRU  command  L=16 N=3 saved=32 sim=1.00
      adapters/python/urirun/__init__.py:47-62  (command)
      adapters/python/urirun/__init__.py:65-69  (shell)
      adapters/python/urirun/__init__.py:72-88  (handler)
  [21ec0af11b527352]   STRU  _free_port_from_old_scanner  L=6 N=3 saved=12 sim=1.00
      adapters/python/urirun/host/_host_port.py:90-95  (_free_port_from_old_scanner)
      adapters/python/urirun/host/_host_port.py:98-103  (_free_port_from_old_chat)
      adapters/python/urirun/host/_host_port.py:106-111  (_free_port_from_old_android_node)
  [5a144dbb12403176]   STRU  _run_dry_run_mode  L=11 N=2 saved=11 sim=1.00
      adapters/python/urirun_runtime/v1.py:287-297  (_run_dry_run_mode)
      adapters/python/urirun_runtime/v2.py:1005-1015  (_run_dry)
  [01e962e545eb2852]   STRU  schema_from_contracts  L=11 N=2 saved=11 sim=1.00
      adapters/python/urirun_twin/reversible.py:135-145  (schema_from_contracts)
      adapters/python/urirun_twin/reversible.py:148-155  (schema_from_bindings)
  [F0025]   FUZZ  essential  L=12 N=2 saved=12 sim=0.91
      examples/matrix/verify.py:16-27  (essential)
      adapters/conformance.py:43-56  (essential)
  [635b02bad6666184]   STRU  is_scanner_process  L=10 N=2 saved=10 sim=1.00
      adapters/python/urirun/host/service_control.py:213-222  (is_scanner_process)
      adapters/python/urirun/host/service_control.py:236-245  (is_android_node_process)
  [F0024]   FUZZ  do_GET  L=11 N=2 saved=11 sim=0.87
      adapters/python/urirun/host/host_dashboard.py:1296-1306  (do_GET)
      adapters/python/urirun/host/host_dashboard.py:1308-1319  (do_POST)
  [F0023]   FUZZ  send_json  L=10 N=2 saved=10 sim=0.90
      adapters/python/urirun_node/server.py:89-98  (send_json)
      adapters/python/urirun/host/dashboard_http.py:19-29  (_json_response)
  [F0022]   FUZZ  render_value  L=8 N=2 saved=8 sim=0.99
      adapters/python/urirun_runtime/v1.py:67-74  (render_value)
      adapters/python/urirun_runtime/v2.py:641-648  (render_value)
  [556cfda3a470f605]   STRU  register_ticket_creator  L=7 N=2 saved=7 sim=1.00
      adapters/python/urirun_runtime/errors.py:390-396  (register_ticket_creator)
      adapters/python/urirun_runtime/v2_service.py:41-44  (register_signer)
  [a1b73f00a3fc889e]   STRU  register_executor  L=7 N=2 saved=7 sim=1.00
      adapters/python/urirun_runtime/v2.py:772-778  (register_executor)
      adapters/python/urirun_runtime/v2.py:917-919  (register_cli_command)
  [F0020]   FUZZ  dispatch_dry  L=7 N=2 saved=7 sim=0.96
      adapters/python/urirun_connectors_toolkit/connector_contract.py:60-66  (dispatch_dry)
      adapters/python/urirun_connectors_toolkit/connector_contract.py:69-75  (dispatch_execute)
  [F0021]   FUZZ  __init__  L=7 N=2 saved=7 sim=0.91
      adapters/python/urirun_runtime/worker.py:205-211  (__init__)
      adapters/python/urirun_runtime/worker.py:166-173  (__init__)
  [b7534632e49155f1]   STRU  _host_db  L=3 N=3 saved=6 sim=1.00
      adapters/python/urirun/host/dashboard_api.py:28-30  (_host_db)
      adapters/python/urirun/host/dashboard_api.py:33-35  (_mesh)
      adapters/python/urirun/host/dashboard_api.py:38-40  (_planfile_adapter)
  [966976c70babeb2e]   STRU  _api_checks  L=6 N=2 saved=6 sim=1.00
      adapters/python/urirun/host/dashboard_api.py:182-187  (_api_checks)
      adapters/python/urirun/host/dashboard_api.py:190-195  (_api_logs)
  [ed23bf98863d2f02]   STRU  ready_bindings  L=3 N=3 saved=6 sim=1.00
      adapters/python/urirun_node/preconditions.py:222-224  (ready_bindings)
      adapters/python/urirun_node/skill.py:238-240  (skill_bindings)
      adapters/python/urirun_node/skill.py:243-245  (session_bindings)
  [4f6f72427626808c]   STRU  _cmd_host  L=6 N=2 saved=6 sim=1.00
      adapters/python/urirun_runtime/v2_cmds.py:520-525  (_cmd_host)
      adapters/python/urirun_runtime/v2_cmds.py:528-533  (_cmd_node)
  [F0019]   FUZZ  command  L=6 N=2 saved=6 sim=0.87
      adapters/python/urirun/_connector.py:48-53  (command)
      adapters/python/urirun/_connector.py:55-60  (shell)
  [3fed59bde8ae1620]   EXAC  replace  L=5 N=2 saved=5 sim=1.00
      adapters/python/urirun_runtime/v1.py:68-72  (replace)
      adapters/python/urirun_runtime/v2.py:642-646  (replace)
  [1edfa1e53bf9c338]   EXAC  _ok_example  L=5 N=2 saved=5 sim=1.00
      xlang/gate.py:23-27  (_ok_example)
      xlang/peer.py:30-34  (_ok_example)
  [51d5a021d8e1b415]   STRU  __getattr__  L=5 N=2 saved=5 sim=1.00
      adapters/python/urirun/host/chat_orchestrator.py:1303-1307  (__getattr__)
      adapters/python/urirun_runtime/v2.py:1275-1279  (__getattr__)
  [F0014]   FUZZ  _admin_ok  L=5 N=2 saved=5 sim=0.96
      adapters/python/urirun_node/server.py:867-871  (_admin_ok)
      adapters/python/urirun_node/server.py:873-879  (_run_ok)
  [F0016]   FUZZ  expand_bindings  L=5 N=2 saved=5 sim=0.95
      adapters/python/urirun_runtime/v1.py:392-396  (expand_bindings)
      adapters/python/urirun_runtime/v2.py:1154-1158  (expand_bindings)
  [F0018]   FUZZ  known_good_flows  L=5 N=2 saved=5 sim=0.93
      adapters/python/urirun_twin/twin_store.py:208-212  (known_good_flows)
      adapters/python/urirun_twin/twin_store.py:230-234  (known_good_episodes)
  [F0017]   FUZZ  __setitem__  L=5 N=2 saved=5 sim=0.92
      adapters/python/urirun_twin/twin_store.py:99-103  (__setitem__)
      adapters/python/urirun_twin/twin_store.py:105-109  (__delitem__)
  [F0015]   FUZZ  decorator  L=5 N=2 saved=5 sim=0.87
      adapters/python/urirun_runtime/_registry.py:395-399  (decorator)
      adapters/python/urirun_runtime/_registry.py:394-401  (uri_handler)
  [ecb3319de9bb32de]   EXAC  close  L=4 N=2 saved=4 sim=1.00
      adapters/python/urirun_runtime/worker.py:188-191  (close)
      adapters/python/urirun_runtime/worker.py:219-222  (close)
  [ffb4bb725278fa05]   STRU  _register_ticket_creator  L=4 N=2 saved=4 sim=1.00
      adapters/python/urirun/host/planfile_adapter.py:284-287  (_register_ticket_creator)
      adapters/python/urirun_node/keyauth.py:176-179  (_register_signer)
  [39d8e0f2bc98c14d]   STRU  _uri_ready_check  L=4 N=2 saved=4 sim=1.00
      adapters/python/urirun/node/preconditions.py:423-426  (_uri_ready_check)
      adapters/python/urirun/node/preconditions.py:429-432  (_uri_ready_ensure)
  [e819c3a558e3729d]   STRU  _cmd_gen  L=4 N=2 saved=4 sim=1.00
      adapters/python/urirun_runtime/v2_cmds.py:209-212  (_cmd_gen)
      adapters/python/urirun_runtime/v2_cmds.py:432-435  (_cmd_agent)
  [F0013]   FUZZ  _handle_check  L=4 N=2 saved=4 sim=0.96
      adapters/python/urirun_runtime/v1.py:470-473  (_handle_check)
      adapters/python/urirun_runtime/_runtime.py:621-625  (_cmd_check)
  [F0012]   FUZZ  loads_json  L=4 N=2 saved=4 sim=0.94
      adapters/python/urirun/host/planfile_adapter.py:278-281  (loads_json)
      adapters/python/urirun_node/_util.py:24-28  (_parse_json_option)
  [24c306c61f9a64c8]   STRU  _artifact_meta_dict  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun/host/host_dashboard.py:623-625  (_artifact_meta_dict)
      adapters/python/urirun/host/host_dashboard.py:1085-1087  (_uri_action_payload)
  [cd0800c552f36fa8]   STRU  _data_artifact_register  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun/host/node_cli.py:97-99  (_data_artifact_register)
      adapters/python/urirun/host/node_cli.py:106-108  (_data_check_add)
  [5b8bcc0e7471f982]   STRU  start_ticket  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun/host/planfile_adapter.py:197-199  (start_ticket)
      adapters/python/urirun/host/planfile_adapter.py:266-268  (ready_ticket)
  [51bef40acae4e702]   STRU  save_host_config  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun_node/config.py:82-84  (save_host_config)
      adapters/python/urirun_node/config.py:196-198  (save_node_config)
  [2a9aceb4be794dd5]   STRU  _api_id  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun_node/doctor.py:74-76  (_api_id)
      adapters/python/urirun_node/transport.py:422-424  (_configured_api_id)
  [bfe3c0f10a741ce8]   STRU  _proofs_from_dicts  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun_twin/episode.py:136-138  (_proofs_from_dicts)
      adapters/python/urirun_twin/episode.py:141-143  (_artifacts_from_dicts)
  [F0010]   FUZZ  _sig  L=3 N=2 saved=3 sim=1.00
      adapters/python/urirun_twin/twin_store.py:121-123  (_sig)
      adapters/python/urirun_twin/reversible.py:49-52  (sig)
  [F0001]   FUZZ  _dispatch  L=3 N=2 saved=3 sim=0.99
      adapters/python/urirun/host/dispatch.py:49-51  (_dispatch)
      adapters/python/urirun_node/skill.py:153-155  (dispatch)
  [F0005]   FUZZ  query_value  L=3 N=2 saved=3 sim=0.93
      adapters/python/urirun/host/widgets.py:4-6  (query_value)
      adapters/python/urirun_scanner/scanner_bridge.py:24-26  (_query_value)
  [F0004]   FUZZ  get_ticket  L=3 N=2 saved=3 sim=0.91
      adapters/python/urirun/host/planfile_adapter.py:187-189  (get_ticket)
      adapters/python/urirun/host/planfile_adapter.py:213-215  (fail_ticket)
  [F0003]   FUZZ  _node_from_url  L=3 N=2 saved=3 sim=0.90
      adapters/python/urirun/host/node_health.py:251-253  (_node_from_url)
      adapters/python/urirun/host/node_dispatch.py:313-317  (_node_from_url)
  [F0002]   FUZZ  _host_cmd_nodes  L=3 N=2 saved=3 sim=0.88
      adapters/python/urirun/host/node_cli.py:495-497  (_host_cmd_nodes)
      adapters/python/urirun/host/node_cli.py:500-502  (_host_cmd_routes)
  [F0006]   FUZZ  fetch_catalog  L=3 N=2 saved=3 sim=0.87
      adapters/python/urirun_connectors_toolkit/connect_catalog.py:43-45  (fetch_catalog)
      adapters/python/urirun_connectors_toolkit/connect_catalog.py:49-51  (fetch_connector)
  [F0009]   FUZZ  document_index_path  L=3 N=2 saved=3 sim=0.87
      adapters/python/urirun_scanner/document_sync.py:80-82  (document_index_path)
      adapters/python/urirun_scanner/document_sync.py:629-631  (scanned_id_log_path)
  [F0008]   FUZZ  _cmd_add_python  L=3 N=2 saved=3 sim=0.86
      adapters/python/urirun_runtime/v2_adopt.py:172-174  (_cmd_add_python)
      adapters/python/urirun_runtime/v2_adopt.py:177-179  (_cmd_add_npm)
  [F0007]   FUZZ  current_id  L=3 N=2 saved=3 sim=0.86
      adapters/python/urirun_node/server.py:80-82  (current_id)
      adapters/python/urirun_node/server.py:84-86  (count)
  [F0011]   FUZZ  recall_flow  L=3 N=2 saved=3 sim=0.86
      adapters/python/urirun_twin/twin_store.py:204-206  (recall_flow)
      adapters/python/urirun_twin/twin_store.py:283-285  (recall_proof)

REFACTOR[49] (ranked by priority):
  [1] ○ extract_function   → adapters/python/urirun/utils/command.py
      WHY: 3 occurrences of 16-line block across 1 files — saves 32 lines
      FILES: adapters/python/urirun/__init__.py
  [2] ○ extract_function   → adapters/python/urirun/host/utils/_free_port_from_old_scanner.py
      WHY: 3 occurrences of 6-line block across 1 files — saves 12 lines
      FILES: adapters/python/urirun/host/_host_port.py
  [3] ○ extract_function   → adapters/python/urirun_runtime/utils/_run_dry_run_mode.py
      WHY: 2 occurrences of 11-line block across 2 files — saves 11 lines
      FILES: adapters/python/urirun_runtime/v1.py, adapters/python/urirun_runtime/v2.py
  [4] ○ extract_function   → adapters/python/urirun_twin/utils/schema_from_contracts.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: adapters/python/urirun_twin/reversible.py
  [5] ○ extract_function   → utils/essential.py
      WHY: 2 occurrences of 12-line block across 2 files — saves 12 lines
      FILES: adapters/conformance.py, examples/matrix/verify.py
  [6] ○ extract_function   → adapters/python/urirun/host/utils/is_scanner_process.py
      WHY: 2 occurrences of 10-line block across 1 files — saves 10 lines
      FILES: adapters/python/urirun/host/service_control.py
  [7] ○ extract_class      → adapters/python/urirun/host/utils/do_GET.py
      WHY: 2 occurrences of 11-line block across 1 files — saves 11 lines
      FILES: adapters/python/urirun/host/host_dashboard.py
  [8] ○ extract_function   → adapters/python/utils/send_json.py
      WHY: 2 occurrences of 10-line block across 2 files — saves 10 lines
      FILES: adapters/python/urirun/host/dashboard_http.py, adapters/python/urirun_node/server.py
  [9] ○ extract_function   → adapters/python/urirun_runtime/utils/render_value.py
      WHY: 2 occurrences of 8-line block across 2 files — saves 8 lines
      FILES: adapters/python/urirun_runtime/v1.py, adapters/python/urirun_runtime/v2.py
  [10] ○ extract_function   → adapters/python/urirun_runtime/utils/register_ticket_creator.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: adapters/python/urirun_runtime/errors.py, adapters/python/urirun_runtime/v2_service.py
  [11] ○ extract_function   → adapters/python/urirun_runtime/utils/register_executor.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: adapters/python/urirun_runtime/v2.py
  [12] ○ extract_class      → adapters/python/urirun_connectors_toolkit/utils/dispatch_dry.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: adapters/python/urirun_connectors_toolkit/connector_contract.py
  [13] ○ extract_function   → adapters/python/urirun_runtime/utils/__init__.py
      WHY: 2 occurrences of 7-line block across 1 files — saves 7 lines
      FILES: adapters/python/urirun_runtime/worker.py
  [14] ○ extract_function   → adapters/python/urirun/host/utils/_host_db.py
      WHY: 3 occurrences of 3-line block across 1 files — saves 6 lines
      FILES: adapters/python/urirun/host/dashboard_api.py
  [15] ○ extract_function   → adapters/python/urirun/host/utils/_api_checks.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: adapters/python/urirun/host/dashboard_api.py
  [16] ○ extract_function   → adapters/python/urirun_node/utils/ready_bindings.py
      WHY: 3 occurrences of 3-line block across 2 files — saves 6 lines
      FILES: adapters/python/urirun_node/preconditions.py, adapters/python/urirun_node/skill.py
  [17] ○ extract_function   → adapters/python/urirun_runtime/utils/_cmd_host.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: adapters/python/urirun_runtime/v2_cmds.py
  [18] ○ extract_class      → adapters/python/urirun/utils/command.py
      WHY: 2 occurrences of 6-line block across 1 files — saves 6 lines
      FILES: adapters/python/urirun/_connector.py
  [19] ○ extract_function   → adapters/python/urirun_runtime/utils/replace.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: adapters/python/urirun_runtime/v1.py, adapters/python/urirun_runtime/v2.py
  [20] ○ extract_function   → xlang/utils/_ok_example.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: xlang/gate.py, xlang/peer.py
  [21] ○ extract_function   → adapters/python/utils/__getattr__.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: adapters/python/urirun/host/chat_orchestrator.py, adapters/python/urirun_runtime/v2.py
  [22] ○ extract_class      → adapters/python/urirun_node/utils/_admin_ok.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: adapters/python/urirun_node/server.py
  [23] ○ extract_function   → adapters/python/urirun_runtime/utils/expand_bindings.py
      WHY: 2 occurrences of 5-line block across 2 files — saves 5 lines
      FILES: adapters/python/urirun_runtime/v1.py, adapters/python/urirun_runtime/v2.py
  [24] ○ extract_class      → adapters/python/urirun_twin/utils/known_good_flows.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: adapters/python/urirun_twin/twin_store.py
  [25] ○ extract_class      → adapters/python/urirun_twin/utils/__setitem__.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: adapters/python/urirun_twin/twin_store.py
  [26] ○ extract_function   → adapters/python/urirun_runtime/utils/decorator.py
      WHY: 2 occurrences of 5-line block across 1 files — saves 5 lines
      FILES: adapters/python/urirun_runtime/_registry.py
  [27] ○ extract_function   → adapters/python/urirun_runtime/utils/close.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: adapters/python/urirun_runtime/worker.py
  [28] ○ extract_function   → adapters/python/utils/_register_ticket_creator.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: adapters/python/urirun/host/planfile_adapter.py, adapters/python/urirun_node/keyauth.py
  [29] ○ extract_function   → adapters/python/urirun/node/utils/_uri_ready_check.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: adapters/python/urirun/node/preconditions.py
  [30] ○ extract_function   → adapters/python/urirun_runtime/utils/_cmd_gen.py
      WHY: 2 occurrences of 4-line block across 1 files — saves 4 lines
      FILES: adapters/python/urirun_runtime/v2_cmds.py
  [31] ○ extract_function   → adapters/python/urirun_runtime/utils/_handle_check.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: adapters/python/urirun_runtime/_runtime.py, adapters/python/urirun_runtime/v1.py
  [32] ○ extract_function   → adapters/python/utils/loads_json.py
      WHY: 2 occurrences of 4-line block across 2 files — saves 4 lines
      FILES: adapters/python/urirun/host/planfile_adapter.py, adapters/python/urirun_node/_util.py
  [33] ○ extract_function   → adapters/python/urirun/host/utils/_artifact_meta_dict.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun/host/host_dashboard.py
  [34] ○ extract_function   → adapters/python/urirun/host/utils/_data_artifact_register.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun/host/node_cli.py
  [35] ○ extract_function   → adapters/python/urirun/host/utils/start_ticket.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun/host/planfile_adapter.py
  [36] ○ extract_function   → adapters/python/urirun_node/utils/save_host_config.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_node/config.py
  [37] ○ extract_function   → adapters/python/urirun_node/utils/_api_id.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: adapters/python/urirun_node/doctor.py, adapters/python/urirun_node/transport.py
  [38] ○ extract_function   → adapters/python/urirun_twin/utils/_proofs_from_dicts.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_twin/episode.py
  [39] ○ extract_function   → adapters/python/urirun_twin/utils/_sig.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: adapters/python/urirun_twin/reversible.py, adapters/python/urirun_twin/twin_store.py
  [40] ○ extract_function   → adapters/python/utils/_dispatch.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: adapters/python/urirun/host/dispatch.py, adapters/python/urirun_node/skill.py
  [41] ○ extract_function   → adapters/python/utils/query_value.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: adapters/python/urirun/host/widgets.py, adapters/python/urirun_scanner/scanner_bridge.py
  [42] ○ extract_function   → adapters/python/urirun/host/utils/get_ticket.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun/host/planfile_adapter.py
  [43] ○ extract_function   → adapters/python/urirun/host/utils/_node_from_url.py
      WHY: 2 occurrences of 3-line block across 2 files — saves 3 lines
      FILES: adapters/python/urirun/host/node_dispatch.py, adapters/python/urirun/host/node_health.py
  [44] ○ extract_function   → adapters/python/urirun/host/utils/_host_cmd_nodes.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun/host/node_cli.py
  [45] ○ extract_function   → adapters/python/urirun_connectors_toolkit/utils/fetch_catalog.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_connectors_toolkit/connect_catalog.py
  [46] ○ extract_function   → adapters/python/urirun_scanner/utils/document_index_path.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_scanner/document_sync.py
  [47] ○ extract_function   → adapters/python/urirun_runtime/utils/_cmd_add_python.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_runtime/v2_adopt.py
  [48] ○ extract_class      → adapters/python/urirun_node/utils/current_id.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_node/server.py
  [49] ○ extract_class      → adapters/python/urirun_twin/utils/recall_flow.py
      WHY: 2 occurrences of 3-line block across 1 files — saves 3 lines
      FILES: adapters/python/urirun_twin/twin_store.py

QUICK_WINS[18] (low risk, high savings — do first):
  [1] extract_function   saved=32L  → adapters/python/urirun/utils/command.py
      FILES: __init__.py
  [2] extract_function   saved=12L  → adapters/python/urirun/host/utils/_free_port_from_old_scanner.py
      FILES: _host_port.py
  [5] extract_function   saved=12L  → utils/essential.py
      FILES: conformance.py, verify.py
  [3] extract_function   saved=11L  → adapters/python/urirun_runtime/utils/_run_dry_run_mode.py
      FILES: v1.py, v2.py
  [4] extract_function   saved=11L  → adapters/python/urirun_twin/utils/schema_from_contracts.py
      FILES: reversible.py
  [7] extract_class      saved=11L  → adapters/python/urirun/host/utils/do_GET.py
      FILES: host_dashboard.py
  [6] extract_function   saved=10L  → adapters/python/urirun/host/utils/is_scanner_process.py
      FILES: service_control.py
  [8] extract_function   saved=10L  → adapters/python/utils/send_json.py
      FILES: dashboard_http.py, server.py
  [9] extract_function   saved=8L  → adapters/python/urirun_runtime/utils/render_value.py
      FILES: v1.py, v2.py
  [10] extract_function   saved=7L  → adapters/python/urirun_runtime/utils/register_ticket_creator.py
      FILES: errors.py, v2_service.py

DEPENDENCY_RISK[1] (duplicates spanning multiple packages):
  essential  packages=2  files=2
      adapters/conformance.py
      examples/matrix/verify.py

EFFORT_ESTIMATE (total ≈ 10.1h):
  medium command                             saved=32L  ~64min
  easy   _free_port_from_old_scanner         saved=12L  ~24min
  easy   _run_dry_run_mode                   saved=11L  ~22min
  easy   schema_from_contracts               saved=11L  ~22min
  medium essential                           saved=12L  ~48min
  easy   is_scanner_process                  saved=10L  ~20min
  easy   do_GET                              saved=11L  ~22min
  easy   send_json                           saved=10L  ~20min
  easy   render_value                        saved=8L  ~16min
  easy   register_ticket_creator             saved=7L  ~14min
  ... +39 more (~332min)

METRICS-TARGET:
  dup_groups:  49 → 0
  saved_lines: 290 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 2702 func | 139f | 2026-07-05
# generated in 0.01s

NEXT[4] (ranked by impact):
  [1] !! SPLIT           adapters/python/urirun/host/dashboard.js
      WHY: 3033L, 0 classes, max CC=14
      EFFORT: ~4h  IMPACT: 42462

  [2] !! SPLIT           adapters/python/urirun/host/host_dashboard.py
      WHY: 1446L, 0 classes, max CC=11
      EFFORT: ~4h  IMPACT: 15906

  [3] !  SPLIT-FUNC      api_twin_state  CC=16  fan=21
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 336

  [4] !! SPLIT           adapters/python/urirun_scanner/scanner_bridge.py
      WHY: 1548L, 0 classes, max CC=0
      EFFORT: ~4h  IMPACT: 0


RISKS[3]:
  ⚠ Splitting adapters/python/urirun/host/dashboard.js may break 452 import paths
  ⚠ Splitting adapters/python/urirun_scanner/scanner_bridge.py may break 0 import paths
  ⚠ Splitting adapters/python/urirun/host/host_dashboard.py may break 70 import paths

METRICS-TARGET:
  CC̄:          4.2 → ≤2.9
  max-CC:      16 → ≤8
  god-modules: 27 → 0
  high-CC(≥15): 1 → ≤0
  hub-types:   0 → ≤0

PATTERNS (language parser shared logic):
  _extract_declarations() in base.py — unified extraction for:
    - TypeScript: interfaces, types, classes, functions, arrow funcs
    - PHP: namespaces, traits, classes, functions, includes
    - Ruby: modules, classes, methods, requires
    - C++: classes, structs, functions, #includes
    - C#: classes, interfaces, methods, usings
    - Java: classes, interfaces, methods, imports
    - Go: packages, functions, structs
    - Rust: modules, functions, traits, use statements

  Shared regex patterns per language:
    - import: language-specific import/require/using patterns
    - class: class/struct/trait declarations with inheritance
    - function: function/method signatures with visibility
    - brace_tracking: for C-family languages ({ })
    - end_keyword_tracking: for Ruby (module/class/def...end)

  Benefits:
    - Consistent extraction logic across all languages
    - Reduced code duplication (~70% reduction in parser LOC)
    - Easier maintenance: fix once, apply everywhere
    - Standardized FunctionInfo/ClassInfo models

HISTORY:
  prev CC̄=4.2 → now CC̄=4.2
```

## Intent

urirun
