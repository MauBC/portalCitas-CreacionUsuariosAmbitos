"""Local execution journal. Store paths and status, never credentials or row data."""
from datetime import datetime
import json
import os
from pathlib import Path
from uuid import uuid4

from app.config import paths

INPUT_KEYS = {"run_folder", "portal_result", "valid_report_path", "review_path", "file_path", "source_type"}
OUTPUT_KEYS = {
    "run_folder", "valid_path", "path_validos", "template_path", "path_template",
    "error_path", "path_errores", "log_path", "preview_path", "result_path",
    "candidate_path", "report_path", "plan_path", "evidence_path", "diagnostics_path", "review_path",
}
STATUS_LABELS = {"running": "Sin cierre registrado", "finished": "Terminó", "failed": "Error",
                 "not_completed": "No completada", "legacy": "Sin registro de estado"}


def _strings(values, allowed):
    return {key: str(value) for key, value in values.items()
            if key in allowed and isinstance(value, (str, Path)) and str(value)}


class RunHistory:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else paths.OUTPUT_ROOT / ".history"

    def save(self, record):
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / f"{record['id']}.json"
        temporary = target.with_suffix(".tmp")
        try:
            temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    def list_runs(self):
        records = []
        skipped = 0
        for path in self.root.glob("*.json"):
            try:
                if path.stat().st_size > 1_000_000:
                    raise ValueError("Record too large")
                record = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(record, dict) or record.get("version") != 1:
                    raise ValueError("Unknown record")
                if record.get("country") not in {"PER", "SLV"} or record.get("phase") not in {1, 2, 3}:
                    raise ValueError("Unknown flow")
                if record.get("status") not in STATUS_LABELS or not isinstance(record.get("created"), str):
                    raise ValueError("Unknown status")
                record["inputs"] = _strings(record.get("inputs", {}), INPUT_KEYS)
                record["outputs"] = _strings(record.get("outputs", {}), OUTPUT_KEYS)
                records.append(record)
            except (OSError, ValueError, TypeError, AttributeError):
                skipped += 1
        return sorted(records, key=lambda item: item["created"], reverse=True), skipped


class HistorySession:
    def __init__(self, *, phase, country, mode, inputs, notify=lambda message: None, store=None):
        self.store = store or RunHistory()
        self.notify = notify
        self.record = {"version": 1, "id": uuid4().hex,
                       "created": datetime.now().isoformat(timespec="seconds"),
                       "phase": phase, "country": country, "mode": mode,
                       "status": "running", "inputs": _strings(inputs, INPUT_KEYS), "outputs": {}}
        self._save()

    def _save(self):
        try:
            self.store.save(self.record)
        except OSError:
            self.notify("No se pudo guardar el historial local; la operación continúa.")

    def finish(self, result):
        self.record["outputs"] = _strings(result, OUTPUT_KEYS)
        self.record["status"] = "not_completed" if result.get("ok") is False else "finished"
        self.record["ended"] = datetime.now().isoformat(timespec="seconds")
        self._save()

    def fail(self):
        self.record["status"] = "failed"
        self.record["ended"] = datetime.now().isoformat(timespec="seconds")
        self._save()


def inspect_legacy_folder(folder, country):
    folder = Path(folder).resolve()
    reports = sorted(folder.glob("reporte*VALIDOS*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not (folder / "usuarios_enviados.xlsx").is_file() and not reports:
        raise ValueError("La carpeta no contiene un manifiesto ni un reporte VALIDOS de Fase 1.")
    return {"country": country, "phase": 1, "mode": "legacy", "status": "legacy", "inputs": {},
            "outputs": {"run_folder": str(folder), **({"valid_path": str(reports[0])} if reports else {})}}


def recovery_inputs(record):
    """Recover existing inputs, without restoring preview results or remote state."""
    inputs, outputs = record.get("inputs", {}), record.get("outputs", {})
    values = dict(inputs)
    if record["phase"] == 1:
        values["run_folder"] = outputs.get("run_folder", "")
        values["valid_report_path"] = outputs.get("valid_path", outputs.get("path_validos", ""))
    recovered = {key: value for key, value in values.items()
                 if key != "source_type" and Path(value).is_file()}
    folder = values.get("run_folder")
    if folder and (Path(folder) / "usuarios_enviados.xlsx").is_file():
        recovered["run_folder"] = folder
    if "valid_report_path" not in recovered and folder:
        reports = sorted(Path(folder).glob("reporte*VALIDOS*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
        if reports:
            recovered["valid_report_path"] = str(reports[0])
    return recovered
