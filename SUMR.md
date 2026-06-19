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

- **name**: `urihandler`
- **version**: `0.0.0`
- **ecosystem**: SUMD + DOQL + testql + taskfile
- **generated_from**: Makefile, testql(1), app.doql.less, goal.yaml, .env.example, package.json, project/(5 analysis files)

## Architecture

```
SUMD (description) → DOQL/source (code) → taskfile (automation) → testql (verification)
```

### DOQL Application Declaration (`app.doql.less`)

```less markpact:doql path=app.doql.less
// LESS format — define @variables here as needed

app {
  name: urirun;
  version: 0.3.7;
}

workflow[name="test"] {
  trigger: manual;
  step-1: depend target=test-js;
  step-2: depend target=test-python;
  step-3: depend target=test-c;
  step-4: depend target=test-examples;
  step-5: depend target=test-v1;
  step-6: depend target=test-v2;
}

workflow[name="test-js"] {
  trigger: manual;
  step-1: run cmd=$(NODE) --test adapters/js/*.test.js;
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

workflow[name="test-examples"] {
  trigger: manual;
  step-1: run cmd=$(NODE) --check examples/reference_adapters/node-server.js;
  step-2: run cmd=$(PYTHON) -m py_compile examples/reference_adapters/python-server.py;
  step-3: run cmd=$(CC) -Wall -Wextra -Werror -Iadapters/c -c examples/reference_adapters/firmware-pseudo.c -o /tmp/urirun-firmware-example.o;
}

workflow[name="test-v1"] {
  trigger: manual;
  step-1: run cmd=$(NODE) --test v1/examples/js/*.test.js;
  step-2: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s v1/examples/python -p 'test_*.py';
  step-3: run cmd=$(NODE) v1/examples/js/example.js;
  step-4: run cmd=PYTHONPATH=adapters/python $(PYTHON) v1/examples/python/example.py;
  step-5: run cmd=$(PYTHON) -m json.tool v1/examples/json/bindings.v1.example.json >/tmp/urirun-v1-bindings.json;
  step-6: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 compile v1/examples/json/bindings.v1.example.json --out /tmp/urirun-v1.registry.json --generated-at 2026-06-19T00:00:00.000Z;
  step-7: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 run 'media://local/video/transcode' --registry /tmp/urirun-v1.registry.json --payload '{"input":"a.mp4","output":"b.mp4"}' >/tmp/urirun-v1-ffmpeg.json;
  step-8: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v1 list /tmp/urirun-v1.registry.json --allow 'media://**';
  step-9: run cmd=$(NODE) v1/examples/html_uri_app/test.mjs;
}

workflow[name="test-v2"] {
  trigger: manual;
  step-1: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s v2/examples/python -p 'test_*.py';
  step-2: run cmd=$(NODE) v2/examples/generators/nodejs/generate-bindings.mjs >/tmp/urirun-v2-gen.json;
  step-3: run cmd=$(NODE) v2/examples/html_uri_app/test.mjs;
  step-4: run cmd=$(PYTHON) -m json.tool v2/examples/json/bindings.v2.example.json >/tmp/urirun-v2-bindings.json;
  step-5: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 compile v2/examples/json/bindings.v2.example.json --out /tmp/urirun-v2.registry.json;
  step-6: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_mcp tools /tmp/urirun-v2.registry.json >/tmp/urirun-v2-mcp.json;
  step-7: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_mcp card /tmp/urirun-v2.registry.json >/tmp/urirun-v2-a2a.json;
  step-8: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2_adopt add-python-package pip --out /tmp/urirun-v2-adopt.bindings.json;
  step-9: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 compile /tmp/urirun-v2-adopt.bindings.json --out /tmp/urirun-v2-adopt.registry.json;
  step-10: run cmd=PYTHONPATH=adapters/python $(PYTHON) -m urirun.v2 run 'cli://pip/pip/run' --registry /tmp/urirun-v2-adopt.registry.json --payload '{"args":["--version"]}' >/tmp/urirun-v2-adopt-run.json;
  step-11: run cmd=command -v php >/dev/null 2>&1 && php v2/examples/generators/php/example.php >/tmp/urirun-v2-php.json || echo "php not installed; skipping PHP generator";
  step-12: run cmd=$(PYTHON) v2/examples/docker_uri_flow/test_flow_runner.py;
  step-13: run cmd=$(PYTHON) v2/examples/docker_uri_flow/test_flow_e2e.py;
  step-14: run cmd=PYTHONPATH=adapters/python $(PYTHON) v2/examples/docker_uri_flow/test_service_adapter.py;
  step-15: run cmd=PYTHONPATH=adapters/python $(PYTHON) v2/examples/transports/test_transports.py;
}

workflow[name="clean"] {
  trigger: manual;
  step-1: run cmd=rm -rf node_modules .pytest_cache adapters/python/tests/__pycache__ adapters/python/urirun/__pycache__ adapters/python/*.egg-info adapters/python/build examples/__pycache__ examples/reference_adapters/__pycache__ v1/examples/python/__pycache__ v2/examples/python/__pycache__ v2/examples/docker_uri_flow/__pycache__ v2/examples/transports/__pycache__ __pycache__;
}

tests {
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
  template_file: .env.example;
  vars: LLM_MODEL, OPENROUTER_API_KEY, PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
  runtime_llm: OPENROUTER_API_KEY;
  runtime_pfix: PFIX_AUTO_APPLY, PFIX_AUTO_INSTALL_DEPS, PFIX_AUTO_RESTART, PFIX_CREATE_BACKUPS, PFIX_DRY_RUN, PFIX_ENABLED, PFIX_GIT_COMMIT, PFIX_GIT_PREFIX, PFIX_MAX_RETRIES;
}
```

## Workflows

## Call Graph

*410 nodes · 500 edges · 32 modules · CC̄=3.8*

### Hubs (by degree)

| Function | CC | in | out | total |
|----------|----|----|-----|-------|
| `normalize_flow` *(in v2.examples.device_mesh_lab.controller)* | 20 ⚠ | 4 | 35 | **39** |
| `handler` *(in v2.examples.device_mesh_lab.device_agent.DeviceAgent)* | 1 | 0 | 32 | **32** |
| `scan_path` *(in adapters.python.urirun._scan)* | 15 ⚠ | 4 | 27 | **31** |
| `send_json` *(in v2.examples.device_mesh_lab.mesh_env)* | 1 | 18 | 12 | **30** |
| `normalize_binding` *(in adapters.python.urirun._scan)* | 11 ⚠ | 17 | 12 | **29** |
| `parse_flow` *(in v8.examples.docker_uri_flow.orchestrator.flow_runner)* | 24 ⚠ | 1 | 26 | **27** |
| `validate_binding_document` *(in adapters.python.urirun.v2)* | 12 ⚠ | 2 | 24 | **26** |
| `run` *(in adapters.python.urirun.v1)* | 14 ⚠ | 2 | 23 | **25** |

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/tellmesh/urihandler
# generated in 0.18s
# nodes: 410 | edges: 500 | modules: 32
# CC̄=3.8

HUBS[20]:
  v2.examples.device_mesh_lab.controller.normalize_flow
    CC=20  in:4  out:35  total:39
  v2.examples.device_mesh_lab.device_agent.DeviceAgent.handler
    CC=1  in:0  out:32  total:32
  adapters.python.urirun._scan.scan_path
    CC=15  in:4  out:27  total:31
  v2.examples.device_mesh_lab.mesh_env.send_json
    CC=1  in:18  out:12  total:30
  adapters.python.urirun._scan.normalize_binding
    CC=11  in:17  out:12  total:29
  v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_flow
    CC=24  in:1  out:26  total:27
  adapters.python.urirun.v2.validate_binding_document
    CC=12  in:2  out:24  total:26
  adapters.python.urirun.v1.run
    CC=14  in:2  out:23  total:25
  v2.examples.transports.transport_lib.start_http_worker
    CC=1  in:1  out:24  total:25
  v2.examples.device_mesh_lab.controller.Handler.do_POST
    CC=12  in:0  out:24  total:24
  adapters.python.urirun.v2_mcp.serve_mcp
    CC=15  in:1  out:23  total:24
  adapters.python.urirun.v2.scan_artifacts
    CC=11  in:4  out:19  total:23
  adapters.python.urirun.v2.run
    CC=15  in:1  out:22  total:23
  v2.examples.device_mesh_lab.www.app.escapeHtml
    CC=1  in:20  out:2  total:22
  adapters.python.urirun._runtime.evaluate_policy
    CC=16  in:3  out:19  total:22
  adapters.python.urirun._registry.discover_manifest
    CC=14  in:2  out:19  total:21
  adapters.python.urirun._runtime.run
    CC=10  in:1  out:20  total:21
  v2.examples.html_uri_app.backend.Handler.do_GET
    CC=8  in:0  out:21  total:21
  v2.examples.device_mesh_lab.controller.fallback_steps
    CC=33  in:1  out:19  total:20
  adapters.python.urirun._registry.discover_docker_labels
    CC=14  in:2  out:18  total:20

MODULES:
  adapters.c.urirun  [3 funcs]
    copy_token  CC=2  out:1
    is_path_end  CC=3  out:0
    memcpy  CC=1  out:1
  adapters.c.urirun_test  [2 funcs]
    assert  CC=1  out:0
    main  CC=2  out:3
  adapters.js  [5 funcs]
    buildInvocation  CC=1  out:2
    dispatch  CC=3  out:4
    fn  CC=2  out:1
    match  CC=2  out:1
    parseUri  CC=8  out:9
  adapters.python.urihandler  [3 funcs]
    build_invocation  CC=1  out:2
    dispatch  CC=4  out:10
    parse_uri  CC=7  out:13
  adapters.python.urirun._registry  [35 funcs]
    _default_openapi_route  CC=9  out:11
    _discover_python_module  CC=1  out:2
    _emit_json  CC=3  out:3
    _get_route_entry  CC=1  out:0
    _iter_module_exports  CC=6  out:8
    _load_sources  CC=2  out:3
    _operation_from_method  CC=1  out:1
    _route_entry_equal  CC=2  out:2
    _walk_route_entries  CC=5  out:3
    add_route  CC=5  out:6
  adapters.python.urirun._runtime  [11 funcs]
    _matches_any  CC=3  out:1
    _truncate  CC=3  out:2
    check  CC=1  out:7
    default_policy  CC=1  out:0
    evaluate_policy  CC=16  out:19
    list_routes  CC=4  out:10
    merge_policy  CC=7  out:8
    run  CC=10  out:20
    run_local_function  CC=2  out:6
    run_shell_template  CC=3  out:11
  adapters.python.urirun._scan  [33 funcs]
    _read_toml  CC=12  out:17
    binding_to_route_source  CC=3  out:3
    build_binding_document  CC=3  out:6
    compile_registry_document  CC=4  out:5
    emit_json  CC=3  out:3
    github_dependency_binding  CC=4  out:3
    infer_kind  CC=12  out:11
    iter_project_files  CC=5  out:4
    list_bindings  CC=2  out:3
    load_binding_source  CC=5  out:11
  adapters.python.urirun.v1  [19 funcs]
    _binding_pairs  CC=8  out:11
    _env_flags  CC=3  out:5
    _has_placeholders  CC=2  out:3
    _params_spec  CC=4  out:3
    _proc_env  CC=3  out:6
    _run_process  CC=1  out:8
    compile_registry  CC=1  out:2
    expand_binding  CC=7  out:6
    expand_bindings  CC=2  out:2
    load_registry_arg  CC=4  out:9
  adapters.python.urirun.v2  [43 funcs]
    _apply_defaults  CC=14  out:12
    _binding_pairs  CC=8  out:11
    _bindings_as_map  CC=2  out:2
    _coerce_default  CC=4  out:3
    _empty_input_schema  CC=1  out:0
    _input_values  CC=4  out:8
    _iter_files  CC=5  out:4
    _load_manifest  CC=1  out:2
    _load_many  CC=3  out:7
    _manifest_candidates  CC=2  out:3
  adapters.python.urirun.v2_adopt  [5 funcs]
    _command_binding  CC=2  out:2
    installed_python_bindings  CC=4  out:3
    npm_package_bindings  CC=4  out:12
    passthrough_schema  CC=2  out:1
    python_package_bindings  CC=4  out:6
  adapters.python.urirun.v2_grpc  [8 funcs]
    _method  CC=2  out:1
    _route_list  CC=2  out:5
    _validate  CC=5  out:4
    call  CC=6  out:7
    channel_target  CC=3  out:3
    list_routes  CC=1  out:3
    serve  CC=2  out:17
    stream  CC=4  out:7
  adapters.python.urirun.v2_mcp  [9 funcs]
    _input_schema  CC=4  out:3
    build_tool_index  CC=2  out:1
    call_tool  CC=3  out:4
    main  CC=9  out:16
    serve_mcp  CC=15  out:23
    to_a2a_card  CC=4  out:9
    to_mcp_manifest  CC=4  out:2
    to_mcp_tools  CC=4  out:7
    tool_name  CC=1  out:4
  adapters.python.urirun.v2_service  [3 funcs]
    _post  CC=3  out:10
    call  CC=9  out:10
    service_base  CC=3  out:4
  examples.reference_adapters.firmware-pseudo  [2 funcs]
    handle_uri  CC=7  out:3
    led_set  CC=1  out:0
  examples.reference_adapters.node-server  [3 funcs]
    readJson  CC=3  out:4
    server  CC=4  out:5
    writeJson  CC=1  out:4
  examples.reference_adapters.python-server  [1 funcs]
    do_POST  CC=5  out:11
  v1.examples.html_uri_app.app  [2 funcs]
    appendLog  CC=1  out:4
    text  CC=1  out:1
  v1.examples.html_uri_app.uri-runtime-v1  [29 funcs]
    activePolicy  CC=1  out:1
    adapter  CC=3  out:1
    allowed  CC=4  out:1
    compileBindings  CC=4  out:4
    createUriRuntimeV1  CC=32  out:17
    defaultPolicy  CC=1  out:0
    dispatch  CC=17  out:8
    entries  CC=1  out:0
    evaluatePolicy  CC=18  out:3
    expandBinding  CC=10  out:1
  v1.examples.js.urirun-v1  [34 funcs]
    DEFAULT_TIMEOUT  CC=5  out:11
    OUTPUT_LIMIT  CC=5  out:11
    allow  CC=2  out:2
    check  CC=5  out:7
    compileRegistry  CC=1  out:2
    compileRegistryDocument  CC=5  out:3
    defaultAdapter  CC=2  out:0
    deny  CC=2  out:2
    envFlags  CC=3  out:4
    evaluatePolicy  CC=6  out:4
  v2.examples.decorators.example  [3 funcs]
    echo_message  CC=1  out:1
    shell_echo  CC=1  out:1
    transcode  CC=1  out:1
  v2.examples.device_mesh_lab.controller  [26 funcs]
    do_GET  CC=2  out:5
    do_OPTIONS  CC=1  out:1
    do_POST  CC=12  out:24
    append_step_if_missing  CC=7  out:6
    build_registry  CC=5  out:3
    discover_device  CC=6  out:9
    discover_mesh  CC=5  out:6
    execute_flow  CC=9  out:15
    fallback_flow  CC=1  out:4
    fallback_steps  CC=33  out:19
  v2.examples.device_mesh_lab.device_agent  [5 funcs]
    handler  CC=1  out:32
    routes  CC=1  out:12
    main  CC=1  out:6
    make_agent_from_env  CC=3  out:12
    object_schema  CC=2  out:0
  v2.examples.device_mesh_lab.mesh_env  [5 funcs]
    auth_headers  CC=2  out:1
    auth_token  CC=1  out:2
    check_auth  CC=2  out:2
    parse_peers  CC=8  out:14
    send_json  CC=1  out:12
  v2.examples.device_mesh_lab.www.app  [51 funcs]
    appendTimeline  CC=3  out:3
    data  CC=2  out:1
    defaultValueFor  CC=20  out:2
    description  CC=3  out:1
    deviceRows  CC=2  out:1
    escapeHtml  CC=1  out:2
    extractRunResult  CC=10  out:0
    filter  CC=3  out:1
    focusArea  CC=3  out:6
    focusTargetFor  CC=2  out:0
  v2.examples.generators.php.example  [2 funcs]
    bindingFromFunction  CC=2  out:9
    schemaType  CC=2  out:3
  v2.examples.html_uri_app.backend  [14 funcs]
    do_GET  CC=8  out:21
    do_POST  CC=4  out:10
    log_message  CC=1  out:1
    add_log  CC=2  out:2
    binding_document  CC=1  out:2
    dispatch  CC=6  out:14
    dispatch_tool  CC=7  out:13
    env_bool  CC=1  out:2
    json_response  CC=1  out:9
    load_env  CC=6  out:10
  v2.examples.transports.transport_lib  [8 funcs]
    available_transports  CC=4  out:1
    build_registry  CC=1  out:3
    grpc_available  CC=2  out:0
    run_inprocess  CC=2  out:1
    run_queue  CC=1  out:10
    run_via  CC=6  out:16
    serverless_handler  CC=1  out:2
    start_http_worker  CC=1  out:24
  v8.examples.docker_uri_flow.node-worker.server  [6 funcs]
    body  CC=2  out:1
    readBody  CC=2  out:4
    send  CC=1  out:4
    server  CC=10  out:4
    slug  CC=1  out:1
    slugify  CC=1  out:4
  v8.examples.docker_uri_flow.orchestrator.flow_runner  [16 funcs]
    get_path  CC=2  out:1
    json_get  CC=1  out:4
    json_post  CC=1  out:7
    load_registry  CC=3  out:4
    main  CC=3  out:5
    normalize_uri  CC=6  out:7
    parse_flow  CC=24  out:26
    parse_scalar  CC=3  out:2
    registry_has_uri  CC=4  out:9
    registry_route_count  CC=5  out:9
  v8.examples.docker_uri_flow.python-worker.server  [5 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=3  out:2
    normalize  CC=1  out:6
    summary  CC=1  out:2
  v8.examples.docker_uri_flow.shell-worker.server  [4 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=2  out:5
    response  CC=1  out:9
  v8.examples.html_uri_app.app  [15 funcs]
    card  CC=2  out:2
    classFor  CC=1  out:2
    data  CC=2  out:1
    defaults  CC=8  out:5
    escapeHtml  CC=1  out:2
    iconFor  CC=2  out:3
    inputType  CC=2  out:2
    payloadDefaults  CC=4  out:0
    refreshLogs  CC=5  out:7
    renderActions  CC=5  out:5

EDGES:
  examples.reference_adapters.node-server.server → examples.reference_adapters.node-server.writeJson
  examples.reference_adapters.node-server.server → examples.reference_adapters.node-server.readJson
  examples.reference_adapters.python-server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.dispatch
  examples.reference_adapters.firmware-pseudo.handle_uri → examples.reference_adapters.firmware-pseudo.led_set
  v8.examples.html_uri_app.app.routeResponse → v8.examples.html_uri_app.app.renderActions
  v8.examples.html_uri_app.app.routeResponse → v8.examples.html_uri_app.app.renderForm
  v8.examples.html_uri_app.app.renderActions → v8.examples.html_uri_app.app.classFor
  v8.examples.html_uri_app.app.renderActions → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.renderActions → v8.examples.html_uri_app.app.iconFor
  v8.examples.html_uri_app.app.renderForm → v8.examples.html_uri_app.app.schemaFor
  v8.examples.html_uri_app.app.renderForm → v8.examples.html_uri_app.app.payloadDefaults
  v8.examples.html_uri_app.app.renderForm → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.required → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.defaults → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.inputType → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.refreshLogs → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.data → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.card → v8.examples.html_uri_app.app.renderToolList
  v8.examples.html_uri_app.app.renderToolList → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.iconFor → v8.examples.html_uri_app.app.classFor
  v8.examples.docker_uri_flow.shell-worker.server.Handler.do_GET → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.shell-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.dispatch
  v8.examples.docker_uri_flow.shell-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.node-worker.server.server → v8.examples.docker_uri_flow.node-worker.server.send
  v8.examples.docker_uri_flow.node-worker.server.server → v8.examples.docker_uri_flow.node-worker.server.readBody
  v8.examples.docker_uri_flow.node-worker.server.server → v8.examples.docker_uri_flow.node-worker.server.slugify
  v8.examples.docker_uri_flow.node-worker.server.body → v8.examples.docker_uri_flow.node-worker.server.send
  v8.examples.docker_uri_flow.node-worker.server.slug → v8.examples.docker_uri_flow.node-worker.server.send
  v8.examples.docker_uri_flow.python-worker.server.dispatch → v8.examples.docker_uri_flow.python-worker.server.normalize
  v8.examples.docker_uri_flow.python-worker.server.dispatch → v8.examples.docker_uri_flow.python-worker.server.summary
  v8.examples.docker_uri_flow.python-worker.server.Handler.do_GET → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.python-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.dispatch
  v8.examples.docker_uri_flow.python-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_scalar
  v8.examples.docker_uri_flow.orchestrator.flow_runner.resolve_payload → v8.examples.docker_uri_flow.orchestrator.flow_runner.get_path
  v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_has_uri → v8.examples.docker_uri_flow.orchestrator.flow_runner.route_key
  v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_has_uri → v8.examples.docker_uri_flow.orchestrator.flow_runner.normalize_uri
  v8.examples.docker_uri_flow.orchestrator.flow_runner.validate_flow_registry → v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_route_count
  v8.examples.docker_uri_flow.orchestrator.flow_runner.validate_flow_registry → v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_has_uri
  v8.examples.docker_uri_flow.orchestrator.flow_runner.wait_for_services → v8.examples.docker_uri_flow.orchestrator.flow_runner.service_url
  v8.examples.docker_uri_flow.orchestrator.flow_runner.wait_for_services → v8.examples.docker_uri_flow.orchestrator.flow_runner.json_get
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.validate_flow_registry
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.wait_for_services
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.load_registry
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.resolve_payload
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.json_post
  v8.examples.docker_uri_flow.orchestrator.flow_runner.main → v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_flow
  v8.examples.docker_uri_flow.orchestrator.flow_runner.main → v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow
  v2.examples.generators.php.example.UriCommand.bindingFromFunction → v2.examples.generators.php.example.UriCommand.schemaType
  v2.examples.transports.transport_lib.run_via → v2.examples.transports.transport_lib.run_inprocess
```

## Test Contracts

*Scenarios as contract signatures — what the system guarantees.*

### Integration (1)

**`Auto-generated from Python Tests`**

## Refactoring Analysis

*Pre-refactoring snapshot — use this section to identify targets. Generated from `project/` toon files.*

### Call Graph & Complexity (`project/calls.toon.yaml`)

```toon markpact:analysis path=project/calls.toon.yaml
# code2llm call graph | /home/tom/github/tellmesh/urihandler
# generated in 0.18s
# nodes: 410 | edges: 500 | modules: 32
# CC̄=3.8

HUBS[20]:
  v2.examples.device_mesh_lab.controller.normalize_flow
    CC=20  in:4  out:35  total:39
  v2.examples.device_mesh_lab.device_agent.DeviceAgent.handler
    CC=1  in:0  out:32  total:32
  adapters.python.urirun._scan.scan_path
    CC=15  in:4  out:27  total:31
  v2.examples.device_mesh_lab.mesh_env.send_json
    CC=1  in:18  out:12  total:30
  adapters.python.urirun._scan.normalize_binding
    CC=11  in:17  out:12  total:29
  v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_flow
    CC=24  in:1  out:26  total:27
  adapters.python.urirun.v2.validate_binding_document
    CC=12  in:2  out:24  total:26
  adapters.python.urirun.v1.run
    CC=14  in:2  out:23  total:25
  v2.examples.transports.transport_lib.start_http_worker
    CC=1  in:1  out:24  total:25
  v2.examples.device_mesh_lab.controller.Handler.do_POST
    CC=12  in:0  out:24  total:24
  adapters.python.urirun.v2_mcp.serve_mcp
    CC=15  in:1  out:23  total:24
  adapters.python.urirun.v2.scan_artifacts
    CC=11  in:4  out:19  total:23
  adapters.python.urirun.v2.run
    CC=15  in:1  out:22  total:23
  v2.examples.device_mesh_lab.www.app.escapeHtml
    CC=1  in:20  out:2  total:22
  adapters.python.urirun._runtime.evaluate_policy
    CC=16  in:3  out:19  total:22
  adapters.python.urirun._registry.discover_manifest
    CC=14  in:2  out:19  total:21
  adapters.python.urirun._runtime.run
    CC=10  in:1  out:20  total:21
  v2.examples.html_uri_app.backend.Handler.do_GET
    CC=8  in:0  out:21  total:21
  v2.examples.device_mesh_lab.controller.fallback_steps
    CC=33  in:1  out:19  total:20
  adapters.python.urirun._registry.discover_docker_labels
    CC=14  in:2  out:18  total:20

MODULES:
  adapters.c.urirun  [3 funcs]
    copy_token  CC=2  out:1
    is_path_end  CC=3  out:0
    memcpy  CC=1  out:1
  adapters.c.urirun_test  [2 funcs]
    assert  CC=1  out:0
    main  CC=2  out:3
  adapters.js  [5 funcs]
    buildInvocation  CC=1  out:2
    dispatch  CC=3  out:4
    fn  CC=2  out:1
    match  CC=2  out:1
    parseUri  CC=8  out:9
  adapters.python.urihandler  [3 funcs]
    build_invocation  CC=1  out:2
    dispatch  CC=4  out:10
    parse_uri  CC=7  out:13
  adapters.python.urirun._registry  [35 funcs]
    _default_openapi_route  CC=9  out:11
    _discover_python_module  CC=1  out:2
    _emit_json  CC=3  out:3
    _get_route_entry  CC=1  out:0
    _iter_module_exports  CC=6  out:8
    _load_sources  CC=2  out:3
    _operation_from_method  CC=1  out:1
    _route_entry_equal  CC=2  out:2
    _walk_route_entries  CC=5  out:3
    add_route  CC=5  out:6
  adapters.python.urirun._runtime  [11 funcs]
    _matches_any  CC=3  out:1
    _truncate  CC=3  out:2
    check  CC=1  out:7
    default_policy  CC=1  out:0
    evaluate_policy  CC=16  out:19
    list_routes  CC=4  out:10
    merge_policy  CC=7  out:8
    run  CC=10  out:20
    run_local_function  CC=2  out:6
    run_shell_template  CC=3  out:11
  adapters.python.urirun._scan  [33 funcs]
    _read_toml  CC=12  out:17
    binding_to_route_source  CC=3  out:3
    build_binding_document  CC=3  out:6
    compile_registry_document  CC=4  out:5
    emit_json  CC=3  out:3
    github_dependency_binding  CC=4  out:3
    infer_kind  CC=12  out:11
    iter_project_files  CC=5  out:4
    list_bindings  CC=2  out:3
    load_binding_source  CC=5  out:11
  adapters.python.urirun.v1  [19 funcs]
    _binding_pairs  CC=8  out:11
    _env_flags  CC=3  out:5
    _has_placeholders  CC=2  out:3
    _params_spec  CC=4  out:3
    _proc_env  CC=3  out:6
    _run_process  CC=1  out:8
    compile_registry  CC=1  out:2
    expand_binding  CC=7  out:6
    expand_bindings  CC=2  out:2
    load_registry_arg  CC=4  out:9
  adapters.python.urirun.v2  [43 funcs]
    _apply_defaults  CC=14  out:12
    _binding_pairs  CC=8  out:11
    _bindings_as_map  CC=2  out:2
    _coerce_default  CC=4  out:3
    _empty_input_schema  CC=1  out:0
    _input_values  CC=4  out:8
    _iter_files  CC=5  out:4
    _load_manifest  CC=1  out:2
    _load_many  CC=3  out:7
    _manifest_candidates  CC=2  out:3
  adapters.python.urirun.v2_adopt  [5 funcs]
    _command_binding  CC=2  out:2
    installed_python_bindings  CC=4  out:3
    npm_package_bindings  CC=4  out:12
    passthrough_schema  CC=2  out:1
    python_package_bindings  CC=4  out:6
  adapters.python.urirun.v2_grpc  [8 funcs]
    _method  CC=2  out:1
    _route_list  CC=2  out:5
    _validate  CC=5  out:4
    call  CC=6  out:7
    channel_target  CC=3  out:3
    list_routes  CC=1  out:3
    serve  CC=2  out:17
    stream  CC=4  out:7
  adapters.python.urirun.v2_mcp  [9 funcs]
    _input_schema  CC=4  out:3
    build_tool_index  CC=2  out:1
    call_tool  CC=3  out:4
    main  CC=9  out:16
    serve_mcp  CC=15  out:23
    to_a2a_card  CC=4  out:9
    to_mcp_manifest  CC=4  out:2
    to_mcp_tools  CC=4  out:7
    tool_name  CC=1  out:4
  adapters.python.urirun.v2_service  [3 funcs]
    _post  CC=3  out:10
    call  CC=9  out:10
    service_base  CC=3  out:4
  examples.reference_adapters.firmware-pseudo  [2 funcs]
    handle_uri  CC=7  out:3
    led_set  CC=1  out:0
  examples.reference_adapters.node-server  [3 funcs]
    readJson  CC=3  out:4
    server  CC=4  out:5
    writeJson  CC=1  out:4
  examples.reference_adapters.python-server  [1 funcs]
    do_POST  CC=5  out:11
  v1.examples.html_uri_app.app  [2 funcs]
    appendLog  CC=1  out:4
    text  CC=1  out:1
  v1.examples.html_uri_app.uri-runtime-v1  [29 funcs]
    activePolicy  CC=1  out:1
    adapter  CC=3  out:1
    allowed  CC=4  out:1
    compileBindings  CC=4  out:4
    createUriRuntimeV1  CC=32  out:17
    defaultPolicy  CC=1  out:0
    dispatch  CC=17  out:8
    entries  CC=1  out:0
    evaluatePolicy  CC=18  out:3
    expandBinding  CC=10  out:1
  v1.examples.js.urirun-v1  [34 funcs]
    DEFAULT_TIMEOUT  CC=5  out:11
    OUTPUT_LIMIT  CC=5  out:11
    allow  CC=2  out:2
    check  CC=5  out:7
    compileRegistry  CC=1  out:2
    compileRegistryDocument  CC=5  out:3
    defaultAdapter  CC=2  out:0
    deny  CC=2  out:2
    envFlags  CC=3  out:4
    evaluatePolicy  CC=6  out:4
  v2.examples.decorators.example  [3 funcs]
    echo_message  CC=1  out:1
    shell_echo  CC=1  out:1
    transcode  CC=1  out:1
  v2.examples.device_mesh_lab.controller  [26 funcs]
    do_GET  CC=2  out:5
    do_OPTIONS  CC=1  out:1
    do_POST  CC=12  out:24
    append_step_if_missing  CC=7  out:6
    build_registry  CC=5  out:3
    discover_device  CC=6  out:9
    discover_mesh  CC=5  out:6
    execute_flow  CC=9  out:15
    fallback_flow  CC=1  out:4
    fallback_steps  CC=33  out:19
  v2.examples.device_mesh_lab.device_agent  [5 funcs]
    handler  CC=1  out:32
    routes  CC=1  out:12
    main  CC=1  out:6
    make_agent_from_env  CC=3  out:12
    object_schema  CC=2  out:0
  v2.examples.device_mesh_lab.mesh_env  [5 funcs]
    auth_headers  CC=2  out:1
    auth_token  CC=1  out:2
    check_auth  CC=2  out:2
    parse_peers  CC=8  out:14
    send_json  CC=1  out:12
  v2.examples.device_mesh_lab.www.app  [51 funcs]
    appendTimeline  CC=3  out:3
    data  CC=2  out:1
    defaultValueFor  CC=20  out:2
    description  CC=3  out:1
    deviceRows  CC=2  out:1
    escapeHtml  CC=1  out:2
    extractRunResult  CC=10  out:0
    filter  CC=3  out:1
    focusArea  CC=3  out:6
    focusTargetFor  CC=2  out:0
  v2.examples.generators.php.example  [2 funcs]
    bindingFromFunction  CC=2  out:9
    schemaType  CC=2  out:3
  v2.examples.html_uri_app.backend  [14 funcs]
    do_GET  CC=8  out:21
    do_POST  CC=4  out:10
    log_message  CC=1  out:1
    add_log  CC=2  out:2
    binding_document  CC=1  out:2
    dispatch  CC=6  out:14
    dispatch_tool  CC=7  out:13
    env_bool  CC=1  out:2
    json_response  CC=1  out:9
    load_env  CC=6  out:10
  v2.examples.transports.transport_lib  [8 funcs]
    available_transports  CC=4  out:1
    build_registry  CC=1  out:3
    grpc_available  CC=2  out:0
    run_inprocess  CC=2  out:1
    run_queue  CC=1  out:10
    run_via  CC=6  out:16
    serverless_handler  CC=1  out:2
    start_http_worker  CC=1  out:24
  v8.examples.docker_uri_flow.node-worker.server  [6 funcs]
    body  CC=2  out:1
    readBody  CC=2  out:4
    send  CC=1  out:4
    server  CC=10  out:4
    slug  CC=1  out:1
    slugify  CC=1  out:4
  v8.examples.docker_uri_flow.orchestrator.flow_runner  [16 funcs]
    get_path  CC=2  out:1
    json_get  CC=1  out:4
    json_post  CC=1  out:7
    load_registry  CC=3  out:4
    main  CC=3  out:5
    normalize_uri  CC=6  out:7
    parse_flow  CC=24  out:26
    parse_scalar  CC=3  out:2
    registry_has_uri  CC=4  out:9
    registry_route_count  CC=5  out:9
  v8.examples.docker_uri_flow.python-worker.server  [5 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=3  out:2
    normalize  CC=1  out:6
    summary  CC=1  out:2
  v8.examples.docker_uri_flow.shell-worker.server  [4 funcs]
    do_GET  CC=3  out:3
    do_POST  CC=6  out:11
    dispatch  CC=2  out:5
    response  CC=1  out:9
  v8.examples.html_uri_app.app  [15 funcs]
    card  CC=2  out:2
    classFor  CC=1  out:2
    data  CC=2  out:1
    defaults  CC=8  out:5
    escapeHtml  CC=1  out:2
    iconFor  CC=2  out:3
    inputType  CC=2  out:2
    payloadDefaults  CC=4  out:0
    refreshLogs  CC=5  out:7
    renderActions  CC=5  out:5

EDGES:
  examples.reference_adapters.node-server.server → examples.reference_adapters.node-server.writeJson
  examples.reference_adapters.node-server.server → examples.reference_adapters.node-server.readJson
  examples.reference_adapters.python-server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.dispatch
  examples.reference_adapters.firmware-pseudo.handle_uri → examples.reference_adapters.firmware-pseudo.led_set
  v8.examples.html_uri_app.app.routeResponse → v8.examples.html_uri_app.app.renderActions
  v8.examples.html_uri_app.app.routeResponse → v8.examples.html_uri_app.app.renderForm
  v8.examples.html_uri_app.app.renderActions → v8.examples.html_uri_app.app.classFor
  v8.examples.html_uri_app.app.renderActions → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.renderActions → v8.examples.html_uri_app.app.iconFor
  v8.examples.html_uri_app.app.renderForm → v8.examples.html_uri_app.app.schemaFor
  v8.examples.html_uri_app.app.renderForm → v8.examples.html_uri_app.app.payloadDefaults
  v8.examples.html_uri_app.app.renderForm → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.required → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.defaults → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.inputType → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.refreshLogs → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.data → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.card → v8.examples.html_uri_app.app.renderToolList
  v8.examples.html_uri_app.app.renderToolList → v8.examples.html_uri_app.app.escapeHtml
  v8.examples.html_uri_app.app.iconFor → v8.examples.html_uri_app.app.classFor
  v8.examples.docker_uri_flow.shell-worker.server.Handler.do_GET → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.shell-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.dispatch
  v8.examples.docker_uri_flow.shell-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.node-worker.server.server → v8.examples.docker_uri_flow.node-worker.server.send
  v8.examples.docker_uri_flow.node-worker.server.server → v8.examples.docker_uri_flow.node-worker.server.readBody
  v8.examples.docker_uri_flow.node-worker.server.server → v8.examples.docker_uri_flow.node-worker.server.slugify
  v8.examples.docker_uri_flow.node-worker.server.body → v8.examples.docker_uri_flow.node-worker.server.send
  v8.examples.docker_uri_flow.node-worker.server.slug → v8.examples.docker_uri_flow.node-worker.server.send
  v8.examples.docker_uri_flow.python-worker.server.dispatch → v8.examples.docker_uri_flow.python-worker.server.normalize
  v8.examples.docker_uri_flow.python-worker.server.dispatch → v8.examples.docker_uri_flow.python-worker.server.summary
  v8.examples.docker_uri_flow.python-worker.server.Handler.do_GET → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.python-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.dispatch
  v8.examples.docker_uri_flow.python-worker.server.Handler.do_POST → v8.examples.docker_uri_flow.shell-worker.server.response
  v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_scalar
  v8.examples.docker_uri_flow.orchestrator.flow_runner.resolve_payload → v8.examples.docker_uri_flow.orchestrator.flow_runner.get_path
  v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_has_uri → v8.examples.docker_uri_flow.orchestrator.flow_runner.route_key
  v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_has_uri → v8.examples.docker_uri_flow.orchestrator.flow_runner.normalize_uri
  v8.examples.docker_uri_flow.orchestrator.flow_runner.validate_flow_registry → v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_route_count
  v8.examples.docker_uri_flow.orchestrator.flow_runner.validate_flow_registry → v8.examples.docker_uri_flow.orchestrator.flow_runner.registry_has_uri
  v8.examples.docker_uri_flow.orchestrator.flow_runner.wait_for_services → v8.examples.docker_uri_flow.orchestrator.flow_runner.service_url
  v8.examples.docker_uri_flow.orchestrator.flow_runner.wait_for_services → v8.examples.docker_uri_flow.orchestrator.flow_runner.json_get
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.validate_flow_registry
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.wait_for_services
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.load_registry
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.resolve_payload
  v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow → v8.examples.docker_uri_flow.orchestrator.flow_runner.json_post
  v8.examples.docker_uri_flow.orchestrator.flow_runner.main → v8.examples.docker_uri_flow.orchestrator.flow_runner.parse_flow
  v8.examples.docker_uri_flow.orchestrator.flow_runner.main → v8.examples.docker_uri_flow.orchestrator.flow_runner.run_flow
  v2.examples.generators.php.example.UriCommand.bindingFromFunction → v2.examples.generators.php.example.UriCommand.schemaType
  v2.examples.transports.transport_lib.run_via → v2.examples.transports.transport_lib.run_inprocess
```

### Code Analysis (`project/analysis.toon.yaml`)

```toon markpact:analysis path=project/analysis.toon.yaml
# code2llm | 107f 10137L | python:24,json:23,javascript:18,shell:12,yaml:5,yml:3,c:2,txt:2,toml:2,typescript:1,php:1,cpp:1 | 2026-06-19
# generated in 0.03s
# CC̅=3.8 | critical:21/649 | dups:3 | cycles:0

HEALTH[20]:
  🔴 DUP   3 classes duplicated
  🟡 CC    parse_flow CC=24 (limit:15)
  🟡 CC    run CC=15 (limit:15)
  🟡 CC    expand_binding CC=16 (limit:15)
  🟡 CC    main CC=21 (limit:15)
  🟡 CC    evaluate_policy CC=16 (limit:15)
  🟡 CC    serve_mcp CC=15 (limit:15)
  🟡 CC    scan_path CC=15 (limit:15)
  🟡 CC    resolveParams CC=15 (limit:15)
  🟡 CC    run CC=19 (limit:15)
  🟡 CC    fallback_steps CC=33 (limit:15)
  🟡 CC    postprocess_flow CC=20 (limit:15)
  🟡 CC    normalize_flow CC=20 (limit:15)
  🟡 CC    dispatch CC=27 (limit:15)
  🟡 CC    defaultValueFor CC=20 (limit:15)
  🟡 CC    renderDevices CC=15 (limit:15)
  🟡 CC    reachable CC=15 (limit:15)
  🟡 CC    renderField CC=15 (limit:15)
  🟡 CC    resolveParams CC=15 (limit:15)
  🟡 CC    evaluatePolicy CC=18 (limit:15)

REFACTOR[2]:
  1. rm duplicates  (-3 dup classes)
  2. split 19 high-CC methods  (CC>15)

PIPELINES[238]:
  [1] Src [raw]: raw
      PURITY: 100% pure
  [2] Src [server]: server → writeJson
      PURITY: 100% pure
  [3] Src [do_POST]: do_POST → dispatch
      PURITY: 100% pure
  [4] Src [write_json]: write_json
      PURITY: 100% pure
  [5] Src [handle_uri]: handle_uri → led_set
      PURITY: 100% pure
  [6] Src [bindings]: bindings
      PURITY: 100% pure
  [7] Src [routeResponse]: routeResponse → renderActions → classFor
      PURITY: 100% pure
  [8] Src [button]: button
      PURITY: 100% pure
  [9] Src [result]: result
      PURITY: 100% pure
  [10] Src [required]: required → escapeHtml
      PURITY: 100% pure
  [11] Src [defaults]: defaults → escapeHtml
      PURITY: 100% pure
  [12] Src [inputType]: inputType → escapeHtml
      PURITY: 100% pure
  [13] Src [payloadFromForm]: payloadFromForm
      PURITY: 100% pure
  [14] Src [refreshLogs]: refreshLogs → escapeHtml
      PURITY: 100% pure
  [15] Src [data]: data → escapeHtml
      PURITY: 100% pure
  [16] Src [manifest]: manifest
      PURITY: 100% pure
  [17] Src [card]: card → renderToolList → escapeHtml
      PURITY: 100% pure
  [18] Src [key]: key
      PURITY: 100% pure
  [19] Src [do_GET]: do_GET → response
      PURITY: 100% pure
  [20] Src [do_POST]: do_POST → dispatch
      PURITY: 100% pure
  [21] Src [http]: http
      PURITY: 100% pure
  [22] Src [fs]: fs
      PURITY: 100% pure
  [23] Src [path]: path
      PURITY: 100% pure
  [24] Src [bindings]: bindings
      PURITY: 100% pure
  [25] Src [data]: data
      PURITY: 100% pure
  [26] Src [server]: server → send
      PURITY: 100% pure
  [27] Src [body]: body → send
      PURITY: 100% pure
  [28] Src [slug]: slug → send
      PURITY: 100% pure
  [29] Src [response]: response
      PURITY: 100% pure
  [30] Src [dispatch]: dispatch → normalize
      PURITY: 100% pure
  [31] Src [do_GET]: do_GET → response
      PURITY: 100% pure
  [32] Src [do_POST]: do_POST → dispatch
      PURITY: 100% pure
  [33] Src [main]: main → parse_flow → parse_scalar
      PURITY: 100% pure
  [34] Src [serve_http]: serve_http → discovery
      PURITY: 100% pure
  [35] Src [serve_grpc]: serve_grpc
      PURITY: 100% pure
  [36] Src [greet]: greet
      PURITY: 100% pure
  [37] Src [document]: document
      PURITY: 100% pure
  [38] Src [uriCommand]: uriCommand
      PURITY: 100% pure
  [39] Src [placeholders]: placeholders
      PURITY: 100% pure
  [40] Src [required]: required
      PURITY: 100% pure
  [41] Src [properties]: properties
      PURITY: 100% pure
  [42] Src [bindingDocument]: bindingDocument
      PURITY: 100% pure
  [43] Src [uriCommand]: uriCommand
      PURITY: 100% pure
  [44] Src [method]: method
      PURITY: 100% pure
  [45] Src [placeholders]: placeholders
      PURITY: 100% pure
  [46] Src [properties]: properties
      PURITY: 100% pure
  [47] Src [add]: add
      PURITY: 100% pure
  [48] Src [bindingFromFunction]: bindingFromFunction → schemaType
      PURITY: 100% pure
  [49] Src [sha256]: sha256
      PURITY: 100% pure
  [50] Src [document]: document
      PURITY: 100% pure

LAYERS:
  adapters/                       CC̄=4.6    ←in:4  →out:0
  │ !! v2                         955L  0C   49m  CC=21     ←2
  │ !! _registry                  679L  0C   41m  CC=14     ←0
  │ !! _scan                      667L  0C   36m  CC=15     ←0
  │ v1                         420L  0C   24m  CC=14     ←2
  │ !! _runtime                   418L  1C   18m  CC=16     ←0
  │ v2_grpc                    202L  0C   11m  CC=9      ←0
  │ v2_adopt                   192L  0C    8m  CC=7      ←0
  │ !! v2_mcp                     176L  0C    9m  CC=15     ←1
  │ v2_service                 100L  0C    3m  CC=9      ←0
  │ pyproject.toml              56L  0C    0m  CC=0.0    ←0
  │ index.test.js               49L  0C    1m  CC=1      ←0
  │ index.js                    30L  0C   11m  CC=8      ←4
  │ urirun_test.c               18L  0C    2m  CC=2      ←0
  │ urirun.h                    13L  0C    1m  CC=1      ←0
  │ package.json                10L  0C    0m  CC=0.0    ←0
  │ urirun.c                     0L  0C    4m  CC=5      ←0
  │ __init__                     0L  0C    3m  CC=7      ←0
  │
  v2/                             CC̄=3.5    ←in:0  →out:0  ×DUP
  │ !! registry.json              806L  0C    0m  CC=0.0    ←0
  │ !! app.js                     559L  0C   91m  CC=20     ←5
  │ !! controller                 482L  1C   27m  CC=33     ←0
  │ !! device_agent               390L  1C   16m  CC=27     ←0
  │ backend                    227L  1C   18m  CC=8      ←2  ×DUP
  │ transport_lib              152L  0C    8m  CC=6      ←1
  │ bindings.v2.example.json   151L  0C    0m  CC=0.0    ←0
  │ worker                      77L  0C    3m  CC=2      ←0
  │ mesh_env                    75L  0C    7m  CC=9      ←2
  │ bindings.json               74L  0C    0m  CC=0.0    ←0
  │ example.php                 64L  1C    4m  CC=2      ←0
  │ decorators.ts               62L  1C    5m  CC=1      ←0
  │ scan_and_run                49L  0C    1m  CC=6      ←0
  │ docker-compose.yml          48L  0C    0m  CC=0.0    ←0
  │ uri-command.mjs             44L  0C    8m  CC=4      ←0
  │ web-bindings.json           36L  0C    0m  CC=0.0    ←0
  │ docker-compose.test.yml     34L  0C    0m  CC=0.0    ←0
  │ docker-compose.test.yml     33L  0C    0m  CC=0.0    ←0
  │ bindings.json               31L  0C    0m  CC=0.0    ←0
  │ registry.bindings.json      28L  0C    0m  CC=0.0    ←0
  │ generate_registry.sh        26L  0C    0m  CC=0.0    ←0
  │ example                     24L  0C    3m  CC=1      ←0
  │ rpc-bindings.json           24L  0C    0m  CC=0.0    ←0
  │ Makefile                    20L  0C    0m  CC=0.0    ←0
  │ bindings.json               20L  0C    0m  CC=0.0    ←0
  │ routes.txt                  18L  0C    0m  CC=0.0    ←0
  │ urirun.manifest.json        18L  0C    0m  CC=0.0    ←0
  │ bindings.json               18L  0C    0m  CC=0.0    ←0
  │ Dockerfile                  15L  0C    0m  CC=0.0    ←0
  │ test.mjs                    13L  0C    2m  CC=1      ←1
  │ run_tests.sh                13L  0C    1m  CC=0.0    ←0
  │ Dockerfile                  12L  0C    0m  CC=0.0    ←0
  │ runtime-config.js           10L  0C    1m  CC=2      ←0
  │ Dockerfile                  10L  0C    0m  CC=0.0    ←0
  │ runtime-config.js            9L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   9L  0C    0m  CC=0.0    ←0
  │ Dockerfile                   7L  0C    0m  CC=0.0    ←0
  │ pyproject.toml               6L  0C    0m  CC=0.0    ←0
  │ package.json                 6L  0C    0m  CC=0.0    ←0
  │
  v1/                             CC̄=3.3    ←in:0  →out:0
  │ !! urirun-v1.js               331L  0C   54m  CC=19     ←4
  │ !! uri-runtime-v1.js          238L  0C   47m  CC=32     ←0
  │ app.js                     185L  0C   35m  CC=7      ←0
  │ bindings.json               66L  0C    0m  CC=0.0    ←0
  │ urirun-v1.test.js           64L  0C    2m  CC=1      ←0
  │ test.mjs                    54L  0C    9m  CC=1      ←0
  │ example.js                  22L  0C    3m  CC=1      ←1
  │ bash-function.bindings.json    22L  0C    0m  CC=0.0    ←0
  │ example                     21L  0C    0m  CC=0.0    ←0
  │ policy.json                 19L  0C    0m  CC=0.0    ←0
  │ run.sh                      17L  0C    0m  CC=0.0    ←0
  │ lib.sh                      11L  0C    2m  CC=0.0    ←0
  │
  v8/                             CC̄=3.1    ←in:0  →out:0  ×DUP
  │ app.js                       0L  0C   24m  CC=10     ←0
  │ run.sh                       0L  0C    1m  CC=0.0    ←0
  │ server                       0L  1C    5m  CC=6      ←3  ×DUP
  │ server.js                    0L  0C   11m  CC=10     ←0
  │ server                       0L  1C    7m  CC=6      ←0  ×DUP
  │ !! flow_runner                  0L  0C   16m  CC=24     ←0
  │ run_tests.sh                 0L  0C    1m  CC=0.0    ←0
  │ example.mjs                  0L  0C    2m  CC=1      ←0
  │ generate-bindings.mjs        0L  0C    3m  CC=2      ←0
  │ deploy.sh                    0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ package.json                 0L  0C    0m  CC=0.0    ←0
  │ run.sh                       0L  0C    0m  CC=0.0    ←0
  │ registry.json                0L  0C    0m  CC=0.0    ←0
  │ routes.txt                   0L  0C    0m  CC=0.0    ←0
  │ bindings.v8.json             0L  0C    0m  CC=0.0    ←0
  │ write_report.sh              0L  0C    0m  CC=0.0    ←0
  │ cross_service_report.yaml     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ Makefile                     0L  0C    0m  CC=0.0    ←0
  │ demo                         0L  0C    0m  CC=0.0    ←0
  │
  examples/                       CC̄=2.5    ←in:0  →out:0
  │ python-server               51L  2C    4m  CC=5      ←0
  │ node-server.js              43L  0C    5m  CC=4      ←0
  │ firmware-pseudo.c           12L  0C    2m  CC=7      ←0
  │
  ./                              CC̄=0.0    ←in:0  →out:0
  │ !! goal.yaml                  526L  0C    0m  CC=0.0    ←0
  │ planfile.yaml              487L  0C    0m  CC=0.0    ←0
  │ prefact.yaml                94L  0C    0m  CC=0.0    ←0
  │ Makefile                    65L  0C    0m  CC=0.0    ←0
  │ project.sh                  63L  0C    0m  CC=0.0    ←0
  │ package.json                28L  0C    0m  CC=0.0    ←0
  │ tree.sh                      1L  0C    0m  CC=0.0    ←0
  │
  testql-scenarios/               CC̄=0.0    ←in:0  →out:0
  │ generated-from-pytests.testql.toon.yaml    14L  0C    0m  CC=0.0    ←0
  │
  v7/                             CC̄=0.0    ←in:0  →out:0
  │ bindings.v7.example.json     0L  0C    0m  CC=0.0    ←0
  │ base.bindings.json           0L  0C    0m  CC=0.0    ←0
  │ new-script.bindings.json     0L  0C    0m  CC=0.0    ←0
  │ http-request.bindings.json     0L  0C    0m  CC=0.0    ←0
  │ notify.sh                    0L  0C    0m  CC=0.0    ←0
  │
  ── zero ──
     adapters/c/urirun.c                       0L
     adapters/python/urihandler/__init__.py    0L
     v7/examples/extend/base.bindings.json     0L
     v7/examples/extend/http-request.bindings.json  0L
     v7/examples/extend/new-script.bindings.json  0L
     v7/examples/extend/notify.sh              0L
     v7/examples/json/bindings.v7.example.json  0L
     v8/examples/artifacts/Makefile            0L
     v8/examples/artifacts/deploy.sh           0L
     v8/examples/artifacts/package.json        0L
     v8/examples/docker_uri_flow/flows/cross_service_report.yaml  0L
     v8/examples/docker_uri_flow/generated/bindings.v8.json  0L
     v8/examples/docker_uri_flow/generated/registry.json  0L
     v8/examples/docker_uri_flow/generated/routes.txt  0L
     v8/examples/docker_uri_flow/node-worker/server.js  0L
     v8/examples/docker_uri_flow/orchestrator/flow_runner.py  0L
     v8/examples/docker_uri_flow/python-worker/server.py  0L
     v8/examples/docker_uri_flow/run.sh        0L
     v8/examples/docker_uri_flow/shell-worker/server.py  0L
     v8/examples/docker_uri_flow/shell-worker/write_report.sh  0L
     v8/examples/generators/js/example.mjs     0L
     v8/examples/generators/nodejs/generate-bindings.mjs  0L
     v8/examples/html_uri_app/app.js           0L
     v8/examples/html_uri_app/run.sh           0L
     v8/examples/multi_transport/Makefile      0L
     v8/examples/multi_transport/run_tests.sh  0L
     v8/examples/transports/Makefile           0L
     v8/examples/transports/demo.py            0L

COUPLING:
                                           adapters.python                  v2.examples                  v1.examples                     adapters                  v8.examples  examples.reference_adapters
              adapters.python                           ──                            3                            6                            4                                                            hub
                  v2.examples                            9                           ──                            2                                                         1                               !! fan-out
                  v1.examples                           ←6                           ←2                           ──                                                                                         hub
                     adapters                           ←4                                                                                     ──                                                          
                  v8.examples                                                        ←1                                                                                     ──                           ←1
  examples.reference_adapters                                                                                                                                                1                           ──
  CYCLES: none
  HUB: adapters.python/ (fan-in=9)
  HUB: v1.examples/ (fan-in=8)
  SMELL: adapters.python/ fan-out=13 → split needed
  SMELL: v2.examples/ fan-out=12 → split needed

EXTERNAL:
  validation: run `vallm batch .` → validation.toon
  duplication: run `redup scan .` → duplication.toon
```

### Duplication (`project/duplication.toon.yaml`)

```toon markpact:analysis path=project/duplication.toon.yaml
# redup/duplication | 1 groups | 11f 1773L | 2026-06-19

SUMMARY:
  files_scanned: 11
  total_lines:   1773
  dup_groups:    1
  dup_fragments: 2
  saved_lines:   7
  scan_ms:       2533

HOTSPOTS[2] (files with most duplication):
  v2/examples/multi_transport/worker.py  dup=7L  groups=1  frags=1  (0.4%)
  v2/examples/transports/transport_lib.py  dup=7L  groups=1  frags=1  (0.4%)

DUPLICATES[1] (ranked by impact):
  [adcbcce722c5fe8d]   EXAC  _send  L=7 N=2 saved=7 sim=1.00
      v2/examples/multi_transport/worker.py:41-47  (_send)
      v2/examples/transports/transport_lib.py:79-85  (_send)

REFACTOR[1] (ranked by priority):
  [1] ○ extract_class      → v2/examples/utils/_send.py
      WHY: 2 occurrences of 7-line block across 2 files — saves 7 lines
      FILES: v2/examples/multi_transport/worker.py, v2/examples/transports/transport_lib.py

QUICK_WINS[1] (low risk, high savings — do first):
  [1] extract_class      saved=7L  → v2/examples/utils/_send.py
      FILES: worker.py, transport_lib.py

EFFORT_ESTIMATE (total ≈ 0.2h):
  easy   _send                               saved=7L  ~14min

METRICS-TARGET:
  dup_groups:  1 → 0
  saved_lines: 7 lines recoverable
```

### Evolution / Churn (`project/evolution.toon.yaml`)

```toon markpact:analysis path=project/evolution.toon.yaml
# code2llm/evolution | 221 func | 15f | 2026-06-19
# generated in 0.00s

NEXT[8] (ranked by impact):
  [1] !! SPLIT           adapters/python/urirun/v2.py
      WHY: 955L, 0 classes, max CC=21
      EFFORT: ~4h  IMPACT: 20055

  [2] !! SPLIT           adapters/python/urirun/_scan.py
      WHY: 667L, 0 classes, max CC=15
      EFFORT: ~4h  IMPACT: 10005

  [3] !! SPLIT           adapters/python/urirun/_registry.py
      WHY: 679L, 0 classes, max CC=14
      EFFORT: ~4h  IMPACT: 9506

  [4] !  SPLIT-FUNC      main  CC=21  fan=39
      WHY: CC=21 exceeds 15
      EFFORT: ~1h  IMPACT: 819

  [5] !  SPLIT-FUNC      scan_path  CC=15  fan=19
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 285

  [6] !  SPLIT-FUNC      run  CC=15  fan=14
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 210

  [7] !  SPLIT-FUNC      serve_mcp  CC=15  fan=14
      WHY: CC=15 exceeds 15
      EFFORT: ~1h  IMPACT: 210

  [8] !  SPLIT-FUNC      evaluate_policy  CC=16  fan=8
      WHY: CC=16 exceeds 15
      EFFORT: ~1h  IMPACT: 128


RISKS[3]:
  ⚠ Splitting adapters/python/urirun/v2.py may break 49 import paths
  ⚠ Splitting adapters/python/urirun/_registry.py may break 41 import paths
  ⚠ Splitting adapters/python/urirun/_scan.py may break 36 import paths

METRICS-TARGET:
  CC̄:          4.6 → ≤3.2
  max-CC:      21 → ≤10
  god-modules: 4 → 0
  high-CC(≥15): 6 → ≤3
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
  prev CC̄=4.6 → now CC̄=4.6
```

## Intent

urirun
