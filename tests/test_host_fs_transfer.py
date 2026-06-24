from urirun.host.fs_transfer import (
    fs_file_transfer_fallback_bindings,
    node_has_route,
    route_key,
)


def test_route_key_ignores_uri_target_for_route_matching() -> None:
    assert route_key("fs://host/file/command/write-b64") == ("fs", "file/command/write-b64")
    assert route_key("fs://lenovo/file/command/write-b64") == ("fs", "file/command/write-b64")


def test_node_has_route_matches_same_route_under_different_target() -> None:
    routes = [{"uri": "fs://host/file/command/write-b64"}]

    assert node_has_route(routes, "fs://lenovo/file/command/write-b64") is True
    assert node_has_route(routes, "fs://lenovo/file/query/read-b64") is False


def test_fs_file_transfer_fallback_bindings_include_only_transfer_routes() -> None:
    bindings = fs_file_transfer_fallback_bindings([
        "fs://host/file/command/write-b64",
        "fs://host/file/query/read-b64",
        "fs://host/duplicates/query/find",
    ])

    assert sorted(bindings["bindings"]) == [
        "fs://host/file/command/write-b64",
        "fs://host/file/query/read-b64",
    ]
    assert bindings["bindings"]["fs://host/file/command/write-b64"]["python"]["export"] == "write_b64"
    assert bindings["bindings"]["fs://host/file/query/read-b64"]["python"]["export"] == "read_b64"
