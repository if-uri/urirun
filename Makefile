PYTHON ?= python3
NODE ?= node
CC ?= cc

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_.-]+:.*##/ {printf "%-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: test
test: test-js test-python test-c test-examples test-v1 test-v2 ## Run all checks.

.PHONY: test-js
test-js: ## Run JavaScript adapter tests.
	$(NODE) --test adapters/js/*.test.js

.PHONY: test-python
test-python: ## Run Python adapter tests.
	PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s adapters/python/tests -p 'test_*.py'

.PHONY: test-c
test-c: ## Compile and run C adapter tests.
	$(CC) -Wall -Wextra -Werror -Iadapters/c adapters/c/urirun.c adapters/c/urirun_test.c -o /tmp/urirun-c-test
	/tmp/urirun-c-test

.PHONY: test-examples
test-examples: ## Syntax-check reference adapter examples.
	$(NODE) --check examples/reference_adapters/node-server.js
	$(PYTHON) -m py_compile examples/reference_adapters/python-server.py
	$(CC) -Wall -Wextra -Werror -Iadapters/c -c examples/reference_adapters/firmware-pseudo.c -o /tmp/urirun-firmware-example.o

.PHONY: test-v1
test-v1: ## Run urirun v1 parameter-binding, docker, and shell checks.
	$(NODE) --test v1/examples/js/*.test.js
	PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s v1/examples/python -p 'test_*.py'
	$(NODE) v1/examples/js/example.js
	PYTHONPATH=adapters/python $(PYTHON) v1/examples/python/example.py
	$(PYTHON) -m json.tool v1/examples/json/bindings.v1.example.json >/tmp/urirun-v1-bindings.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 compile v1/examples/json/bindings.v1.example.json --out /tmp/urirun-v1.registry.json --generated-at 2026-06-19T00:00:00.000Z
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 run 'media://local/video/transcode' --registry /tmp/urirun-v1.registry.json --payload '{"input":"a.mp4","output":"b.mp4"}' >/tmp/urirun-v1-ffmpeg.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 list /tmp/urirun-v1.registry.json --allow 'media://**'
	$(NODE) v1/examples/html_uri_app/test.mjs

.PHONY: test-v2
test-v2: ## Run urirun v2 schema/decorator, artifact, and MCP/A2A checks.
	PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s v2/examples/python -p 'test_*.py'
	$(NODE) v2/examples/generators/nodejs/generate-bindings.mjs >/tmp/urirun-v2-gen.json
	$(NODE) v2/examples/html_uri_app/test.mjs
	$(PYTHON) -m json.tool v2/examples/json/bindings.v2.example.json >/tmp/urirun-v2-bindings.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 compile v2/examples/json/bindings.v2.example.json --out /tmp/urirun-v2.registry.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_mcp tools /tmp/urirun-v2.registry.json >/tmp/urirun-v2-mcp.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_mcp card /tmp/urirun-v2.registry.json >/tmp/urirun-v2-a2a.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_adopt add-python-package pip --out /tmp/urirun-v2-adopt.bindings.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 compile /tmp/urirun-v2-adopt.bindings.json --out /tmp/urirun-v2-adopt.registry.json
	PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 run 'cli://pip/pip/run' --registry /tmp/urirun-v2-adopt.registry.json --payload '{"args":["--version"]}' >/tmp/urirun-v2-adopt-run.json
	command -v php >/dev/null 2>&1 && php v2/examples/generators/php/example.php >/tmp/urirun-v2-php.json || echo "php not installed; skipping PHP generator"
	$(PYTHON) v2/examples/docker_uri_flow/test_flow_runner.py
	$(PYTHON) v2/examples/docker_uri_flow/test_flow_e2e.py
	PYTHONPATH=adapters/python $(PYTHON) v2/examples/docker_uri_flow/test_service_adapter.py
	PYTHONPATH=adapters/python $(PYTHON) v2/examples/transports/test_transports.py

.PHONY: clean
clean: ## Remove local generated cache files.
	rm -rf node_modules .pytest_cache adapters/python/tests/__pycache__ adapters/python/urirun/__pycache__ adapters/python/*.egg-info adapters/python/build examples/__pycache__ examples/reference_adapters/__pycache__ v1/examples/python/__pycache__ v2/examples/python/__pycache__ v2/examples/docker_uri_flow/__pycache__ v2/examples/transports/__pycache__ __pycache__
