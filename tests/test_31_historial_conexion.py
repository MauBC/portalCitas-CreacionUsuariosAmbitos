from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.run_history_service import HistorySession, RunHistory, inspect_legacy_folder, recovery_inputs
from app.services.connection_check_service import check_connections


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.store = RunHistory(self.root / ".history")

    def test_persistence_allowlist_and_status(self):
        session = HistorySession(phase=2, country="PER", mode="preview",
                                 inputs={"run_folder": str(self.root), "shared_url": "private-link", "password": "secret"},
                                 store=self.store)
        records, _ = self.store.list_runs()
        self.assertEqual(records[0]["status"], "running")
        session.finish({"ok": True, "candidate_path": "output.xlsx", "rows": [{"email": "private"}]})
        records, skipped = RunHistory(self.store.root).list_runs()
        self.assertEqual(skipped, 0)
        self.assertEqual(records[0]["status"], "finished")
        self.assertEqual(records[0]["outputs"], {"candidate_path": "output.xlsx"})
        content = next(self.store.root.glob("*.json")).read_text(encoding="utf-8")
        self.assertNotIn("private", content)
        self.assertNotIn("secret", content)
        session.fail()
        self.assertEqual(self.store.list_runs()[0][0]["status"], "failed")

    def test_invalid_record_does_not_hide_valid_history(self):
        session = HistorySession(phase=1, country="SLV", mode="users", inputs={}, store=self.store)
        session.finish({"ok": False})
        (self.store.root / "broken.json").write_text("invalid", encoding="utf-8")
        (self.store.root / "future.json").write_text('{"version": 2}', encoding="utf-8")
        records, skipped = self.store.list_runs()
        self.assertEqual(len(records), 1)
        self.assertEqual(skipped, 2)
        self.assertEqual(records[0]["status"], "not_completed")

    def test_journal_failure_does_not_fail_operation(self):
        notices = []
        with patch.object(self.store, "save", side_effect=PermissionError):
            session = HistorySession(phase=1, country="PER", mode="users", inputs={}, store=self.store, notify=notices.append)
            session.finish({"ok": True})
        self.assertEqual(len(notices), 2)

    def test_legacy_recovery_requires_artifacts_and_rechecks_existence(self):
        with self.assertRaises(ValueError):
            inspect_legacy_folder(self.root, "PER")
        manifest = self.root / "usuarios_enviados.xlsx"
        report = self.root / "reporte_excel_VALIDOS_1.xlsx"
        manifest.touch()
        report.touch()
        record = inspect_legacy_folder(self.root, "PER")
        recovered = recovery_inputs(record)
        self.assertEqual(recovered["run_folder"], str(self.root))
        self.assertEqual(recovered["valid_report_path"], str(report))
        manifest.unlink()
        report.unlink()
        self.assertEqual(recovery_inputs(record), {})

    def test_connection_checks_are_independent_and_read_only(self):
        with patch("app.services.connection_check_service.PostgresClient") as db, \
                patch("app.services.connection_check_service.SharePointClient") as sp:
            db.return_value.fetch_all.side_effect = RuntimeError("password=private")
            result = check_connections("SLV", lambda message: None)
            self.assertFalse(result[0]["ok"])
            self.assertNotIn("private", result[0]["detail"])
            self.assertTrue(result[1]["ok"])
            db.return_value.fetch_all.assert_called_once_with("SELECT 1 AS connection_ok")
            sp.return_value.get_list_id.assert_called_once()
            sp.return_value.update_list_item_fields.assert_not_called()
            sp.reset_mock()
            check_connections("PER", lambda message: None)
            sp.return_value.get_site_id.assert_called_once()
            sp.return_value.get_list_id.assert_not_called()


if __name__ == "__main__":
    unittest.main()
