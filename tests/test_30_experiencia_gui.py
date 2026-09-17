"""Session overview navigation and diagnostic interactions, without services."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.main_window import MainWindow
from app.ui.workflow_presentation import normalize_status


class ExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_overview_tracks_sidebar_and_next_phase(self):
        home = self.window.home_page
        self.assertEqual(home.next_index, 1)
        self.window._on_phase1_workflow_completed("PER", {})
        self.assertEqual(home.progress.value(), 1)
        self.assertEqual(home.next_index, 2)
        self.window._on_phase2_workflow_status("PER", "action")
        self.assertEqual(home.status_labels["phase2"].text(), "Requiere atención")
        self.assertEqual(self.window.nav_buttons[2].property("workflowStatus"), "action")
        self.window._on_phase2_workflow_status("PER", "done")
        self.assertEqual(home.next_index, 3)
        self.window._on_ambitos_workflow_status("PER", "done")
        self.assertEqual(home.progress.value(), 3)
        self.assertEqual(home.next_button.text(), "Revisar Ámbitos")
        self.window.country_combo.setCurrentIndex(1)
        self.assertIn("EL SALVADOR", home.country_label.text())
        self.assertEqual(home.progress.value(), 0)
        self.assertIn("lista", home.descriptions["phase2"].text())

    def test_shortcuts_only_navigate_and_respect_active_operation(self):
        home = self.window.home_page
        for index, key in enumerate(("users", "phase2", "ambitos"), 1):
            home.phase_buttons[key].click()
            self.assertEqual(self.window.pages.currentIndex(), index)
            self.assertTrue(all(page.thread is None for page in self.window._operation_pages()))
        self.window._show_page(0)
        home.next_button.click()
        self.assertEqual(self.window.pages.currentIndex(), 1)
        self.window.users_page.thread = object()
        try:
            self.window._refresh_operation_state(True)
            self.assertFalse(home.isEnabled())
            home.navigate_requested.emit(3)
            self.assertEqual(self.window.pages.currentIndex(), 1)
        finally:
            self.window.users_page.thread = None
            self.window._refresh_operation_state(False)
        self.assertTrue(home.isEnabled())

    def test_diagnostic_copy_redacts_and_toggle_updates_label(self):
        dialog = AppDialog(self.window, "Error", "Literal <archivo>", details="password=test-secret")
        try:
            dialog.show()
            self.app.processEvents()
            label = dialog.findChild(QLabel, "dialogMessage")
            self.assertEqual(label.textFormat(), Qt.PlainText)
            self.assertEqual(label.text(), "Literal <archivo>")
            dialog.details_button.click()
            self.assertTrue(dialog.details_box.isVisible())
            self.assertEqual(dialog.details_button.text(), "Ocultar detalles técnicos")
            dialog.details_button.click()
            self.assertFalse(dialog.details_box.isVisible())
            with patch("app.ui.dialogs.app_dialog.QApplication.clipboard") as clipboard:
                dialog.copy_details_button.click()
                copied = clipboard.return_value.setText.call_args.args[0]
                self.assertNotIn("test-secret", copied)
                self.assertIn("[REDACTED]", copied)
            self.assertEqual(dialog.copy_details_button.text(), "Diagnóstico copiado")
        finally:
            dialog.close()
            dialog.deleteLater()

    def test_unknown_status_is_pending(self):
        self.assertEqual(normalize_status(" DONE "), "done")
        self.assertEqual(normalize_status("unexpected"), "pending")


if __name__ == "__main__":
    unittest.main()
