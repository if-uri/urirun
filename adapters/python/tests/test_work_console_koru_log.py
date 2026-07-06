# Author: Tom Sapletta · Part of the ifURI solution.

import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from urirun.host import work_console


class WorkConsoleKoruLogTests(unittest.TestCase):
    def test_stale_stopped_koru_log_reports_loop_controller(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / ".planfile" / ".koru" / "queue.log"
            log.parent.mkdir(parents=True)
            log.write_text("[13:03:49] koru ▸ KORUAUTONOMOUS: SIGTERM received\n", encoding="utf-8")
            old = time.time() - 3600
            os.utime(log, (old, old))

            with (
                patch.dict(os.environ, {"URIRUN_KORU_PROJECT": tmp}, clear=False),
                patch("urirun.host.work_queue.koru_status", return_value={"running": False}),
                patch("urirun.host.work_queue._loop_controller_active", return_value=True),
            ):
                result = work_console.koru_log_tail(20)

        self.assertEqual(result["controller"], "loop://")
        self.assertFalse(result["live"])
        self.assertTrue(result["stale"])
        self.assertGreaterEqual(result["source_age_seconds"], 3500)
        self.assertEqual(result["lines"][-1]["type"], "CTRL")
        self.assertIn("queue.log nie jest aktywnym kontrolerem", result["lines"][-1]["text"])

    def test_fresh_running_koru_log_is_live_without_control_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / ".planfile" / ".koru" / "queue.log"
            log.parent.mkdir(parents=True)
            log.write_text("[13:00:00] koru ▸ QUEUE: cycle=1 queue=open\n", encoding="utf-8")

            with (
                patch.dict(os.environ, {"URIRUN_KORU_PROJECT": tmp}, clear=False),
                patch("urirun.host.work_queue.koru_status", return_value={"running": True}),
                patch("urirun.host.work_queue._loop_controller_active", return_value=False),
            ):
                result = work_console.koru_log_tail(20)

        self.assertEqual(result["controller"], "koru")
        self.assertTrue(result["live"])
        self.assertFalse(result["stale"])
        self.assertNotIn("CTRL", [line["type"] for line in result["lines"]])


if __name__ == "__main__":
    unittest.main()
