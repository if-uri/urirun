# One @conn.handler declaration must project to OpenAPI too (URI+MCP+A2A+OpenAPI+CLI).
import urirun


def _conn():
    c = urirun.connector("demo", scheme="demo")
    @c.handler("thing/command/do", meta={"label": "Do the thing"})
    def do(x: str = "", n: int = 0):
        return urirun.ok(connector="demo", x=x, n=n)
    return c


def test_connector_projects_openapi():
    oa = _conn().openapi(title="demo", version="1.2.3")
    assert oa["openapi"].startswith("3.") and oa["info"]["version"] == "1.2.3"
    assert "/thing/command/do" in oa["paths"]
    op = oa["paths"]["/thing/command/do"]["post"]
    assert op["summary"] == "Do the thing" and op["x-uri"].startswith("demo://")
    props = op["requestBody"]["content"]["application/json"]["schema"].get("properties", {})
    assert "x" in props and "n" in props   # request body derived from the handler signature


def test_same_declaration_gives_every_surface():
    c = _conn()
    assert c.mcp_tools() and c.a2a_card()["skills"] and c.openapi()["paths"] and c.bindings()
