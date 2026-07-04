# Guards the single-source-of-truth invariant for externally-owned packages.
# History: adapters/python carried stale snapshots of urirun_flow / urirun_connector_router /
# urirun_scanner that silently shadowed the owning repos (editable finders sit at the END of
# sys.meta_path, so any sys.path entry wins). These tests fail loudly if that returns.
from __future__ import annotations

import importlib
import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import dev_deps_doctor as doctor  # noqa: E402

_ADAPTERS = Path(__file__).resolve().parents[1]
_EXTERNALLY_OWNED = ["urirun_flow", "urirun_connector_router", "urirun_connector_scanner"]


@pytest.mark.parametrize("name", _EXTERNALLY_OWNED)
def test_externally_owned_package_resolves_outside_adapters(name):
    mod = importlib.import_module(name)
    origin = str(Path(mod.__file__).resolve())
    assert not origin.startswith(str(_ADAPTERS)), (
        f"{name} loaded from the adapters snapshot ({origin}) — the owning sibling repo "
        f"must win; check conftest sibling-path ordering and delete the stale copy"
    )


def test_editable_owner_mapping_readable():
    site = doctor._site_packages()
    assert site is not None
    owners = doctor.editable_owners(site)
    # the two packages this repo historically shadowed must have editable owners
    assert "urirun_flow" in owners
    assert "urirun_connector_router" in owners
    for name in ("urirun_flow", "urirun_connector_router"):
        assert not str(owners[name]).startswith(str(_ADAPTERS))


def test_under_git_walks_up_to_repo_root():
    assert doctor._under_git(_ADAPTERS / "urirun") is True  # nested package, .git two levels up


def test_version_key_orders_semantic_versions():
    assert doctor._version_key("0.1.106") > doctor._version_key("0.1.48")
    assert doctor._version_key("2.1.266") > doctor._version_key("2.1.254")
    assert doctor._version_key("0.2.0") == doctor._version_key("0.2.0")


def test_stale_install_detected_from_fake_dist_info(tmp_path):
    repo = tmp_path / "mylib"
    repo.mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "mylib"\nversion = "1.2.0"\n')
    di = tmp_path / "site" / "mylib-1.0.0.dist-info"
    di.mkdir(parents=True)
    (di / "METADATA").write_text("Name: mylib\nVersion: 1.0.0\n\n")
    (di / "direct_url.json").write_text(
        '{"dir_info": {}, "url": "file://%s"}' % repo)
    findings = doctor.local_install_health(tmp_path / "site")
    assert len(findings) == 1
    assert findings[0]["verdict"].startswith("STALE-INSTALL")
    assert findings[0]["fix"].endswith(str(repo))


def test_editable_installs_are_never_stale(tmp_path):
    repo = tmp_path / "mylib"
    repo.mkdir()
    (repo / "pyproject.toml").write_text('[project]\nname = "mylib"\nversion = "9.9.9"\n')
    di = tmp_path / "site" / "mylib-1.0.0.dist-info"
    di.mkdir(parents=True)
    (di / "METADATA").write_text("Name: mylib\nVersion: 1.0.0\n\n")
    (di / "direct_url.json").write_text(
        '{"dir_info": {"editable": true}, "url": "file://%s"}' % repo)
    assert doctor.local_install_health(tmp_path / "site") == []


def test_this_venv_has_no_stale_local_installs():
    """LIVE guard: the suite goes red the day a local dependency is installed at a
    version older than its source repo declares — the recurring 'stale library'
    class gets caught at test time instead of mid-debug."""
    site = doctor._site_packages()
    assert site is not None
    stale = [h for h in doctor.local_install_health(site) if h["verdict"].startswith("STALE")]
    assert not stale, "stale local installs (run scripts/dev_deps_doctor.py --fix):\n" + "\n".join(
        f"  {h['name']} {h['installed']} < {h['sourceVersion']} ({h['source']})" for h in stale)
