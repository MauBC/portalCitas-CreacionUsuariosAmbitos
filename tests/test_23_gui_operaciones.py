"""Exercise window guards with real Qt threads and offline backend doubles."""
import os
from pathlib import Path
import sys
from threading import Event
from time import monotonic
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid

from app.ui.dialogs.app_dialog import AppDialog
from app.ui.main_window import MainWindow


class OperationSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_until(self, predicate):
        deadline = monotonic() + 5
        while not predicate() and monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(predicate(), "Qt did not finish the operation in time")

    def test_guards_and_cleanup_after_success_and_failure(self):
        cases = (
            (1, "users_page", "app.main_pipeline.run_pipeline"),
            (2, "phase2_page", "app.ui.workers.phase2_worker.Phase2Worker._run_slv"),
            (3, "ambitos_page", "app.ui.workers.phase3_worker.Phase3Worker._run_preview"),
        )
        for index, name, target in cases:
            for fail in (False, True):
                with self.subTest(page=name, fail=fail):
                    self.exercise_operation(index, name, target, fail)

    def exercise_operation(self, index, name, target, fail):
        entered, release = Event(), Event()

        def backend():
            entered.set()
            if not release.wait(10):
                raise RuntimeError("Test backend timed out")
            if fail:
                raise RuntimeError("Simulated offline failure")
            return {"ok": True}

        window = MainWindow()
        window.country_combo.setCurrentIndex(1)
        window._show_page(index)
        window.show()
        page = getattr(window, name)
        states = []
        page.busy_changed.connect(states.append)
        with patch(target, side_effect=backend), \
                patch.object(AppDialog, "success"), \
                patch.object(AppDialog, "warning") as warning, \
                patch.object(AppDialog, "error") as error, \
                patch(f"app.ui.pages.{name}.build_error_details", return_value="Test error"):
            try:
                if index == 1:
                    page._start_phase1()
                else:
                    page._start_worker("preview")
                self.wait_until(entered.is_set)
                worker = page.worker
                self.assertEqual(states, [True])
                self.assertFalse(page.isEnabled())
                self.assertFalse(window.country_combo.isEnabled())
                self.assertTrue(all(not b.isEnabled() for b in window.nav_buttons))

                # Programmatic navigation must also respect the guard.
                window.country_combo.setCurrentIndex(0)
                window._show_page(0)
                self.assertEqual(window._current_country(), "SLV")
                self.assertEqual(window.pages.currentIndex(), index)
                self.assertEqual(page.country, "SLV")
                self.assertFalse(window.close())
                self.assertTrue(window.isVisible())
                warning.assert_called_once()

                release.set()
                self.wait_until(lambda: page.thread is None)
                self.wait_until(lambda: not isValid(worker))
                self.assertEqual(states, [True, False])
                self.assertTrue(page.isEnabled())
                self.assertTrue(window.country_combo.isEnabled())
                self.assertTrue(all(b.isEnabled() for b in window.nav_buttons))
                self.assertEqual(error.call_count, int(fail))
                window.country_combo.setCurrentIndex(0)
                window._show_page(0)
                self.assertEqual(page.country, "PER")
                self.assertEqual(window.pages.currentIndex(), 0)
                self.assertTrue(window.close())
            finally:
                release.set()
                self.wait_until(lambda: page.thread is None)
                window.close()
                window.deleteLater()
                self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
