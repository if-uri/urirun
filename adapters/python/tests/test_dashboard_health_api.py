from __future__ import annotations

from urirun.host import dashboard_api as da


def test_dashboard_health_identifies_current_dashboard():
    status, body = da._dashboard_api_response(
        "/api/health",
        "C:/work/project",
        "C:/work/host.db",
        "C:/work/mesh.json",
        {},
        ["node=http://127.0.0.1:8765"],
    )

    assert status == 200
    assert body["ok"] is True
    assert body["service"] == "urirun-host-dashboard"
    assert body["version"]
    assert body["project"] == "C:/work/project"
    assert body["db"] == "C:/work/host.db"
    assert body["config"] == "C:/work/mesh.json"
    assert body["nodeUrls"] == ["node=http://127.0.0.1:8765"]
