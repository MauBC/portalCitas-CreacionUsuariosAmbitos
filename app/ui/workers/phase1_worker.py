from __future__ import annotations

import traceback
from app.services.run_history_service import HistorySession

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)


class Phase1Worker(QObject):
    progress = Signal(str)
    finished = Signal(dict)
    failed = Signal(str, str)

    def __init__(
        self,
        country: str,
        source_type: str | None = None,
        file_path: str | None = None,
        shared_url: str | None = None,
    ):
        super().__init__()

        self.country = str(
            country or ""
        ).strip().upper()

        self.source_type = str(
            source_type or ""
        ).strip().lower()

        self.file_path = str(
            file_path or ""
        ).strip()

        self.shared_url = str(
            shared_url or ""
        ).strip()

    @Slot()
    def run(self):
        history = HistorySession(phase=1, country=self.country, mode="users",
                                 inputs={"file_path": self.file_path, "source_type": self.source_type}, notify=self.progress.emit)
        try:
            if self.country == "SLV":
                self.progress.emit(
                    "Leyendo registros de SharePoint..."
                )

                from app.main_pipeline import (
                    run_pipeline,
                )

                result = run_pipeline()

            elif self.country == "PER":
                self.progress.emit(
                    "Leyendo Excel de proveedores..."
                )

                from app.provider_excel_pipeline import (
                    run_provider_excel,
                )

                kwargs = {
                    "country_code": "PER",
                    "source_type": self.source_type,
                }

                if self.source_type == "local":
                    kwargs["file_path"] = (
                        self.file_path
                    )

                elif self.source_type == "sharepoint":
                    kwargs["shared_url"] = (
                        self.shared_url
                    )

                else:
                    raise ValueError(
                        "Fuente PER no reconocida."
                    )

                result = run_provider_excel(
                    **kwargs
                )

            else:
                raise ValueError(
                    f"Pais no soportado: {self.country}"
                )

            history.finish(result)
            self.finished.emit(
                result
            )

        except Exception as exc:
            history.fail()
            self.failed.emit(
                f"{type(exc).__name__}: {exc}",
                traceback.format_exc(),
            )
