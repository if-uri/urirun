# Author: Tom Sapletta · https://tom.sapletta.com
# Part of the ifURI solution.

import contextlib
import io
import json
import unittest
from unittest.mock import patch

import urirun
from urirun import compat


class CompatReportTests(unittest.TestCase):
    def test_report_marks_installed_connector_replacement_ready(self):
        def importable(name):
            return name in {"urirun.planfile_adapter", "urirun_connector_planfile"}

        with patch.object(compat, "_entry_point_names", return_value={"planfile"}), \
             patch.object(compat, "_importable", side_effect=importable):
            data = compat.report()

        planfile = next(item for item in data["modules"] if item["module"] == "urirun.planfile_adapter")
        self.assertEqual(planfile["owner"], "connector")
        self.assertEqual(planfile["replacement"], "urirun-connector-planfile")
        self.assertTrue(planfile["replacementInstalled"])
        self.assertTrue(planfile["entryPointInstalled"])
        self.assertTrue(planfile["migrationReady"])

    def test_top_level_api_exposes_compat_report(self):
        data = urirun.compat_report()
        self.assertTrue(data["ok"])
        self.assertTrue(any(item["module"] == "urirun.host_integrations" for item in data["modules"]))

    def test_cli_list_json(self):
        with patch.object(compat, "_entry_point_names", return_value=set()), \
             patch.object(compat, "_importable", return_value=False):
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                code = compat.main(["list", "--json"])

        self.assertEqual(code, 0)
        data = json.loads(buffer.getvalue())
        self.assertTrue(data["ok"])
        self.assertGreater(data["pending"], 0)
        self.assertGreater(data["blockingPending"], 0)
        self.assertTrue(any(item["module"] == "urirun.mesh" for item in data["modules"]))

    def test_cli_check_returns_non_zero_when_replacements_missing(self):
        with patch.object(compat, "_entry_point_names", return_value=set()), \
             patch.object(compat, "_importable", return_value=False), \
             contextlib.redirect_stdout(io.StringIO()):
            code = compat.main(["check"])

        self.assertEqual(code, 1)

    def test_cli_check_ignores_internal_compat_bridge_when_replacements_ready(self):
        replacement_imports = {
            "urirun_connector_planfile",
            "urirun_connector_sqlite_context",
            "urirun_connector_domain_monitor",
            "urirun_connector_namecheap_dns",
            "ifuri_app",
        }
        entry_points = {"planfile", "sqlite-context", "domain-monitor", "namecheap-dns"}

        with patch.object(compat, "_entry_point_names", return_value=entry_points), \
             patch.object(compat, "_importable", side_effect=lambda name: name in replacement_imports), \
             contextlib.redirect_stdout(io.StringIO()):
            code = compat.main(["check"])

        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
