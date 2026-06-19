% ── Project Metadata ─────────────────────────────────────
project_metadata('urihandler', '0.3.9', 'javascript').

% ── Project Files ────────────────────────────────────────
project_file('adapters/js/index.js', 31, 'javascript').
project_file('adapters/js/index.test.js', 50, 'javascript').
project_file('adapters/python/tests/test_domain_monitor.py', 159, 'python').
project_file('adapters/python/tests/test_host_dashboard.py', 94, 'python').
project_file('adapters/python/tests/test_host_db.py', 110, 'python').
project_file('adapters/python/tests/test_mesh.py', 61, 'python').
project_file('adapters/python/tests/test_namecheap_dns.py', 156, 'python').
project_file('adapters/python/tests/test_planfile_adapter.py', 340, 'python').
project_file('adapters/python/tests/test_scheduler.py', 59, 'python').
project_file('adapters/python/tests/test_urihandler.py', 85, 'python').
project_file('adapters/python/urirun/__init__.py', 39, 'python').
project_file('adapters/python/urirun/_registry.py', 680, 'python').
project_file('adapters/python/urirun/_runtime.py', 419, 'python').
project_file('adapters/python/urirun/_scan.py', 668, 'python').
project_file('adapters/python/urirun/domain_monitor.py', 381, 'python').
project_file('adapters/python/urirun/host_dashboard.py', 588, 'python').
project_file('adapters/python/urirun/host_db.py', 469, 'python').
project_file('adapters/python/urirun/mesh.py', 1072, 'python').
project_file('adapters/python/urirun/namecheap_dns.py', 289, 'python').
project_file('adapters/python/urirun/planfile_adapter.py', 259, 'python').
project_file('adapters/python/urirun/scheduler.py', 128, 'python').
project_file('adapters/python/urirun/task_planner.py', 342, 'python').
project_file('adapters/python/urirun/v1.py', 421, 'python').
project_file('adapters/python/urirun/v2.py', 1656, 'python').
project_file('adapters/python/urirun/v2_adopt.py', 193, 'python').
project_file('adapters/python/urirun/v2_grpc.py', 203, 'python').
project_file('adapters/python/urirun/v2_mcp.py', 177, 'python').
project_file('adapters/python/urirun/v2_service.py', 101, 'python').
project_file('app.doql.less', 79, 'less').
project_file('project.sh', 63, 'shell').
project_file('test/urirun.test.js', 8, 'javascript').
project_file('tree.sh', 2, 'shell').
project_file('v1/js/urirun-v1.js', 332, 'javascript').

% ── Python Functions ─────────────────────────────────────
python_function('adapters/python/tests/test_domain_monitor.py', 'local_http', 1, 1, 6).
python_function('adapters/python/tests/test_host_dashboard.py', 'get_json', 1, 1, 4).
python_function('adapters/python/tests/test_host_dashboard.py', 'post_json', 2, 1, 7).
python_function('adapters/python/urirun/__init__.py', 'parse_uri', 1, 7, 8).
python_function('adapters/python/urirun/__init__.py', 'build_invocation', 1, 1, 2).
python_function('adapters/python/urirun/__init__.py', 'dispatch', 3, 4, 8).
python_function('adapters/python/urirun/_registry.py', 'parse_uri', 1, 8, 10).
python_function('adapters/python/urirun/_registry.py', 'translate', 1, 2, 2).
python_function('adapters/python/urirun/_registry.py', 'hash_uri', 1, 1, 3).
python_function('adapters/python/urirun/_registry.py', 'default_adapter', 1, 3, 1).
python_function('adapters/python/urirun/_registry.py', 'normalize_route_entry', 1, 8, 4).
python_function('adapters/python/urirun/_registry.py', 'route_from_uri', 3, 2, 4).
python_function('adapters/python/urirun/_registry.py', 'route_from_parts', 6, 1, 2).
python_function('adapters/python/urirun/_registry.py', 'coerce_route_source', 2, 11, 7).
python_function('adapters/python/urirun/_registry.py', '_route_entry_equal', 2, 2, 1).
python_function('adapters/python/urirun/_registry.py', 'add_route', 4, 5, 5).
python_function('adapters/python/urirun/_registry.py', 'flatten_registry_tree', 2, 8, 4).
python_function('adapters/python/urirun/_registry.py', '_get_route_entry', 2, 1, 0).
python_function('adapters/python/urirun/_registry.py', 'flatten_registry_document', 2, 10, 6).
python_function('adapters/python/urirun/_registry.py', 'discover_manifest', 2, 14, 8).
python_function('adapters/python/urirun/_registry.py', 'build_registry_document', 3, 10, 13).
python_function('adapters/python/urirun/_registry.py', '_parse_command', 1, 4, 4).
python_function('adapters/python/urirun/_registry.py', 'discover_docker_labels', 2, 14, 10).
python_function('adapters/python/urirun/_registry.py', 'discover_docker_inspect', 1, 10, 4).
python_function('adapters/python/urirun/_registry.py', '_operation_from_method', 1, 1, 1).
python_function('adapters/python/urirun/_registry.py', '_default_openapi_route', 5, 9, 8).
python_function('adapters/python/urirun/_registry.py', 'discover_openapi', 5, 10, 9).
python_function('adapters/python/urirun/_registry.py', 'uri_handler', 1, 1, 2).
python_function('adapters/python/urirun/_registry.py', '_iter_module_exports', 1, 6, 6).
python_function('adapters/python/urirun/_registry.py', 'discover_python_modules', 1, 5, 6).
python_function('adapters/python/urirun/_registry.py', 'discover_entry_points', 1, 6, 9).
python_function('adapters/python/urirun/_registry.py', 'registry_tree', 1, 2, 2).
python_function('adapters/python/urirun/_registry.py', 'resolve_route', 2, 8, 6).
python_function('adapters/python/urirun/_registry.py', '_walk_route_entries', 1, 5, 3).
python_function('adapters/python/urirun/_registry.py', 'hydrate_registry', 2, 4, 5).
python_function('adapters/python/urirun/_registry.py', 'exec_local_function', 1, 2, 3).
python_function('adapters/python/urirun/_registry.py', 'exec_fetch', 1, 1, 1).
python_function('adapters/python/urirun/_registry.py', 'exec_spawn', 1, 2, 1).
python_function('adapters/python/urirun/_registry.py', 'exec_shell_template', 1, 2, 3).
python_function('adapters/python/urirun/_registry.py', 'exec_mqtt_publish', 1, 3, 2).
python_function('adapters/python/urirun/_registry.py', 'dispatch_generated', 5, 7, 7).
python_function('adapters/python/urirun/_registry.py', 'load_json', 1, 1, 3).
python_function('adapters/python/urirun/_registry.py', 'write_json', 2, 1, 5).
python_function('adapters/python/urirun/_registry.py', '_emit_json', 2, 3, 3).
python_function('adapters/python/urirun/_registry.py', '_load_sources', 1, 2, 3).
python_function('adapters/python/urirun/_registry.py', '_discover_python_module', 1, 1, 2).
python_function('adapters/python/urirun/_registry.py', 'main', 1, 9, 17).
python_function('adapters/python/urirun/_runtime.py', 'default_policy', 0, 1, 0).
python_function('adapters/python/urirun/_runtime.py', 'merge_policy', 1, 7, 5).
python_function('adapters/python/urirun/_runtime.py', '_matches_any', 2, 3, 1).
python_function('adapters/python/urirun/_runtime.py', '_looks_destructive', 2, 5, 6).
python_function('adapters/python/urirun/_runtime.py', 'evaluate_policy', 4, 16, 4).
python_function('adapters/python/urirun/_runtime.py', '_truncate', 1, 3, 1).
python_function('adapters/python/urirun/_runtime.py', 'run_spawn', 2, 5, 5).
python_function('adapters/python/urirun/_runtime.py', 'run_shell_template', 2, 3, 7).
python_function('adapters/python/urirun/_runtime.py', 'run_fetch', 2, 7, 16).
python_function('adapters/python/urirun/_runtime.py', 'run_local_function', 2, 2, 6).
python_function('adapters/python/urirun/_runtime.py', 'run_mqtt_publish', 2, 3, 2).
python_function('adapters/python/urirun/_runtime.py', 'run', 7, 10, 11).
python_function('adapters/python/urirun/_runtime.py', 'check', 3, 1, 6).
python_function('adapters/python/urirun/_runtime.py', 'load_registry_arg', 2, 4, 8).
python_function('adapters/python/urirun/_runtime.py', 'build_policy', 3, 10, 4).
python_function('adapters/python/urirun/_runtime.py', 'list_routes', 2, 4, 8).
python_function('adapters/python/urirun/_runtime.py', 'format_route_table', 2, 13, 8).
python_function('adapters/python/urirun/_runtime.py', 'main', 1, 10, 18).
python_function('adapters/python/urirun/_scan.py', 'slugify', 2, 2, 4).
python_function('adapters/python/urirun/_scan.py', 'relpath', 2, 2, 3).
python_function('adapters/python/urirun/_scan.py', 'now_iso', 0, 1, 2).
python_function('adapters/python/urirun/_scan.py', 'load_json', 1, 1, 3).
python_function('adapters/python/urirun/_scan.py', 'write_json', 2, 1, 5).
python_function('adapters/python/urirun/_scan.py', 'emit_json', 2, 3, 3).
python_function('adapters/python/urirun/_scan.py', 'infer_kind', 1, 12, 1).
python_function('adapters/python/urirun/_scan.py', 'normalize_binding', 2, 11, 7).
python_function('adapters/python/urirun/_scan.py', 'binding_to_route_source', 1, 3, 2).
python_function('adapters/python/urirun/_scan.py', 'route_source_to_binding', 1, 5, 2).
python_function('adapters/python/urirun/_scan.py', 'load_bindings_from_manifest', 2, 14, 7).
python_function('adapters/python/urirun/_scan.py', 'build_binding_document', 2, 3, 6).
python_function('adapters/python/urirun/_scan.py', 'compile_registry_document', 3, 4, 5).
python_function('adapters/python/urirun/_scan.py', 'iter_project_files', 1, 5, 4).
python_function('adapters/python/urirun/_scan.py', 'scan_manifest_files', 1, 4, 6).
python_function('adapters/python/urirun/_scan.py', 'npm_command_for_script', 1, 2, 0).
python_function('adapters/python/urirun/_scan.py', 'github_dependency_binding', 5, 4, 3).
python_function('adapters/python/urirun/_scan.py', 'scan_package_json', 2, 7, 11).
python_function('adapters/python/urirun/_scan.py', '_read_toml', 1, 12, 10).
python_function('adapters/python/urirun/_scan.py', 'scan_pyproject', 2, 9, 12).
python_function('adapters/python/urirun/_scan.py', 'scan_makefile', 2, 5, 10).
python_function('adapters/python/urirun/_scan.py', 'scan_shell_script', 2, 1, 3).
python_function('adapters/python/urirun/_scan.py', 'module_ref_for_python', 3, 3, 3).
python_function('adapters/python/urirun/_scan.py', 'scan_python_code', 2, 3, 8).
python_function('adapters/python/urirun/_scan.py', 'scan_js_code', 2, 4, 7).
python_function('adapters/python/urirun/_scan.py', 'parse_compose_label_line', 1, 4, 4).
python_function('adapters/python/urirun/_scan.py', 'scan_docker_compose', 2, 10, 12).
python_function('adapters/python/urirun/_scan.py', 'scan_openapi', 3, 4, 5).
python_function('adapters/python/urirun/_scan.py', 'scan_path', 3, 15, 18).
python_function('adapters/python/urirun/_scan.py', 'scan_github', 3, 2, 6).
python_function('adapters/python/urirun/_scan.py', 'load_binding_source', 3, 5, 10).
python_function('adapters/python/urirun/_scan.py', 'load_binding_sources', 3, 2, 2).
python_function('adapters/python/urirun/_scan.py', 'load_registry_arg', 5, 4, 8).
python_function('adapters/python/urirun/_scan.py', 'list_bindings', 3, 2, 3).
python_function('adapters/python/urirun/_scan.py', 'format_binding_table', 1, 11, 8).
python_function('adapters/python/urirun/_scan.py', 'main', 1, 10, 19).
python_function('adapters/python/urirun/domain_monitor.py', 'now_id', 0, 1, 2).
python_function('adapters/python/urirun/domain_monitor.py', '_list', 1, 6, 5).
python_function('adapters/python/urirun/domain_monitor.py', '_domain', 2, 2, 2).
python_function('adapters/python/urirun/domain_monitor.py', 'default_url', 1, 2, 1).
python_function('adapters/python/urirun/domain_monitor.py', 'http_status', 3, 5, 7).
python_function('adapters/python/urirun/domain_monitor.py', 'dns_records', 2, 11, 7).
python_function('adapters/python/urirun/domain_monitor.py', 'expected_records', 1, 8, 6).
python_function('adapters/python/urirun/domain_monitor.py', 'dns_mismatches', 2, 4, 4).
python_function('adapters/python/urirun/domain_monitor.py', 'capture_screenshot_artifact', 0, 3, 8).
python_function('adapters/python/urirun/domain_monitor.py', 'create_dns_repair_ticket', 0, 2, 3).
python_function('adapters/python/urirun/domain_monitor.py', 'check_domain', 0, 16, 13).
python_function('adapters/python/urirun/domain_monitor.py', 'run_daily', 0, 7, 9).
python_function('adapters/python/urirun/domain_monitor.py', '_db', 2, 3, 1).
python_function('adapters/python/urirun/domain_monitor.py', '_project', 2, 3, 1).
python_function('adapters/python/urirun/domain_monitor.py', '_screenshot_dir', 2, 3, 1).
python_function('adapters/python/urirun/domain_monitor.py', '_provider', 2, 4, 3).
python_function('adapters/python/urirun/domain_monitor.py', 'run_uri_route', 2, 46, 22).
python_function('adapters/python/urirun/host_dashboard.py', '_json_response', 3, 1, 8).
python_function('adapters/python/urirun/host_dashboard.py', '_html_response', 2, 1, 7).
python_function('adapters/python/urirun/host_dashboard.py', '_read_json', 1, 3, 5).
python_function('adapters/python/urirun/host_dashboard.py', '_first', 3, 2, 1).
python_function('adapters/python/urirun/host_dashboard.py', '_safe_tickets', 4, 2, 2).
python_function('adapters/python/urirun/host_dashboard.py', '_task_counts', 1, 3, 2).
python_function('adapters/python/urirun/host_dashboard.py', 'summary', 3, 6, 15).
python_function('adapters/python/urirun/host_dashboard.py', 'task_action', 4, 8, 8).
python_function('adapters/python/urirun/host_dashboard.py', 'create_handler', 3, 1, 19).
python_function('adapters/python/urirun/host_dashboard.py', 'serve', 5, 1, 7).
python_function('adapters/python/urirun/host_dashboard.py', 'command', 1, 8, 4).
python_function('adapters/python/urirun/host_dashboard.py', 'default_host', 0, 1, 2).
python_function('adapters/python/urirun/host_db.py', 'db_path', 1, 2, 3).
python_function('adapters/python/urirun/host_db.py', 'now_iso', 0, 1, 2).
python_function('adapters/python/urirun/host_db.py', 'new_id', 1, 1, 1).
python_function('adapters/python/urirun/host_db.py', 'connect', 1, 1, 5).
python_function('adapters/python/urirun/host_db.py', 'connection', 1, 1, 3).
python_function('adapters/python/urirun/host_db.py', 'row_dict', 1, 7, 5).
python_function('adapters/python/urirun/host_db.py', 'rows_dict', 1, 2, 1).
python_function('adapters/python/urirun/host_db.py', 'init_db', 1, 2, 5).
python_function('adapters/python/urirun/host_db.py', '_schema_json', 1, 2, 2).
python_function('adapters/python/urirun/host_db.py', 'create_dataset', 4, 1, 7).
python_function('adapters/python/urirun/host_db.py', 'list_datasets', 1, 1, 5).
python_function('adapters/python/urirun/host_db.py', 'get_dataset', 2, 2, 6).
python_function('adapters/python/urirun/host_db.py', '_validate_record', 2, 2, 3).
python_function('adapters/python/urirun/host_db.py', 'upsert_record', 4, 1, 11).
python_function('adapters/python/urirun/host_db.py', '_sync_record_fts', 3, 3, 3).
python_function('adapters/python/urirun/host_db.py', 'search_records', 4, 6, 10).
python_function('adapters/python/urirun/host_db.py', 'register_artifact', 5, 2, 8).
python_function('adapters/python/urirun/host_db.py', 'list_artifacts', 3, 2, 6).
python_function('adapters/python/urirun/host_db.py', 'add_check', 5, 2, 8).
python_function('adapters/python/urirun/host_db.py', 'recent_checks', 3, 2, 6).
python_function('adapters/python/urirun/host_db.py', 'add_log', 4, 2, 8).
python_function('adapters/python/urirun/host_db.py', 'recent_logs', 3, 2, 6).
python_function('adapters/python/urirun/host_db.py', 'create_llm_session', 2, 1, 7).
python_function('adapters/python/urirun/host_db.py', 'add_llm_message', 5, 2, 8).
python_function('adapters/python/urirun/host_db.py', 'read_only_sql', 4, 5, 11).
python_function('adapters/python/urirun/host_db.py', 'route_db_path', 2, 3, 1).
python_function('adapters/python/urirun/host_db.py', 'run_uri_route', 2, 45, 18).
python_function('adapters/python/urirun/mesh.py', 'now_id', 0, 1, 3).
python_function('adapters/python/urirun/mesh.py', 'slug', 1, 2, 3).
python_function('adapters/python/urirun/mesh.py', 'json_load', 1, 1, 3).
python_function('adapters/python/urirun/mesh.py', 'json_write', 2, 1, 4).
python_function('adapters/python/urirun/mesh.py', 'host_config_path', 1, 2, 2).
python_function('adapters/python/urirun/mesh.py', 'node_config_path', 1, 2, 2).
python_function('adapters/python/urirun/mesh.py', 'default_host_config', 1, 3, 2).
python_function('adapters/python/urirun/mesh.py', 'load_host_config', 1, 2, 6).
python_function('adapters/python/urirun/mesh.py', 'save_host_config', 2, 1, 2).
python_function('adapters/python/urirun/mesh.py', 'init_host', 2, 1, 2).
python_function('adapters/python/urirun/mesh.py', 'add_node', 4, 4, 6).
python_function('adapters/python/urirun/mesh.py', 'default_node_config', 2, 2, 1).
python_function('adapters/python/urirun/mesh.py', 'load_node_config', 1, 2, 5).
python_function('adapters/python/urirun/mesh.py', 'save_node_config', 2, 1, 2).
python_function('adapters/python/urirun/mesh.py', 'init_node', 6, 1, 3).
python_function('adapters/python/urirun/mesh.py', 'http_json', 4, 6, 8).
python_function('adapters/python/urirun/mesh.py', 'routes_from_registry', 1, 9, 5).
python_function('adapters/python/urirun/mesh.py', 'safe_route', 1, 4, 4).
python_function('adapters/python/urirun/mesh.py', 'route_target', 1, 1, 1).
python_function('adapters/python/urirun/mesh.py', 'discover_node', 1, 2, 5).
python_function('adapters/python/urirun/mesh.py', 'discover_mesh', 1, 7, 6).
python_function('adapters/python/urirun/mesh.py', 'binding_for_remote_route', 1, 3, 1).
python_function('adapters/python/urirun/mesh.py', 'registry_from_routes', 1, 3, 3).
python_function('adapters/python/urirun/mesh.py', 'target_nodes', 3, 10, 2).
python_function('adapters/python/urirun/mesh.py', 'first_url', 1, 2, 2).
python_function('adapters/python/urirun/mesh.py', 'append_if_available', 5, 5, 5).
python_function('adapters/python/urirun/mesh.py', 'heuristic_flow', 4, 19, 7).
python_function('adapters/python/urirun/mesh.py', 'json_from_text', 1, 5, 7).
python_function('adapters/python/urirun/mesh.py', 'normalize_flow', 2, 15, 9).
python_function('adapters/python/urirun/mesh.py', 'llm_flow', 3, 7, 7).
python_function('adapters/python/urirun/mesh.py', 'make_flow', 4, 6, 5).
python_function('adapters/python/urirun/mesh.py', 'execute_flow', 4, 9, 8).
python_function('adapters/python/urirun/mesh.py', 'format_nodes', 1, 8, 5).
python_function('adapters/python/urirun/mesh.py', 'format_routes', 1, 6, 4).
python_function('adapters/python/urirun/mesh.py', 'format_tickets', 1, 6, 2).
python_function('adapters/python/urirun/mesh.py', 'format_table', 3, 6, 9).
python_function('adapters/python/urirun/mesh.py', '_parse_json_option', 2, 2, 1).
python_function('adapters/python/urirun/mesh.py', 'data_command', 1, 15, 15).
python_function('adapters/python/urirun/mesh.py', 'monitor_command', 1, 14, 10).
python_function('adapters/python/urirun/mesh.py', '_task_prompt', 1, 7, 2).
python_function('adapters/python/urirun/mesh.py', '_ticket_payload', 1, 7, 4).
python_function('adapters/python/urirun/mesh.py', '_host_local_registry', 1, 4, 7).
python_function('adapters/python/urirun/mesh.py', '_run_executor_handler', 3, 2, 6).
python_function('adapters/python/urirun/mesh.py', '_resolves_locally', 2, 5, 3).
python_function('adapters/python/urirun/mesh.py', '_run_task_flow', 2, 11, 16).
python_function('adapters/python/urirun/mesh.py', 'task_command', 1, 52, 34).
python_function('adapters/python/urirun/mesh.py', 'host_command', 1, 19, 17).
python_function('adapters/python/urirun/mesh.py', 'send_json', 3, 1, 8).
python_function('adapters/python/urirun/mesh.py', 'read_json', 1, 3, 5).
python_function('adapters/python/urirun/mesh.py', 'serve_node', 6, 2, 13).
python_function('adapters/python/urirun/mesh.py', 'node_command', 1, 16, 14).
python_function('adapters/python/urirun/namecheap_dns.py', 'split_domain', 1, 2, 2).
python_function('adapters/python/urirun/namecheap_dns.py', 'env_name', 2, 2, 1).
python_function('adapters/python/urirun/namecheap_dns.py', 'config_from_env', 2, 12, 5).
python_function('adapters/python/urirun/namecheap_dns.py', 'auth_params', 3, 1, 1).
python_function('adapters/python/urirun/namecheap_dns.py', 'request_api', 5, 3, 8).
python_function('adapters/python/urirun/namecheap_dns.py', '_strip_ns', 1, 2, 1).
python_function('adapters/python/urirun/namecheap_dns.py', 'parse_api_xml', 1, 7, 8).
python_function('adapters/python/urirun/namecheap_dns.py', 'normalize_record', 1, 13, 5).
python_function('adapters/python/urirun/namecheap_dns.py', 'normalize_records', 1, 3, 2).
python_function('adapters/python/urirun/namecheap_dns.py', 'record_key', 1, 1, 1).
python_function('adapters/python/urirun/namecheap_dns.py', 'record_identity', 1, 1, 1).
python_function('adapters/python/urirun/namecheap_dns.py', 'merge_records', 3, 4, 5).
python_function('adapters/python/urirun/namecheap_dns.py', 'diff_records', 2, 6, 5).
python_function('adapters/python/urirun/namecheap_dns.py', 'desired_from_payload', 2, 2, 3).
python_function('adapters/python/urirun/namecheap_dns.py', 'current_records', 2, 4, 6).
python_function('adapters/python/urirun/namecheap_dns.py', 'plan', 2, 1, 4).
python_function('adapters/python/urirun/namecheap_dns.py', 'sethosts_params', 1, 6, 4).
python_function('adapters/python/urirun/namecheap_dns.py', 'backup', 4, 2, 9).
python_function('adapters/python/urirun/namecheap_dns.py', 'apply', 2, 15, 9).
python_function('adapters/python/urirun/namecheap_dns.py', 'run_uri_route', 2, 16, 9).
python_function('adapters/python/urirun/planfile_adapter.py', '_imports', 0, 2, 1).
python_function('adapters/python/urirun/planfile_adapter.py', 'normalize_priority', 1, 2, 2).
python_function('adapters/python/urirun/planfile_adapter.py', 'project_root', 1, 2, 4).
python_function('adapters/python/urirun/planfile_adapter.py', '_model_dict', 1, 1, 1).
python_function('adapters/python/urirun/planfile_adapter.py', 'load_planfile', 1, 1, 2).
python_function('adapters/python/urirun/planfile_adapter.py', 'ticket_to_dict', 1, 2, 1).
python_function('adapters/python/urirun/planfile_adapter.py', 'build_ticket_payload', 1, 35, 13).
python_function('adapters/python/urirun/planfile_adapter.py', 'create_ticket', 2, 3, 6).
python_function('adapters/python/urirun/planfile_adapter.py', 'list_tickets', 5, 9, 4).
python_function('adapters/python/urirun/planfile_adapter.py', 'next_ticket', 3, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'get_ticket', 2, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'claim_ticket', 4, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'start_ticket', 3, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'complete_ticket', 5, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'fail_ticket', 3, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'fail_or_retry', 3, 4, 7).
python_function('adapters/python/urirun/planfile_adapter.py', 'update_ticket', 3, 3, 5).
python_function('adapters/python/urirun/planfile_adapter.py', 'wait_for_input', 5, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'ready_ticket', 3, 2, 3).
python_function('adapters/python/urirun/planfile_adapter.py', 'run_dsl', 2, 1, 4).
python_function('adapters/python/urirun/planfile_adapter.py', 'loads_json', 2, 2, 1).
python_function('adapters/python/urirun/scheduler.py', 'build_loop_command', 0, 4, 3).
python_function('adapters/python/urirun/scheduler.py', 'shell_join', 1, 2, 2).
python_function('adapters/python/urirun/scheduler.py', 'systemd_units', 0, 2, 1).
python_function('adapters/python/urirun/scheduler.py', 'cron_line', 2, 1, 3).
python_function('adapters/python/urirun/scheduler.py', 'preview', 0, 3, 5).
python_function('adapters/python/urirun/scheduler.py', 'install_systemd_user', 2, 3, 7).
python_function('adapters/python/urirun/task_planner.py', 'normalize_text', 1, 3, 6).
python_function('adapters/python/urirun/task_planner.py', 'slug', 1, 2, 3).
python_function('adapters/python/urirun/task_planner.py', '_json_from_text', 1, 5, 7).
python_function('adapters/python/urirun/task_planner.py', 'is_ambiguous', 1, 2, 3).
python_function('adapters/python/urirun/task_planner.py', 'is_destructive', 1, 4, 4).
python_function('adapters/python/urirun/task_planner.py', '_has_any', 2, 2, 2).
python_function('adapters/python/urirun/task_planner.py', '_unique', 1, 4, 1).
python_function('adapters/python/urirun/task_planner.py', '_short_name', 3, 6, 6).
python_function('adapters/python/urirun/task_planner.py', 'heuristic_plan_chat_request', 1, 22, 14).
python_function('adapters/python/urirun/task_planner.py', 'llm_plan_chat_request', 1, 4, 8).
python_function('adapters/python/urirun/task_planner.py', 'plan_chat_request', 1, 3, 3).
python_function('adapters/python/urirun/task_planner.py', 'ticket_payload', 2, 3, 2).
python_function('adapters/python/urirun/task_planner.py', 'create_tickets_from_plan', 2, 4, 4).
python_function('adapters/python/urirun/v1.py', '_params_spec', 1, 4, 1).
python_function('adapters/python/urirun/v1.py', 'resolve_params', 4, 11, 11).
python_function('adapters/python/urirun/v1.py', 'render_value', 2, 1, 4).
python_function('adapters/python/urirun/v1.py', 'render_command', 2, 2, 1).
python_function('adapters/python/urirun/v1.py', '_has_placeholders', 1, 2, 3).
python_function('adapters/python/urirun/v1.py', '_proc_env', 2, 3, 6).
python_function('adapters/python/urirun/v1.py', '_run_process', 5, 1, 4).
python_function('adapters/python/urirun/v1.py', '_env_flags', 2, 3, 5).
python_function('adapters/python/urirun/v1.py', 'run_spawn', 3, 6, 6).
python_function('adapters/python/urirun/v1.py', 'run_shell_template', 3, 3, 5).
python_function('adapters/python/urirun/v1.py', 'run_docker_exec', 3, 4, 5).
python_function('adapters/python/urirun/v1.py', 'run_docker_run', 3, 5, 9).
python_function('adapters/python/urirun/v1.py', 'run_fetch', 3, 3, 6).
python_function('adapters/python/urirun/v1.py', 'run_local_function', 3, 2, 2).
python_function('adapters/python/urirun/v1.py', 'run_mqtt_publish', 3, 1, 1).
python_function('adapters/python/urirun/v1.py', 'run', 7, 14, 11).
python_function('adapters/python/urirun/v1.py', 'check', 3, 1, 1).
python_function('adapters/python/urirun/v1.py', 'list_routes', 2, 1, 1).
python_function('adapters/python/urirun/v1.py', 'expand_binding', 2, 7, 5).
python_function('adapters/python/urirun/v1.py', '_binding_pairs', 1, 8, 5).
python_function('adapters/python/urirun/v1.py', 'expand_bindings', 1, 2, 2).
python_function('adapters/python/urirun/v1.py', 'compile_registry', 3, 1, 2).
python_function('adapters/python/urirun/v1.py', 'load_registry_arg', 2, 4, 9).
python_function('adapters/python/urirun/v1.py', 'main', 1, 13, 23).
python_function('adapters/python/urirun/v2.py', 'model_from_function', 1, 4, 4).
python_function('adapters/python/urirun/v2.py', '_placeholder_kwargs', 1, 2, 1).
python_function('adapters/python/urirun/v2.py', 'uri_command', 1, 1, 6).
python_function('adapters/python/urirun/v2.py', 'uri_shell', 1, 1, 1).
python_function('adapters/python/urirun/v2.py', 'decorated_bindings', 0, 2, 1).
python_function('adapters/python/urirun/v2.py', '_document_binding_from_expanded', 1, 4, 5).
python_function('adapters/python/urirun/v2.py', 'connector_bindings', 1, 11, 8).
python_function('adapters/python/urirun/v2.py', '_schema_for', 1, 3, 1).
python_function('adapters/python/urirun/v2.py', '_apply_defaults', 2, 14, 5).
python_function('adapters/python/urirun/v2.py', '_input_values', 3, 4, 7).
python_function('adapters/python/urirun/v2.py', 'validate_input', 4, 6, 13).
python_function('adapters/python/urirun/v2.py', 'render_value', 2, 1, 4).
python_function('adapters/python/urirun/v2.py', 'render_sequence', 2, 2, 1).
python_function('adapters/python/urirun/v2.py', 'render_argv', 2, 7, 9).
python_function('adapters/python/urirun/v2.py', 'run_argv_template', 3, 5, 4).
python_function('adapters/python/urirun/v2.py', 'run_shell_template', 3, 4, 3).
python_function('adapters/python/urirun/v2.py', 'planfile_task_bindings', 2, 3, 1).
python_function('adapters/python/urirun/v2.py', '_list_param', 1, 6, 4).
python_function('adapters/python/urirun/v2.py', '_ticket_id', 2, 5, 4).
python_function('adapters/python/urirun/v2.py', '_planfile_action', 1, 7, 1).
python_function('adapters/python/urirun/v2.py', '_planfile_project', 2, 4, 2).
python_function('adapters/python/urirun/v2.py', '_simulate_planfile', 4, 1, 3).
python_function('adapters/python/urirun/v2.py', 'run_planfile_task', 3, 31, 25).
python_function('adapters/python/urirun/v2.py', 'host_data_bindings', 2, 3, 1).
python_function('adapters/python/urirun/v2.py', 'run_host_data', 3, 1, 1).
python_function('adapters/python/urirun/v2.py', 'domain_monitor_bindings', 4, 5, 1).
python_function('adapters/python/urirun/v2.py', 'run_domain_monitor', 3, 3, 4).
python_function('adapters/python/urirun/v2.py', 'run', 7, 15, 11).
python_function('adapters/python/urirun/v2.py', 'check', 3, 1, 1).
python_function('adapters/python/urirun/v2.py', 'list_routes', 2, 1, 1).
python_function('adapters/python/urirun/v2.py', '_strip_runtime_only', 1, 3, 1).
python_function('adapters/python/urirun/v2.py', 'expand_binding', 2, 16, 6).
python_function('adapters/python/urirun/v2.py', '_binding_pairs', 1, 8, 5).
python_function('adapters/python/urirun/v2.py', 'expand_bindings', 1, 2, 2).
python_function('adapters/python/urirun/v2.py', 'compile_registry', 3, 1, 2).
python_function('adapters/python/urirun/v2.py', 'build_binding_document', 2, 3, 5).
python_function('adapters/python/urirun/v2.py', '_bindings_as_map', 1, 2, 2).
python_function('adapters/python/urirun/v2.py', 'merge_binding_document', 2, 2, 3).
python_function('adapters/python/urirun/v2.py', 'write_or_emit_binding', 2, 3, 7).
python_function('adapters/python/urirun/v2.py', '_coerce_default', 2, 4, 3).
python_function('adapters/python/urirun/v2.py', 'parse_param_declaration', 1, 8, 7).
python_function('adapters/python/urirun/v2.py', 'input_schema_from_params', 1, 4, 2).
python_function('adapters/python/urirun/v2.py', 'command_binding_from_cli', 1, 5, 5).
python_function('adapters/python/urirun/v2.py', 'pypi_binding', 3, 3, 1).
python_function('adapters/python/urirun/v2.py', 'load_registry_arg', 2, 4, 8).
python_function('adapters/python/urirun/v2.py', '_placeholders_in', 1, 6, 6).
python_function('adapters/python/urirun/v2.py', 'validate_binding_document', 1, 12, 15).
python_function('adapters/python/urirun/v2.py', '_iter_files', 1, 5, 4).
python_function('adapters/python/urirun/v2.py', '_rel', 2, 2, 3).
python_function('adapters/python/urirun/v2.py', '_empty_input_schema', 0, 1, 0).
python_function('adapters/python/urirun/v2.py', '_load_manifest', 1, 1, 2).
python_function('adapters/python/urirun/v2.py', '_scan_package_json', 2, 4, 9).
python_function('adapters/python/urirun/v2.py', '_read_toml', 1, 2, 3).
python_function('adapters/python/urirun/v2.py', '_scan_pyproject', 2, 4, 9).
python_function('adapters/python/urirun/v2.py', '_scan_shell_script', 2, 1, 4).
python_function('adapters/python/urirun/v2.py', '_scan_makefile', 2, 5, 11).
python_function('adapters/python/urirun/v2.py', '_parse_dockerfile_labels', 1, 4, 7).
python_function('adapters/python/urirun/v2.py', '_manifest_candidates', 2, 2, 3).
python_function('adapters/python/urirun/v2.py', '_scan_dockerfile', 2, 7, 12).
python_function('adapters/python/urirun/v2.py', 'scan_artifacts', 1, 11, 15).
python_function('adapters/python/urirun/v2.py', '_load_many', 1, 3, 6).
python_function('adapters/python/urirun/v2.py', 'main', 1, 23, 33).
python_function('adapters/python/urirun/v2_adopt.py', 'passthrough_schema', 1, 2, 1).
python_function('adapters/python/urirun/v2_adopt.py', '_command_binding', 5, 2, 2).
python_function('adapters/python/urirun/v2_adopt.py', 'python_package_bindings', 1, 4, 5).
python_function('adapters/python/urirun/v2_adopt.py', 'installed_python_bindings', 0, 4, 3).
python_function('adapters/python/urirun/v2_adopt.py', 'npm_package_bindings', 2, 4, 9).
python_function('adapters/python/urirun/v2_adopt.py', 'init_project', 1, 1, 2).
python_function('adapters/python/urirun/v2_adopt.py', 'merge_into', 2, 7, 9).
python_function('adapters/python/urirun/v2_adopt.py', 'main', 1, 7, 14).
python_function('adapters/python/urirun/v2_grpc.py', '_dumps', 1, 1, 2).
python_function('adapters/python/urirun/v2_grpc.py', '_loads', 1, 2, 2).
python_function('adapters/python/urirun/v2_grpc.py', '_route_list', 1, 2, 4).
python_function('adapters/python/urirun/v2_grpc.py', 'serve', 7, 2, 12).
python_function('adapters/python/urirun/v2_grpc.py', 'channel_target', 1, 3, 3).
python_function('adapters/python/urirun/v2_grpc.py', '_method', 3, 2, 1).
python_function('adapters/python/urirun/v2_grpc.py', '_validate', 3, 5, 4).
python_function('adapters/python/urirun/v2_grpc.py', 'call', 7, 6, 7).
python_function('adapters/python/urirun/v2_grpc.py', 'stream', 5, 4, 7).
python_function('adapters/python/urirun/v2_grpc.py', 'list_routes', 2, 1, 3).
python_function('adapters/python/urirun/v2_grpc.py', 'main', 1, 9, 15).
python_function('adapters/python/urirun/v2_mcp.py', 'tool_name', 1, 1, 4).
python_function('adapters/python/urirun/v2_mcp.py', '_input_schema', 1, 4, 1).
python_function('adapters/python/urirun/v2_mcp.py', 'to_mcp_tools', 1, 4, 5).
python_function('adapters/python/urirun/v2_mcp.py', 'to_mcp_manifest', 1, 4, 2).
python_function('adapters/python/urirun/v2_mcp.py', 'to_a2a_card', 4, 4, 6).
python_function('adapters/python/urirun/v2_mcp.py', 'build_tool_index', 1, 2, 1).
python_function('adapters/python/urirun/v2_mcp.py', 'call_tool', 6, 3, 4).
python_function('adapters/python/urirun/v2_mcp.py', 'serve_mcp', 5, 15, 11).
python_function('adapters/python/urirun/v2_mcp.py', 'main', 1, 9, 11).
python_function('adapters/python/urirun/v2_service.py', 'service_base', 1, 3, 4).
python_function('adapters/python/urirun/v2_service.py', '_post', 3, 3, 7).
python_function('adapters/python/urirun/v2_service.py', 'call', 6, 9, 9).

% ── Python Classes ───────────────────────────────────────
python_class('adapters/python/tests/test_domain_monitor.py', '_StatusHandler').
python_method('_StatusHandler', 'do_GET', 0, 1, 4).
python_method('_StatusHandler', 'log_message', 1, 1, 0).
python_class('adapters/python/tests/test_domain_monitor.py', 'DomainMonitorTests').
python_method('DomainMonitorTests', 'test_http_200_writes_success_check', 0, 1, 9).
python_method('DomainMonitorTests', 'test_http_failure_creates_screenshot_artifact', 0, 1, 9).
python_method('DomainMonitorTests', 'test_dns_mismatch_creates_review_ticket_only', 0, 1, 11).
python_method('DomainMonitorTests', 'test_v2_domain_monitor_bindings', 0, 1, 10).
python_method('DomainMonitorTests', 'test_v2_domain_monitor_mismatch_sets_failed_envelope_and_review_ticket', 0, 1, 12).
python_method('DomainMonitorTests', 'test_cli_monitor_domain_dry_run', 0, 1, 12).
python_class('adapters/python/tests/test_host_dashboard.py', 'HostDashboardTests').
python_method('HostDashboardTests', 'test_dashboard_html_summary_and_task_action', 0, 1, 22).
python_method('HostDashboardTests', 'test_v2_dashboard_url_command', 0, 1, 7).
python_class('adapters/python/tests/test_host_db.py', 'HostDbTests').
python_method('HostDbTests', 'test_dataset_schema_and_record_search', 0, 1, 8).
python_method('HostDbTests', 'test_v2_data_uri_bindings', 0, 1, 9).
python_method('HostDbTests', 'test_artifact_and_check_storage', 0, 1, 7).
python_class('adapters/python/tests/test_mesh.py', 'MeshTests').
python_method('MeshTests', 'test_host_config_add_node', 0, 1, 7).
python_method('MeshTests', 'test_node_config_defaults', 0, 1, 6).
python_method('MeshTests', 'test_heuristic_flow_uses_all_reachable_nodes', 0, 2, 2).
python_method('MeshTests', 'test_registry_from_remote_routes', 0, 1, 3).
python_class('adapters/python/tests/test_namecheap_dns.py', 'NamecheapDnsTests').
python_method('NamecheapDnsTests', 'test_parse_get_hosts_xml', 0, 1, 3).
python_method('NamecheapDnsTests', 'test_plan_merges_ensure_and_remove_records', 0, 1, 3).
python_method('NamecheapDnsTests', 'test_backup_writes_artifact_and_registers_it', 0, 1, 8).
python_method('NamecheapDnsTests', 'test_apply_requires_backup_uri', 0, 1, 2).
python_method('NamecheapDnsTests', 'test_apply_mock_refuses_current_drift_from_reviewed_plan', 0, 1, 3).
python_method('NamecheapDnsTests', 'test_v2_dns_namecheap_uri_plan_backup_apply_mock', 0, 1, 8).
python_class('adapters/python/tests/test_planfile_adapter.py', 'PlanfileAdapterTests').
python_method('PlanfileAdapterTests', 'test_create_next_and_complete_ticket', 0, 1, 7).
python_method('PlanfileAdapterTests', 'test_dsl_create_ticket', 0, 1, 6).
python_method('PlanfileAdapterTests', 'test_cli_host_task_create_and_list', 0, 1, 7).
python_method('PlanfileAdapterTests', 'test_host_task_run_updates_ticket', 0, 1, 12).
python_method('PlanfileAdapterTests', 'test_v2_task_uri_bindings_create_and_list_ticket', 0, 1, 7).
python_method('PlanfileAdapterTests', 'test_v2_task_uri_complete_and_fail_record_outputs', 0, 1, 9).
python_method('PlanfileAdapterTests', 'test_v2_task_uri_rejects_invalid_payload', 0, 1, 7).
python_method('PlanfileAdapterTests', 'test_host_task_run_dispatches_executor_handler', 0, 1, 14).
python_method('PlanfileAdapterTests', 'test_fail_or_retry_requeues_until_max_attempts', 0, 1, 9).
python_method('PlanfileAdapterTests', 'test_fail_or_retry_default_max_attempts_fails_terminally', 0, 1, 6).
python_method('PlanfileAdapterTests', 'test_host_task_loop_retries_failing_flow_until_exhausted', 0, 1, 11).
python_method('PlanfileAdapterTests', 'test_chat_plan_domain_prompt_creates_ticket', 0, 1, 10).
python_method('PlanfileAdapterTests', 'test_chat_plan_ambiguous_prompt_waits_for_input', 0, 1, 6).
python_method('PlanfileAdapterTests', 'test_chat_plan_destructive_prompt_requires_review', 0, 1, 6).
python_class('adapters/python/tests/test_scheduler.py', 'SchedulerTests').
python_method('SchedulerTests', 'test_systemd_preview_and_install', 0, 1, 9).
python_method('SchedulerTests', 'test_cli_schedule_cron_preview', 0, 1, 9).
python_class('adapters/python/tests/test_urihandler.py', 'UriHandlerTests').
python_method('UriHandlerTests', 'test_parse_uri', 0, 1, 2).
python_method('UriHandlerTests', 'test_build_invocation', 0, 1, 2).
python_method('UriHandlerTests', 'test_dispatch', 0, 1, 2).
python_method('UriHandlerTests', 'test_missing_registry_entries', 0, 1, 2).
python_method('UriHandlerTests', 'test_v2_connector_bindings_from_decorators', 0, 2, 10).
python_class('adapters/python/urirun/_runtime.py', 'PolicyError').
python_class('adapters/python/urirun/planfile_adapter.py', 'PlanfileUnavailable').
python_class('adapters/python/urirun/task_planner.py', 'PlannedTicket').
python_class('adapters/python/urirun/task_planner.py', 'TaskPlanningResult').

% ── Dependencies ─────────────────────────────────────────

% ── Makefile Targets ─────────────────────────────────────
makefile_target('help', '').
makefile_target('test', '').
makefile_target('test-js', '').
makefile_target('test-python', '').
makefile_target('test-c', '').
makefile_target('test-v1', '').
makefile_target('test-v2', '').
makefile_target('clean', '').

% ── Taskfile Tasks ───────────────────────────────────────

% ── Environment Variables ────────────────────────────────
env_variable('OPENROUTER_API_KEY', '*(not set)*', 'Required: OpenRouter API key (https://openrouter.ai/keys)').
env_variable('LLM_MODEL', 'openrouter/qwen/qwen3-coder-next', 'Model (default: openrouter/qwen/qwen3-coder-next)').
env_variable('PFIX_AUTO_APPLY', 'true', 'true = apply fixes without asking').
env_variable('PFIX_AUTO_INSTALL_DEPS', 'true', 'true = auto pip/uv install').
env_variable('PFIX_AUTO_RESTART', 'false', 'true = os.execv restart after fix').
env_variable('PFIX_MAX_RETRIES', '3', '').
env_variable('PFIX_DRY_RUN', 'false', '').
env_variable('PFIX_ENABLED', 'true', '').
env_variable('PFIX_GIT_COMMIT', 'false', 'true = auto-commit fixes').
env_variable('PFIX_GIT_PREFIX', 'pfix:', 'commit message prefix').
env_variable('PFIX_CREATE_BACKUPS', 'false', 'false = disable .pfix_backups/ directory').

% ── TestQL Scenarios ─────────────────────────────────────
testql_scenario('generated-from-pytests.testql.toon.yaml', 'integration').

% ── Semantic Facts from SUMD.md ──────────────────────────
sumd_declared_file('app.doql.less', 'doql').
sumd_declared_file('testql-scenarios/generated-from-pytests.testql.toon.yaml', 'testql').
sumd_declared_file('project/map.toon.yaml', 'analysis').
sumd_declared_file('project/logic.pl', 'analysis').
sumd_declared_file('project/calls.toon.yaml', 'analysis').
sumd_workflow('test', 'manual').
sumd_workflow('test-js', 'manual').
sumd_workflow_step('test-js', 1, '$(NODE) --test adapters/js/*.test.js').
sumd_workflow('test-python', 'manual').
sumd_workflow_step('test-python', 1, 'PYTHONPATH=adapters/python $(PYTHON) -m unittest discover -s adapters/python/tests -p \'test_*.py\'').
sumd_workflow('test-c', 'manual').
sumd_workflow_step('test-c', 1, '$(CC) -Wall -Wextra -Werror -Iadapters/c adapters/c/urirun.c adapters/c/urirun_test.c -o /tmp/urirun-c-test').
sumd_workflow_step('test-c', 2, '/tmp/urirun-c-test').
sumd_workflow('test-v1', 'manual').
sumd_workflow('test-v2', 'manual').
sumd_workflow('clean', 'manual').
sumd_workflow_step('clean', 1, 'rm -rf node_modules .pytest_cache adapters/python/tests/__pycache__ adapters/python/urirun/__pycache__ adapters/python/*.egg-info adapters/python/build __pycache__').

