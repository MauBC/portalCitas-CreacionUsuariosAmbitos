"""Local GUI regressions for shared file actions and inline feedback."""

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication

from app.ui.dialogs.app_dialog import AppDialog
from app.ui.file_actions import open_local_path
from app.ui.main_window import MainWindow


class GuiComponentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_open_empty_missing_existing_and_unassociated_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'reporte con espacios.xlsx'
            with patch('app.ui.file_actions.QDesktopServices.openUrl', return_value=True) as launch:
                with patch.object(AppDialog, 'warning') as warning:
                    self.assertFalse(open_local_path(self.window, None))
                    warning.assert_not_called()
                    self.assertFalse(open_local_path(self.window, path))
                    warning.assert_called_once()
                    launch.assert_not_called()
                    warning.reset_mock()
                    path.touch()
                    for page in (self.window.users_page, self.window.phase2_page, self.window.ambitos_page):
                        page._open_path(path)
                        self.assertEqual(launch.call_args.args[0].toLocalFile(), path.resolve().as_posix())
                    self.assertEqual(launch.call_count, 3)
                    warning.assert_not_called()
                    launch.return_value = False
                    self.assertFalse(open_local_path(self.window, path))
                    warning.assert_called_once()

    def test_phase2_and_phase3_inline_feedback(self):
        pages = (
            (self.window.phase2_page, 'run_folder', 'run_folder_error', '_set_field_error', '_clear_field_error'),
            (self.window.ambitos_page, 'valid_report', 'valid_report_error', '_set_inline_error', '_clear_inline_error'),
        )
        for page, field_name, label_name, setter, clearer in pages:
            with self.subTest(page=type(page).__name__):
                field = getattr(page, field_name)
                label = getattr(page, label_name)
                getattr(page, setter)(field, label, 'Falta archivo')
                self.assertTrue(field.property('invalid'))
                self.assertFalse(field.property('valid'))
                self.assertEqual(label.text(), 'Falta archivo')
                self.assertFalse(label.isHidden())
                getattr(page, clearer)(field, label, mark_valid=True)
                self.assertFalse(field.property('invalid'))
                self.assertTrue(field.property('valid'))
                self.assertTrue(label.isHidden())
                self.assertEqual(label.text(), '')
                getattr(page, clearer)(field, label)
                self.assertFalse(field.property('valid'))

    def test_users_feedback_keeps_source_fields_independent(self):
        page = self.window.users_page
        page._set_per_source_error(page.per_url, 'Falta enlace')
        self.assertTrue(page.per_url.property('invalid'))
        self.assertFalse(page.per_file.property('invalid'))
        page._set_per_source_valid(page.per_file)
        self.assertTrue(page.per_file.property('valid'))
        self.assertFalse(page.per_url.property('valid'))
        self.assertFalse(page.per_url.property('invalid'))
        page._clear_per_source_validation()
        self.assertTrue(page.per_source_error.isHidden())
        self.assertFalse(page.per_file.property('valid'))


if __name__ == '__main__':
    unittest.main()
