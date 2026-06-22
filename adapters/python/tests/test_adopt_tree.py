"""adopt-pack on a directory of packs merges every manifest.yaml into one document."""
from __future__ import annotations

from urirun.runtime import adopt_pack

_MANIFEST = """\
id: {pid}
scheme: {scheme}
uri_patterns:
  - pattern: "{scheme}://host/thing/query/list"
    operation: list
    kind: query
handlers:
  python:
    list: "python://{pid}.handlers:list_things"
"""


def _pack(root, pid, scheme):
    d = root / pid
    d.mkdir()
    (d / "manifest.yaml").write_text(_MANIFEST.format(pid=pid, scheme=scheme))


def test_directory_of_packs_merges(tmp_path):
    _pack(tmp_path, "alpha", "al")
    _pack(tmp_path, "beta", "be")
    _pack(tmp_path, "gamma", "ga")
    doc = adopt_pack.adopt(str(tmp_path))
    uris = set(doc["bindings"])
    assert {"al://host/thing/query/list", "be://host/thing/query/list", "ga://host/thing/query/list"} <= uris
    assert len(uris) == 3


def test_single_manifest_dir_unchanged(tmp_path):
    _pack(tmp_path, "solo", "so")
    doc = adopt_pack.adopt(str(tmp_path))
    assert set(doc["bindings"]) == {"so://host/thing/query/list"}
