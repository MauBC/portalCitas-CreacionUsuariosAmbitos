"""Phase 2 readers release actual XLSX handles, including early exits/errors."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from app.services.user_creation_phase2_service import UserCreationPhase2Service


class ExcelReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.service = UserCreationPhase2Service()
        self.portal = pd.DataFrame({"_item_id": ["001"], "email": ["a@example.test"]})
        self.source = pd.DataFrame({"_item_id": ["001"], "cliente": ["Cliente A"],
                                    "email": ["A@EXAMPLE.TEST"], "observaciones": ["Dato inválido"]})
        self.books = []
        self.original_init = pd.ExcelFile.__init__

    def track_open(self, book, *args, **kwargs):
        self.original_init(book, *args, **kwargs)
        self.books.append(book)

    def assert_released(self, path):
        self.assertEqual(len(self.books), 1)
        self.assertTrue(self.books[0]._reader.handles.handle.closed)
        # Windows refuses this if an XLSX reader still holds the file open.
        renamed = path.with_name("released.xlsx")
        path.rename(renamed)
        renamed.unlink()

    def test_enrichment_preserves_ids_and_closes(self):
        path = self.folder / "reporte_VALIDOS_test.xlsx"
        self.source.to_excel(path, sheet_name="DATOS_TECNICOS", index=False)
        with patch.object(pd.ExcelFile, "__init__", lambda book, *a, **k: self.track_open(book, *a, **k)):
            result = self.service._enrich_portal_result(self.portal, str(self.folder))
        self.assertEqual(result.loc[0, "_item_id"], "001")
        self.assertEqual(result.loc[0, "cliente"], "Cliente A")
        self.assert_released(path)

    def test_missing_technical_sheet_closes_on_early_return(self):
        path = self.folder / "reporte_VALIDOS_test.xlsx"
        self.source.to_excel(path, sheet_name="VALIDOS", index=False)
        with patch.object(pd.ExcelFile, "__init__", lambda book, *a, **k: self.track_open(book, *a, **k)):
            self.assertIs(self.service._enrich_portal_result(self.portal, str(self.folder)), self.portal)
        self.assert_released(path)

    def test_error_sheet_priority_and_fallback(self):
        for sheets in (("ERRORES", "DATOS_TECNICOS"), ("OTRA", "ERRORES"), ("OTRA",)):
            with self.subTest(sheets=sheets):
                self.books.clear()
                path = self.folder / "reporte_ERRORES_test.xlsx"
                with pd.ExcelWriter(path) as writer:
                    for sheet in sheets:
                        data = self.source.assign(observaciones=sheet)
                        data.to_excel(writer, sheet_name=sheet, index=False)
                with patch.object(pd.ExcelFile, "__init__", lambda book, *a, **k: self.track_open(book, *a, **k)):
                    result = self.service._load_local_errors(str(self.folder))
                self.assertEqual(result.loc[0, "mensaje_error"], sheets[-1])
                self.assertEqual(result.loc[0, "creado"], 2)
                self.assertEqual(result.loc[0, "email"], "a@example.test")
                self.assert_released(path)

    def test_parse_failures_close_both_readers(self):
        for prefix in ("VALIDOS", "ERRORES"):
            with self.subTest(prefix=prefix):
                self.books.clear()
                path = self.folder / f"reporte_{prefix}_test.xlsx"
                self.source.to_excel(path, sheet_name="DATOS_TECNICOS", index=False)
                with patch.object(pd.ExcelFile, "__init__", lambda book, *a, **k: self.track_open(book, *a, **k)), \
                        patch.object(pd.ExcelFile, "parse", side_effect=ValueError("Invalid sheet data")):
                    with self.assertRaisesRegex(ValueError, "Invalid sheet data"):
                        if prefix == "VALIDOS":
                            self.service._enrich_portal_result(self.portal, str(self.folder))
                        else:
                            self.service._load_local_errors(str(self.folder))
                self.assert_released(path)


if __name__ == "__main__":
    unittest.main()
