# System Architecture Analysis
<!-- generated in 0.00s -->

## Overview

- **Project**: /home/tom/github/tellmesh/urihandler
- **Primary Language**: python
- **Languages**: python: 18, yaml: 4, javascript: 3, shell: 2, json: 2
- **Analysis Mode**: static
- **Total Functions**: 455
- **Total Classes**: 4
- **Modules**: 33
- **Entry Points**: 120

## Architecture by Module

### v1.examples.js.urirun-v1
- **Functions**: 65
- **File**: `urirun-v1.js`

### adapters.python.urirun.v2
- **Functions**: 62
- **File**: `v2.py`

### adapters.python.urirun.mesh
- **Functions**: 51
- **File**: `mesh.py`

### adapters.python.urirun._registry
- **Functions**: 41
- **File**: `_registry.py`

### adapters.python.urirun._scan
- **Functions**: 36
- **File**: `_scan.py`

### adapters.python.urirun.host_db
- **Functions**: 27
- **File**: `host_db.py`

### adapters.python.urirun.v1
- **Functions**: 24
- **File**: `v1.py`

### adapters.python.urirun.planfile_adapter
- **Functions**: 21
- **Classes**: 1
- **File**: `planfile_adapter.py`

### adapters.python.urirun.namecheap_dns
- **Functions**: 20
- **File**: `namecheap_dns.py`

### adapters.python.urirun._runtime
- **Functions**: 18
- **Classes**: 1
- **File**: `_runtime.py`

### adapters.python.urirun.domain_monitor
- **Functions**: 17
- **File**: `domain_monitor.py`

### adapters.python.urirun.task_planner
- **Functions**: 13
- **Classes**: 2
- **File**: `task_planner.py`

### adapters.python.urirun.host_dashboard
- **Functions**: 12
- **File**: `host_dashboard.py`

### adapters.js
- **Functions**: 11
- **File**: `index.js`

### adapters.c.urirun_test
- **Functions**: 11
- **File**: `urirun_test.c`

### adapters.python.urirun.v2_grpc
- **Functions**: 11
- **File**: `v2_grpc.py`

### adapters.python.urirun.v2_mcp
- **Functions**: 9
- **File**: `v2_mcp.py`

### adapters.python.urirun.v2_adopt
- **Functions**: 8
- **File**: `v2_adopt.py`

### adapters.python.urirun.scheduler
- **Functions**: 6
- **File**: `scheduler.py`

### adapters.python.urirun.v2_service
- **Functions**: 3
- **File**: `v2_service.py`

## Key Entry Points

Main execution flows into the system:

### adapters.python.urirun.v2.main
- **Calls**: list, argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, scan_parser.add_argument, scan_parser.add_argument, scan_parser.add_argument, subparsers.add_parser

### adapters.python.urirun.v2.run_planfile_task
- **Calls**: dict, list, adapters.python.urirun.v2._planfile_action, adapters.python.urirun.v2._planfile_project, ValueError, planfile_adapter.list_tickets, planfile_adapter.next_ticket, planfile_adapter.get_ticket

### adapters.python.urirun._scan.main
- **Calls**: list, argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, scan.add_argument, scan.add_argument, scan.add_argument, scan.add_argument

### adapters.python.urirun.domain_monitor.run_uri_route
- **Calls**: dict, ValueError, adapters.python.urirun.domain_monitor._domain, adapters.python.urirun.domain_monitor._domain, namecheap_dns.run_uri_route, adapters.python.urirun.domain_monitor._domain, str, ctx.get

### adapters.python.urirun._registry.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, discover.add_subparsers, discover_sub.add_parser, p_manifest.add_argument, p_manifest.add_argument, p_manifest.add_argument

### adapters.python.urirun.host_db.run_uri_route
- **Calls**: dict, adapters.python.urirun.host_db.route_db_path, ValueError, ctx.get, adapters.python.urirun.host_db.list_datasets, adapters.python.urirun.host_db.search_records, adapters.python.urirun.host_db.read_only_sql, adapters.python.urirun.host_db.list_artifacts

### adapters.python.urirun.v1.main
- **Calls**: list, argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, add_source, run_parser.add_argument, run_parser.add_argument, run_parser.add_argument

### adapters.python.urirun._runtime.main
- **Calls**: list, argparse.ArgumentParser, parser.add_subparsers, subparsers.add_parser, add_source, run_parser.add_argument, run_parser.add_argument, run_parser.add_argument

### adapters.python.urirun.v2_adopt.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, py.add_argument, py.add_argument, sub.add_parser, npm.add_argument, npm.add_argument

### adapters.python.urirun.mesh.host_command
- **Calls**: adapters.python.urirun.mesh.load_host_config, adapters.python.urirun.mesh.discover_mesh, host_dashboard.command, reglib._emit_json, reglib._emit_json, adapters.python.urirun.mesh.data_command, adapters.python.urirun.mesh.monitor_command, adapters.python.urirun.mesh.task_command

### adapters.python.urirun.v2_grpc.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, sub.add_parser, s.add_argument, s.add_argument, s.add_argument, s.add_argument, s.add_argument

### adapters.python.urirun._runtime.run_fetch
- **Calls**: None.get, config.get, None.upper, dict, urllib.request.Request, ValueError, None.startswith, PolicyError

### adapters.python.urirun.mesh.node_command
- **Calls**: adapters.python.urirun.mesh.load_node_config, dict, v2.load_registry_arg, reglib._emit_json, reglib._emit_json, node.get, socket.gethostname, node.get

### adapters.python.urirun.namecheap_dns.run_uri_route
- **Calls**: dict, str, ValueError, payload.get, None.get, ValueError, adapters.python.urirun.namecheap_dns.current_records, ctx.get

### adapters.python.urirun.v2_mcp.main
- **Calls**: argparse.ArgumentParser, parser.add_subparsers, parser.parse_args, v2.load_registry_arg, sub.add_parser, p.add_argument, reglib._emit_json, reglib._emit_json

### adapters.python.urirun.v1.run_docker_run
- **Calls**: None.get, config.get, adapters.python.urirun.v1.render_command, config.get, flags.extend, ValueError, os.path.abspath, flags.extend

### adapters.python.urirun._registry.discover_entry_points
- **Calls**: metadata.entry_points, hasattr, eps.select, eps.get, entry_point.load, getattr, dict, entries.append

### adapters.python.urirun._runtime.run_shell_template
- **Calls**: None.get, enumerate, bool, subprocess.run, rendered.replace, policy.get, shlex.split, adapters.python.urirun._runtime._truncate

### adapters.python.urirun.planfile_adapter.fail_or_retry
> Fail a ticket, requeuing it for another run while attempts remain.

``Planfile.fail_ticket`` records the error, increments ``execution.attempt``
and s
- **Calls**: adapters.python.urirun.planfile_adapter.load_planfile, pf.fail_ticket, adapters.python.urirun.planfile_adapter.ticket_to_dict, dict, int, int, execution.get, execution.get

### v1.examples.js.urirun-v1.DEFAULT_TIMEOUT
- **Calls**: v1.examples.js.urirun-v1.String, v1.examples.js.urirun-v1.match, v1.examples.js.urirun-v1.Error, v1.examples.js.urirun-v1.split, v1.examples.js.urirun-v1.filter, v1.examples.js.urirun-v1.map, v1.examples.js.urirun-v1.fromEntries, v1.examples.js.urirun-v1.URLSearchParams

### v1.examples.js.urirun-v1.OUTPUT_LIMIT
- **Calls**: v1.examples.js.urirun-v1.String, v1.examples.js.urirun-v1.match, v1.examples.js.urirun-v1.Error, v1.examples.js.urirun-v1.split, v1.examples.js.urirun-v1.filter, v1.examples.js.urirun-v1.map, v1.examples.js.urirun-v1.fromEntries, v1.examples.js.urirun-v1.URLSearchParams

### adapters.python.urirun.v2.connector_bindings
> Return serializable bindings generated from decorated connector commands.

``decorated_bindings()`` intentionally keeps runtime-only objects such as t
- **Calls**: set, sorted, adapters.python.urirun.v2.expand_bindings, adapters.python.urirun.v2._document_binding_from_expanded, binding.get, adapters.python.urirun.v2.decorated_bindings, binding.get, isinstance

### adapters.python.urirun.v2_service.call
- **Calls**: reglib.parse_uri, reglib.translate, data.get, bool, adapters.python.urirun.v2_service._post, data.get, reglib.resolve_route, v2.validate_input

### adapters.python.urihandler.dispatch
- **Calls**: adapters.python.urihandler.parse_uri, adapters.python.urihandler.build_invocation, registry.get, adapters.js.fn, KeyError, getattr, mod.get, callable

### adapters.python.urirun._runtime.run_spawn
- **Calls**: None.get, subprocess.run, ValueError, adapters.python.urirun._runtime._truncate, adapters.python.urirun._runtime._truncate, str, str, policy.get

### adapters.python.urirun.host_db.add_llm_message
- **Calls**: adapters.python.urirun.host_db.init_db, adapters.python.urirun.host_db.new_id, adapters.python.urirun.host_db.connection, conn.execute, adapters.python.urirun.host_db.row_dict, None.fetchone, adapters.python.urirun.host_db.now_iso, json.dumps

### v1.examples.js.urirun-v1.run
- **Calls**: v1.examples.js.urirun-v1.mergePolicy, v1.examples.js.urirun-v1.parseUri, v1.examples.js.urirun-v1.translate, v1.examples.js.urirun-v1.registryTree, v1.examples.js.urirun-v1.Error, v1.examples.js.urirun-v1.join, v1.examples.js.urirun-v1.resolveParams, v1.examples.js.urirun-v1.evaluatePolicy

### adapters.python.urirun.host_db.create_llm_session
- **Calls**: adapters.python.urirun.host_db.init_db, adapters.python.urirun.host_db.new_id, adapters.python.urirun.host_db.connection, conn.execute, adapters.python.urirun.host_db.row_dict, None.fetchone, adapters.python.urirun.host_db.now_iso, conn.execute

### adapters.python.urirun.v1.run_docker_exec
- **Calls**: None.get, adapters.python.urirun.v1.render_command, config.get, flags.extend, flags.extend, adapters.python.urirun.v1._env_flags, adapters.python.urirun.v1._run_process, config.get

### adapters.python.urirun.v1.run_fetch
- **Calls**: dict, adapters.python.urirun.v1.render_value, None.upper, runtime.run_fetch, None.get, str, config.get, config.get

## Process Flows

Key execution flows identified:

### Flow 1: main
```
main [adapters.python.urirun.v2]
```

### Flow 2: run_planfile_task
```
run_planfile_task [adapters.python.urirun.v2]
  └─> _planfile_action
  └─> _planfile_project
```

### Flow 3: run_uri_route
```
run_uri_route [adapters.python.urirun.domain_monitor]
  └─> _domain
  └─> _domain
```

### Flow 4: host_command
```
host_command [adapters.python.urirun.mesh]
  └─> load_host_config
      └─> host_config_path
      └─> json_load
  └─> discover_mesh
      └─> discover_node
          └─> http_json
          └─> http_json
```

### Flow 5: run_fetch
```
run_fetch [adapters.python.urirun._runtime]
```

### Flow 6: node_command
```
node_command [adapters.python.urirun.mesh]
  └─> load_node_config
      └─> node_config_path
      └─> json_load
```

### Flow 7: run_docker_run
```
run_docker_run [adapters.python.urirun.v1]
  └─> render_command
      └─> render_value
```

### Flow 8: discover_entry_points
```
discover_entry_points [adapters.python.urirun._registry]
```

### Flow 9: run_shell_template
```
run_shell_template [adapters.python.urirun._runtime]
```

### Flow 10: fail_or_retry
```
fail_or_retry [adapters.python.urirun.planfile_adapter]
  └─> load_planfile
      └─> project_root
      └─> _imports
  └─> ticket_to_dict
      └─> _model_dict
```

## Key Classes

### adapters.python.urirun._runtime.PolicyError
> Raised when a route is blocked by policy in execute mode.
- **Methods**: 0
- **Inherits**: Exception

### adapters.python.urirun.task_planner.PlannedTicket
- **Methods**: 0
- **Inherits**: BaseModel

### adapters.python.urirun.task_planner.TaskPlanningResult
- **Methods**: 0
- **Inherits**: BaseModel

### adapters.python.urirun.planfile_adapter.PlanfileUnavailable
> Raised when the optional planfile package is not installed.
- **Methods**: 0
- **Inherits**: RuntimeError

## Data Transformation Functions

Key functions that process and transform data:

### adapters.js.parseUri
- **Output to**: adapters.js.String, adapters.js.match, adapters.js.Error, adapters.js.split, adapters.js.filter

### adapters.c.urirun.urirun_parse

### adapters.python.urirun.host_db._validate_record
- **Output to**: None.validate, dataset.get, Draft202012Validator

### adapters.python.urirun.v1._run_process
- **Output to**: subprocess.run, runtime._truncate, runtime._truncate, config.get, config.get

### adapters.python.urihandler.parse_uri
- **Output to**: URI_RE.match, str, ValueError, m.group, unquote

### adapters.python.urirun._runtime.format_route_table
- **Output to**: out.extend, None.join, max, None.rstrip, line

### adapters.python.urirun.v2_grpc._validate
> Return an error envelope if the URI/payload is invalid, else None.
- **Output to**: reglib.parse_uri, reglib.translate, reglib.resolve_route, v2.validate_input

### adapters.python.urirun.mesh.format_nodes
- **Output to**: adapters.python.urirun.mesh.format_table, len, len, rows.append, None.get

### adapters.python.urirun.mesh.format_routes
- **Output to**: adapters.python.urirun.mesh.format_table, sorted, adapters.python.urirun.mesh.safe_route, route.get, route.get

### adapters.python.urirun.mesh.format_tickets
- **Output to**: adapters.python.urirun.mesh.format_table, ticket.get, ticket.get, None.get, None.get

### adapters.python.urirun.mesh.format_table
- **Output to**: output.extend, None.join, max, None.rstrip, line

### adapters.python.urirun.mesh._parse_json_option
- **Output to**: json.loads

### adapters.python.urirun._registry.parse_uri
- **Output to**: URI_RE.match, unquote, str, ValueError, unquote

### adapters.python.urirun._registry._parse_command
- **Output to**: shlex.split, json.loads, isinstance, str

### adapters.python.urirun._scan.parse_compose_label_line
- **Output to**: None.strip, value.startswith, value.split, key.strip, None.strip

### adapters.python.urirun._scan.format_binding_table
- **Output to**: output.extend, None.join, max, None.rstrip, line

### adapters.python.urirun.namecheap_dns.parse_api_xml
- **Output to**: ET.fromstring, root.attrib.get, root.iter, adapters.python.urirun.namecheap_dns._strip_ns, errors.append

### v1.examples.js.urirun-v1.parseUri
- **Output to**: v1.examples.js.urirun-v1.String, v1.examples.js.urirun-v1.match, v1.examples.js.urirun-v1.Error, v1.examples.js.urirun-v1.split, v1.examples.js.urirun-v1.filter

### v1.examples.js.urirun-v1.runProcess
- **Output to**: v1.examples.js.urirun-v1.spawnSync, v1.examples.js.urirun-v1.renderedEnv, v1.examples.js.urirun-v1.truncate

### adapters.python.urirun.v2.validate_input
- **Output to**: adapters.python.urirun.v2._input_values, adapters.python.urirun.v2._schema_for, Draft202012Validator.check_schema, set, adapters.python.urirun.v2._apply_defaults

### adapters.python.urirun.v2.parse_param_declaration
> Parse a compact CLI param declaration.

Supported forms:
- ``name``
- ``name:type``
- ``name:type:re
- **Output to**: left.split, None.strip, None.get, declaration.split, ValueError

### adapters.python.urirun.v2.validate_binding_document
- **Output to**: adapters.python.urirun.v2.expand_bindings, binding.get, config.get, set, set

### adapters.python.urirun.v2._parse_dockerfile_labels
- **Output to**: re.compile, re.compile, None.splitlines, label_re.match, pair_re.findall

## Behavioral Patterns

### recursion__walk_route_entries
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: adapters.python.urirun._registry._walk_route_entries

### recursion__apply_defaults
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: adapters.python.urirun.v2._apply_defaults

### recursion__placeholders_in
- **Type**: recursion
- **Confidence**: 0.90
- **Functions**: adapters.python.urirun.v2._placeholders_in

## Public API Surface

Functions exposed as public API (no underscore prefix):

- `adapters.python.urirun.v2.main` - 314 calls
- `adapters.python.urirun.mesh.task_command` - 78 calls
- `adapters.python.urirun.v2.run_planfile_task` - 66 calls
- `adapters.python.urirun._scan.main` - 59 calls
- `adapters.python.urirun.domain_monitor.run_uri_route` - 57 calls
- `adapters.python.urirun._registry.main` - 56 calls
- `adapters.python.urirun.host_dashboard.create_handler` - 47 calls
- `adapters.python.urirun.host_db.run_uri_route` - 45 calls
- `adapters.python.urirun.v1.main` - 44 calls
- `adapters.python.urirun.planfile_adapter.build_ticket_payload` - 43 calls
- `adapters.python.urirun._runtime.main` - 33 calls
- `adapters.python.urirun.mesh.normalize_flow` - 31 calls
- `adapters.python.urirun.v2_adopt.main` - 31 calls
- `adapters.python.urirun.mesh.data_command` - 29 calls
- `adapters.python.urirun.task_planner.heuristic_plan_chat_request` - 27 calls
- `adapters.python.urirun._scan.scan_path` - 27 calls
- `adapters.python.urirun.mesh.host_command` - 26 calls
- `adapters.python.urirun.v2_grpc.main` - 25 calls
- `adapters.python.urirun.namecheap_dns.apply` - 25 calls
- `adapters.python.urirun.v2.validate_binding_document` - 24 calls
- `adapters.python.urirun.v1.run` - 23 calls
- `adapters.python.urirun._runtime.run_fetch` - 23 calls
- `adapters.python.urirun.host_dashboard.summary` - 23 calls
- `adapters.python.urirun.v2_mcp.serve_mcp` - 23 calls
- `adapters.python.urirun.mesh.serve_node` - 22 calls
- `adapters.python.urirun.namecheap_dns.config_from_env` - 22 calls
- `adapters.python.urirun.namecheap_dns.normalize_record` - 22 calls
- `adapters.python.urirun.v2.run` - 22 calls
- `adapters.python.urirun.host_db.search_records` - 21 calls
- `adapters.python.urirun.mesh.node_command` - 21 calls
- `adapters.python.urirun._runtime.run` - 20 calls
- `adapters.python.urirun.domain_monitor.check_domain` - 19 calls
- `adapters.python.urirun._runtime.evaluate_policy` - 19 calls
- `adapters.python.urirun.mesh.monitor_command` - 19 calls
- `adapters.python.urirun._registry.discover_manifest` - 19 calls
- `adapters.python.urirun.v2.scan_artifacts` - 19 calls
- `adapters.python.urirun._registry.discover_docker_labels` - 18 calls
- `adapters.python.urirun.v2_grpc.serve` - 17 calls
- `adapters.python.urirun._scan.format_binding_table` - 17 calls
- `adapters.python.urirun.namecheap_dns.parse_api_xml` - 17 calls

## System Interactions

How components interact:

```mermaid
graph TD
    main --> list
    main --> ArgumentParser
    main --> add_subparsers
    main --> add_parser
    main --> add_argument
    run_planfile_task --> dict
    run_planfile_task --> list
    run_planfile_task --> _planfile_action
    run_planfile_task --> _planfile_project
    run_planfile_task --> ValueError
    run_uri_route --> dict
    run_uri_route --> ValueError
    run_uri_route --> _domain
    run_uri_route --> run_uri_route
    run_uri_route --> route_db_path
    run_uri_route --> get
    run_uri_route --> list_datasets
    main --> add_source
    host_command --> load_host_config
    host_command --> discover_mesh
    host_command --> command
    host_command --> _emit_json
    run_fetch --> get
    run_fetch --> upper
    run_fetch --> dict
    run_fetch --> Request
    node_command --> load_node_config
    node_command --> dict
    node_command --> load_registry_arg
    node_command --> _emit_json
```

## Reverse Engineering Guidelines

1. **Entry Points**: Start analysis from the entry points listed above
2. **Core Logic**: Focus on classes with many methods
3. **Data Flow**: Follow data transformation functions
4. **Process Flows**: Use the flow diagrams for execution paths
5. **API Surface**: Public API functions reveal the interface

## Context for LLM

Maintain the identified architectural patterns and public API surface when suggesting changes.