import os
from pathlib import Path
import sys
import tempfile
from time import monotonic
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from app.config import paths
from app.services.run_history_service import HistorySession
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.main_window import MainWindow


class RecoveryGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patch = patch.object(paths, "OUTPUT_ROOT", self.root)
        self.patch.start()
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()
        self.patch.stop()
        self.temp.cleanup()

    def test_history_recovery_does_not_restore_remote_approval(self):
        (self.root / "usuarios_enviados.xlsx").touch()
        report = self.root / "reporte_VALIDOS_1.xlsx"
        report.touch()
        portal = self.root / "portal.xlsx"
        portal.touch()
        session = HistorySession(phase=2, country="PER", mode="apply",
                                 inputs={"run_folder": str(self.root), "portal_result": str(portal)})
        session.finish({"ok": True})
        page = self.window.phase2_page
        page.remote_replacement_verified = True
        page.last_preview = {"ok": True}
        page.last_local_copy = {"candidate_path": "old.xlsx"}
        self.window._show_page(4)
        history = self.window.history_page
        self.assertEqual(history.table.rowCount(), 1)
        history.table.selectRow(0)
        history.resume_button.click()
        self.assertEqual(self.window.pages.currentIndex(), 2)
        self.assertEqual(page.run_folder.text(), str(self.root))
        self.assertEqual(page.portal_result.text(), str(portal))
        self.assertEqual(self.window.ambitos_page.valid_report.text(), str(report))
        self.assertIsNone(page.last_preview)
        self.assertIsNone(page.last_local_copy)
        self.assertFalse(page.remote_replacement_verified)
        self.assertFalse(page.apply_button.isEnabled())
        self.assertFalse(self.window.ambitos_page.final_button.isEnabled())
        self.assertEqual(self.window.home_page.progress.value(), 0)

    def test_missing_inputs_warn_without_destroying_current_work(self):
        self.window.phase2_page.portal_result.setText("current.xlsx")
        with patch.object(AppDialog, "warning") as warning:
            self.window._restore_execution({"country": "PER", "phase": 2, "inputs": {}, "outputs": {}})
        warning.assert_called_once()
        self.assertEqual(self.window.phase2_page.portal_result.text(), "current.xlsx")

    def test_connection_page_finishes_and_unlocks(self):
        page = self.window.connection_page
        with patch("app.ui.pages.connection_page.check_connections", return_value=[{"name": "Test", "ok": True, "detail": "Offline"}]):
            page.start()
            self.assertFalse(self.window.country_combo.isEnabled())
            deadline = monotonic() + 5
            while page.thread is not None and monotonic() < deadline:
                QTest.qWait(10)
        self.assertIsNone(page.thread)
        self.assertTrue(self.window.country_combo.isEnabled())
        self.assertIn("Test: OK", page.results.toPlainText())

    def test_write_confirmation_contains_preview_counts(self):
        page = self.window.phase2_page
        page.last_preview = {"cuentas_enviadas": 3, "actualizaciones_remotas_preview": 5}
        page.preview_signature = page._current_signature()
        with patch.object(AppDialog, "confirm", return_value=False) as confirm, patch.object(page, "_start_worker") as start:
            page._confirm_apply()
        self.assertIn("Cuentas enviadas: 3", confirm.call_args.args[2])
        self.assertIn("Cambios remotos: 5", confirm.call_args.args[2])
        start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
