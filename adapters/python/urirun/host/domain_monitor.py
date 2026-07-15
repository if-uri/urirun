# Back-compat shim — domain monitor backend moved to
# urirun-connector-domain-monitor/urirun_connector_domain_monitor/host_service.py.
#
# Load the backend module directly. Importing the package would execute its
# __init__/core, and core imports urirun.host.domain_monitor as the backend,
# creating a circular import.
from __future__ import annotations

import importlib.util
import sys as _sys
from pathlib import Path


def _installed_host_service_path() -> Path | None:
    """Resolve via the package's own (editable) install location — works regardless of where
    urirun-connector-domain-monitor's repo checkout lives (e.g. after the 2026-07-15 move to
    github.com/urirun-connectors + ~/github/urirun-connectors). find_spec on a top-level name
    does not execute the package's __init__.py, so this stays safe from the circular import."""
    try:
        spec = importlib.util.find_spec("urirun_connector_domain_monitor")
    except (ImportError, ValueError):
        return None
    if spec is None or not spec.submodule_search_locations:
        return None
    for location in spec.submodule_search_locations:
        candidate = Path(location) / "host_service.py"
        if candidate.is_file():
            return candidate
    return None


def _local_host_service_path() -> Path | None:
    installed = _installed_host_service_path()
    if installed is not None:
        return installed
    # Last-resort fallback for a source checkout that isn't pip-installed at all: sibling search.
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = (
            parent
            / "urirun-connector-domain-monitor"
            / "urirun_connector_domain_monitor"
            / "host_service.py"
        )
        if candidate.is_file():
            return candidate
    return None


def _load_host_service():
    source = _local_host_service_path()
    if source is None:
        raise ImportError("urirun_connector_domain_monitor.host_service is not available")
    spec = importlib.util.spec_from_file_location("_urirun_domain_monitor_host_service", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load domain monitor host service from {source}")
    module = importlib.util.module_from_spec(spec)
    _sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_sys.modules[__name__] = _load_host_service()
