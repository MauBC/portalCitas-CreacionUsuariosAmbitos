from __future__ import annotations

import traceback

from PySide6.QtCore import (
    QObject,
    Signal,
    Slot,
)


class Phase2Worker(QObject):
    progress = Signal(str)
    finished = Signal(str, dict)
    failed = Signal(str, str, str)

    def __init__(
        self,
        country: str,
        mode: str,
        run_folder: str,
        portal_result: str,
        shared_url: str | None = None,
    ):
        super().__init__()

        self.country = str(
            country or ""
        ).strip().upper()

        self.mode = str(
            mode or ""
        ).strip().lower()

        self.run_folder = str(
            run_folder or ""
        ).strip()

        self.portal_result = str(
            portal_result or ""
        ).strip()

        self.shared_url = str(
            shared_url or ""
        ).strip()

    @Slot()
    def run(self):
        try:
            if self.mode not in {
                "preview",
                "local_copy",
                "verify_remote",
                "apply",
            }:
                raise ValueError(
                    f"Modo Fase 2 invalido: {self.mode}"
                )

            if self.country == "PER":
                result = self._run_per()

            elif self.country == "SLV":
                result = self._run_slv()

            else:
                raise ValueError(
                    f"Pais no soportado: {self.country}"
                )

            self.finished.emit(
                self.mode,
                result,
            )

        except Exception as exc:
            self.failed.emit(
                self.mode,
                f"{type(exc).__name__}: {exc}",
                traceback.format_exc(),
            )

    def _run_per(self):
        if not self.shared_url:
            raise ValueError(
                "PER requiere la URL del Excel "
                "de proveedores en SharePoint."
            )

        if self.mode == "preview":
            self.progress.emit(
                "Analizando resultado del Portal "
                "y verificando Excel remoto..."
            )

            from app.provider_phase2_pipeline import (
                run_provider_phase2_preview,
            )

            return run_provider_phase2_preview(
                run_folder=self.run_folder,
                portal_result_excel=self.portal_result,
                shared_url=self.shared_url,
            )

        if self.mode == "verify_remote":
            self.progress.emit(
                "Verificando el Excel reemplazado "
                "en SharePoint..."
            )

            from app.provider_phase2_pipeline import (
                run_provider_phase2_verify_replacement,
            )

            return (
                run_provider_phase2_verify_replacement(
                    run_folder=
                        self.run_folder,
                    portal_result_excel=
                        self.portal_result,
                    shared_url=
                        self.shared_url,
                )
            )

        if self.mode == "local_copy":
            self.progress.emit(
                "Descargando Excel actual y "
                "generando copia local..."
            )

            from app.provider_phase2_apply_pipeline import (
                run_provider_phase2_local_copy,
            )

            return run_provider_phase2_local_copy(
                run_folder=self.run_folder,
                portal_result_excel=self.portal_result,
                shared_url=self.shared_url,
            )

        self.progress.emit(
            "Aplicando estados creado al Excel remoto..."
        )

        from app.provider_phase2_apply_pipeline import (
            run_provider_phase2_apply,
        )

        return run_provider_phase2_apply(
            run_folder=self.run_folder,
            portal_result_excel=self.portal_result,
            shared_url=self.shared_url,
        )

    def _run_slv(self):
        if self.mode == "verify_remote":
            raise ValueError(
                "La verificacion de reemplazo manual "
                "solo corresponde a Peru."
            )

        if self.mode == "local_copy":
            raise ValueError(
                "Copia local solo esta disponible "
                "para PER."
            )

        from app.phase2_pipeline import (
            run_phase2,
        )

        if self.mode == "preview":
            self.progress.emit(
                "Calculando estados CREADO "
                "sin modificar SharePoint..."
            )

            dry_run = True

        else:
            self.progress.emit(
                "Actualizando CREADO en SharePoint..."
            )

            dry_run = False

        return run_phase2(
            run_folder=self.run_folder,
            portal_error_excel=self.portal_result,
            dry_run=dry_run,
        )
