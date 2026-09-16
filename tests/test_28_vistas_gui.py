"""Views are standalone; controllers still connect each user action once."""
from contextlib import ExitStack
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication
from app.ui.pages.users_page import UsersPage
from app.ui.pages.ambitos_page import AmbitosPage
from app.ui.views.users_view import UsersView
from app.ui.views.ambitos_view import AmbitosView


class ViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def dispose(self, widget):
        widget.close()
        widget.deleteLater()
        self.app.processEvents()

    def test_views_build_without_settings_or_controller(self):
        for view_type in (UsersView, AmbitosView):
            with self.subTest(view=view_type.__name__):
                view = view_type()
                try:
                    self.assertFalse(hasattr(view, "settings"))
                    self.assertNotIn("thread", view.__dict__)
                    self.assertTrue(view.result_card.isHidden())
                    action = view.continue_phase2_button if isinstance(view, UsersView) else view.final_button
                    self.assertFalse(action.isEnabled())
                finally:
                    self.dispose(view)

    def test_buttons_keep_their_controller_actions(self):
        cases = (
            (UsersPage, {
                "browse_button": "_browse_per_file", "run_button": "_start_phase1",
                "open_folder_button": "_open_run_folder", "open_template_button": "_open_template",
                "open_valid_button": "_open_valid", "open_error_button": "_open_errors",
            }),
            (AmbitosPage, {
                "report_button": "_browse_valid_report", "review_button": "_browse_review",
                "preview_button": "_start_preview", "final_button": "_start_final",
                "open_preview_button": "_open_preview", "open_diagnostic_button": "_open_diagnostic",
                "open_review_button": "_open_review", "open_final_button": "_open_final",
                "open_folder_button": "_open_folder",
            }),
        )
        for page_type, actions in cases:
            with self.subTest(page=page_type.__name__), ExitStack() as stack:
                mocks = {button: stack.enter_context(patch.object(page_type, method))
                         for button, method in actions.items()}
                page = page_type()
                try:
                    for button, handler in mocks.items():
                        control = getattr(page, button)
                        control.setEnabled(True)
                        control.click()
                        handler.assert_called_once()
                finally:
                    self.dispose(page)

    def test_saved_url_and_users_source_navigation(self):
        for page_type, field in ((UsersPage, "per_url"), (AmbitosPage, "shared_url")):
            with self.subTest(page=page_type.__name__), patch(f"{page_type.__module__}.QSettings") as settings:
                settings.return_value.value.return_value = "https://example.test/saved"
                page = page_type()
                try:
                    self.assertEqual(getattr(page, field).text(), "https://example.test/saved")
                    if isinstance(page, UsersPage):
                        page.per_source_combo.setCurrentIndex(1)
                        self.assertEqual(page.per_input_stack.currentIndex(), 1)
                        page.per_source_combo.setCurrentIndex(0)
                        self.assertEqual(page.per_input_stack.currentIndex(), 0)
                        destinations = []
                        page.navigate_requested.connect(destinations.append)
                        page.continue_phase2_button.setEnabled(True)
                        page.continue_phase2_button.click()
                        self.assertEqual(destinations, [2])
                finally:
                    self.dispose(page)


if __name__ == "__main__":
    unittest.main()
