# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

import tempfile
import unittest
from pathlib import Path

from urirun import mesh


class MeshTests(unittest.TestCase):
    def test_host_config_add_node(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "mesh.json")
            config = mesh.init_host(path, name="host-a")
            self.assertEqual(config["host"]["name"], "host-a")

            updated = mesh.add_node(path, "node-a", "http://127.0.0.1:8765/", ["lab"])
            self.assertEqual(updated["nodes"], [{"name": "node-a", "url": "http://127.0.0.1:8765", "tags": ["lab"]}])
            self.assertEqual(mesh.load_host_config(path)["nodes"][0]["name"], "node-a")

    def test_node_config_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "node.json")
            config = mesh.init_node(path, name="node-a", registry="registry.json", port=9999, execute=True)
            self.assertEqual(config["node"]["name"], "node-a")
            self.assertEqual(config["node"]["registry"], "registry.json")
            self.assertEqual(config["node"]["port"], 9999)
            self.assertTrue(config["node"]["execute"])

    def test_heuristic_flow_uses_all_reachable_nodes(self):
        nodes = [
            {"name": "pc1", "reachable": True},
            {"name": "pc2", "reachable": True},
        ]
        routes = [
            {"uri": "env://pc1/runtime/query/health", "safe": True},
            {"uri": "proc://pc1/process/query/list", "safe": True},
            {"uri": "env://pc2/runtime/query/health", "safe": True},
            {"uri": "proc://pc2/process/query/list", "safe": True},
        ]
        flow = mesh.heuristic_flow("pokaz procesy na wszystkich komputerach", routes, nodes)
        uris = [step["uri"] for step in flow["steps"]]
        self.assertIn("proc://pc1/process/query/list", uris)
        self.assertIn("proc://pc2/process/query/list", uris)

    def test_registry_from_remote_routes(self):
        registry = mesh.registry_from_routes([
            {
                "uri": "proc://pc1/process/query/list",
                "kind": "query",
                "adapter": "ps",
                "safe": True,
                "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer"}}},
            }
        ])
        flattened = mesh.routes_from_registry(registry)
        self.assertEqual(flattened[0]["uri"], "proc://pc1/process/query/list")
        self.assertEqual(flattened[0]["adapter"], "http-service")


if __name__ == "__main__":
    unittest.main()
