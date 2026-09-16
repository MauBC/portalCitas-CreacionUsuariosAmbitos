"""Presentation contracts preserve counts and do not mutate backend results."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ui.result_models import Phase1Summary, Phase2Presentation, scope_metrics


class PresentationTests(unittest.TestCase):
    def test_accounts_and_relations_are_distinct(self):
        source = {"total": 287, "valid_relations": 246, "errors": 41, "unique_users": 230}
        original = deepcopy(source)
        summary = Phase1Summary.from_backend("PER", source)
        self.assertEqual((summary.total, summary.valid, summary.errors, summary.users), (287, 246, 41, 230))
        self.assertEqual(source, original)
        slv = Phase1Summary.from_backend("SLV", {"total": 3, "validos": 2, "errores": 1})
        self.assertEqual((slv.valid, slv.users, slv.errors), (2, 2, 1))

    def test_all_phase2_modes(self):
        cases = [
            ("PER", "preview", {"cuentas_enviadas": 230, "cuentas_disponibles": 220,
                                "cuentas_no_creadas": 10, "actualizaciones_remotas_preview": 246},
             [230, 220, 10, 246]),
            ("SLV", "preview", {"total": 4, "creados": 3, "errores": 1, "preview": [{}, {}]},
             [4, 3, 1, 2]),
            ("PER", "local_copy", {"cambios_aplicados": 287, "verificado_creado_1": 246,
                                   "verificado_creado_2": 41, "filas_verificadas": 287},
             [287, 246, 41, 287]),
            ("PER", "apply", {"relaciones_total": 287, "verificado_creado_1": 246,
                              "verificado_creado_2": 41, "filas_verificadas": 287},
             [287, 246, 41, 287]),
            ("SLV", "apply", {"total": 4, "creados": 3, "errores": 1, "updated": 4}, [4, 3, 1, 4]),
        ]
        for country, mode, source, expected in cases:
            with self.subTest(country=country, mode=mode):
                original = deepcopy(source)
                result = Phase2Presentation.from_backend(country, mode, source)
                self.assertEqual([metric.value for metric in result.metrics], expected)
                self.assertEqual(source, original)
                if mode == "apply":
                    self.assertIsNone(result.files)

    def test_local_copy_is_presented_as_local(self):
        result = Phase2Presentation.from_backend("PER", "local_copy", {"candidate_path": "local.xlsx"})
        self.assertIn("SharePoint NO fue modificado", result.detail)
        self.assertTrue(result.files.result_available)
        self.assertFalse(result.files.evidence_available)
        self.assertEqual(result.files.result_label, "Abrir copia local")

    def test_scope_counts_and_defaults(self):
        result = scope_metrics("final", {"creado_1": 246, "registros_finales": 246,
                                         "relacion_nueva": 138, "ambitos": 231})
        self.assertEqual([metric.value for metric in result], [246, 246, 0, 0, 138, 231])
        self.assertEqual([metric.value for metric in scope_metrics("preview", {})], [0] * 6)
        with self.assertRaises(ValueError):
            Phase2Presentation.from_backend("SLV", "local_copy", {})


if __name__ == "__main__":
    unittest.main()
