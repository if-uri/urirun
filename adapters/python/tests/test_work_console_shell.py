# Author: Tom Sapletta · Part of the ifURI solution.

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from urirun.host import work_console


class WorkConsoleShellTests(unittest.TestCase):
    def setUp(self):
        # Reset event hub or any mockable module
        pass

    @patch("urirun.host.work_console.shell_enabled", return_value=True)
    @patch("urirun.host.twin_bridge.TWIN_EVENT_HUB.publish")
    def test_run_shell_success(self, mock_publish, mock_enabled):
        with tempfile.TemporaryDirectory() as tmp:
            res = work_console.run_shell(tmp, "echo hello")
            self.assertTrue(res["ok"])
            self.assertEqual(res["exit"], 0)
            self.assertIn("hello", res["out"])

            mock_publish.assert_called_once()
            event = mock_publish.call_args[0][0]
            self.assertEqual(event["uri"], "shell://host/command/run")
            self.assertEqual(event["type"], "URI_PROCESS")
            self.assertEqual(event["status"], "done")
            self.assertEqual(event["exit"], 0)

    @patch("urirun.host.work_console.shell_enabled", return_value=True)
    @patch("urirun.host.twin_bridge.TWIN_EVENT_HUB.publish")
    @patch("urirun_runtime.errors.record")
    def test_run_shell_command_failure(self, mock_record, mock_publish, mock_enabled):
        with tempfile.TemporaryDirectory() as tmp:
            res = work_console.run_shell(tmp, "exit 42")
            self.assertTrue(res["ok"])
            self.assertEqual(res["exit"], 42)

            mock_publish.assert_called_once()
            event = mock_publish.call_args[0][0]
            self.assertEqual(event["status"], "failed")
            self.assertEqual(event["exit"], 42)

            mock_record.assert_called_once()
            envelope = mock_record.call_args[0][0]
            self.assertFalse(envelope["ok"])
            self.assertEqual(envelope["error"]["type"], "ShellCommandFailed")
            self.assertEqual(envelope["error"]["exit"], 42)

    @patch("urirun.host.work_console.shell_enabled", return_value=True)
    @patch("urirun.host.twin_bridge.TWIN_EVENT_HUB.publish")
    @patch("urirun_runtime.errors.record")
    def test_run_shell_timeout(self, mock_record, mock_publish, mock_enabled):
        with tempfile.TemporaryDirectory() as tmp:
            res = work_console.run_shell(tmp, "sleep 10", timeout=0.01)
            self.assertFalse(res["ok"])
            self.assertIn("timed out", res["error"])

            mock_publish.assert_called_once()
            event = mock_publish.call_args[0][0]
            self.assertEqual(event["status"], "failed")

            mock_record.assert_called_once()
            envelope = mock_record.call_args[0][0]
            self.assertEqual(envelope["error"]["type"], "TimeoutExpired")

    @patch("urirun.host.work_console.shell_enabled", return_value=False)
    @patch("urirun_runtime.errors.record")
    def test_run_shell_disabled(self, mock_record, mock_enabled):
        with tempfile.TemporaryDirectory() as tmp:
            res = work_console.run_shell(tmp, "echo hello")
            self.assertFalse(res["ok"])
            self.assertIn("disabled", res["error"])

            mock_record.assert_called_once()
            envelope = mock_record.call_args[0][0]
            self.assertEqual(envelope["error"]["type"], "PermissionError")


if __name__ == "__main__":
    unittest.main()
