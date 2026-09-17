from __future__ import annotations

import traceback
from app.services.run_history_service import HistorySession

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)


class Phase3Worker(QObject):
    progress = Signal(str)
    finished = Signal(str, dict)
    failed = Signal(str, str, str)

    def __init__(
        self,
        country: str,
        mode: str,
        valid_report_path: str,
        provider_shared_url: str | None = None,
        review_path: str | None = None,
    ):
        super().__init__()

        self.country = str(
            country or ""
        ).strip().upper()

        self.mode = str(
            mode or ""
        ).strip().lower()

        self.valid_report_path = str(
            valid_report_path or ""
        ).strip()

        self.provider_shared_url = str(
            provider_shared_url or ""
        ).strip()

        self.review_path = str(
            review_path or ""
        ).strip()

    @Slot()
    def run(self):
        history = HistorySession(phase=3, country=self.country, mode=self.mode,
                                 inputs={"valid_report_path": self.valid_report_path, "review_path": self.review_path}, notify=self.progress.emit)
        try:
            if self.mode == "preview":
                result = self._run_preview()

            elif self.mode == "final":
                result = self._run_final()

            else:
                raise ValueError(
                    f"Modo Fase 3 invalido: {self.mode}"
                )

            history.finish(result)
            self.finished.emit(
                self.mode,
                result,
            )

        except Exception as exc:
            history.fail()
            self.failed.emit(
                self.mode,
                f"{type(exc).__name__}: {exc}",
                traceback.format_exc(),
            )

    def _run_preview(self):
        self.progress.emit(
            "Leyendo estados de creación "
            "y preparando ámbitos..."
        )

        from app.phase3_pipeline import (
            run_phase3_preview,
        )

        return run_phase3_preview(
            valid_report_path=(
                self.valid_report_path
            ),
            country_code=self.country,
            provider_shared_url=(
                self.provider_shared_url
                if self.country == "PER"
                else None
            ),
        )

    def _run_final(self):
        self.progress.emit(
            "Generando plantilla final de ámbitos..."
        )

        from app.phase3_pipeline import (
            run_phase3_final,
        )

        return run_phase3_final(
            valid_report_path=(
                self.valid_report_path
            ),
            review_path=(
                self.review_path
                or None
            ),
            country_code=self.country,
            provider_shared_url=(
                self.provider_shared_url
                if self.country == "PER"
                else None
            ),
        )
