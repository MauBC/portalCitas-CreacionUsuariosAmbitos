from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QSettings,
    QThread,
    Signal,
)
from PySide6.QtWidgets import QFileDialog
from app.ui.views.users_view import UsersView

from app.services.error_report_service import build_error_details, redact_secrets

from app.ui.file_actions import open_local_path
from app.ui.error_guidance import error_guidance
from app.ui.result_models import Phase1Summary
from app.ui.widgets.field_feedback import set_input_state

from app.ui.dialogs.app_dialog import (
    AppDialog,
)

from app.ui.workers.phase1_worker import (
    Phase1Worker,
)


class UsersPage(UsersView):
    phase1_completed = Signal(str, dict)
    navigate_requested = Signal(int)

    busy_changed = Signal(bool)

    def __init__(self):
        super().__init__()

        self.country = "PER"
        self.thread = None
        self.worker = None
        self.last_result = None

        self.settings = QSettings(
            "Ransa",
            "PortalCitasAutomatizacion",
        )

        saved_url = self.settings.value(
            "phase1/per_shared_url",
            "",
            type=str,
        )
        self.per_url.setText(
            saved_url
        )
        self._connect_view_signals()
        self.set_country("PER")

    def _connect_view_signals(self):
        self.per_source_combo.currentIndexChanged.connect(
            self._update_per_source
        )
        self.per_url.textChanged.connect(
            self._clear_per_source_validation
        )
        self.per_file.textChanged.connect(
            self._clear_per_source_validation
        )
        self.browse_button.clicked.connect(
            self._browse_per_file
        )
        self.run_button.clicked.connect(
            self._start_phase1
        )
        self.open_folder_button.clicked.connect(
            self._open_run_folder
        )
        self.open_template_button.clicked.connect(
            self._open_template
        )
        self.open_valid_button.clicked.connect(
            self._open_valid
        )
        self.open_error_button.clicked.connect(
            self._open_errors
        )
        self.continue_phase2_button.clicked.connect(
            lambda:
            self.navigate_requested.emit(2)
        )


    def set_country(
        self,
        country: str,
    ):
        self.country = str(
            country or "PER"
        ).upper()

        if hasattr(
            self,
            "per_source_error",
        ):
            self._clear_per_source_validation()

        self.result_card.hide()
        self.last_result = None

        if hasattr(
            self,
            "continue_phase2_button",
        ):
            self.continue_phase2_button.setEnabled(
                False
            )

        if self.country == "SLV":
            self.source_stack.setCurrentIndex(
                0
            )

            self.description.setText(
                "Valida los registros de El Salvador "
                "desde la lista SharePoint y genera "
                "la plantilla oficial de usuarios."
            )

            self.run_button.setText(
                "Procesar usuarios · El Salvador"
            )

        else:
            self.source_stack.setCurrentIndex(
                1
            )

            self.description.setText(
                "Valida los registros de Perú "
                "desde el Excel de proveedores y "
                "genera la plantilla oficial de usuarios."
            )

            self.run_button.setText(
                "Procesar usuarios · Per\u00fa"
            )

        self.status_label.setText(
            "Listo para ejecutar."
        )

    def _update_per_source(self):
        self._clear_per_source_validation()

        source = (
            self.per_source_combo
            .currentData()
        )

        self.per_input_stack.setCurrentIndex(
            0
            if source == "sharepoint"
            else 1
        )

    def _set_per_source_error(
        self,
        widget,
        message: str,
    ):
        for current in [
            self.per_url,
            self.per_file,
        ]:
            set_input_state(current, invalid=current is widget)

        self.per_source_error.setText(
            message
        )
        self.per_source_error.show()

    def _set_per_source_valid(
        self,
        widget,
    ):
        for current in [
            self.per_url,
            self.per_file,
        ]:
            set_input_state(current, valid=current is widget)

        self.per_source_error.clear()
        self.per_source_error.hide()

    def _clear_per_source_validation(self):
        if not hasattr(
            self,
            "per_source_error",
        ):
            return

        for current in [
            self.per_url,
            self.per_file,
        ]:
            set_input_state(current)

        self.per_source_error.clear()
        self.per_source_error.hide()

    def _browse_per_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Excel de proveedores",
            "",
            "Archivos Excel (*.xlsx *.xlsm)",
        )

        if path:
            self.per_file.setText(path)

    def _start_phase1(self):
        if self.thread is not None:
            return

        source_type = None
        file_path = None
        shared_url = None

        if self.country == "PER":
            self._clear_per_source_validation()

            source_type = (
                self.per_source_combo
                .currentData()
            )

            if source_type == "sharepoint":
                shared_url = (
                    self.per_url.text().strip()
                )

                if not shared_url:
                    self._set_per_source_error(
                        self.per_url,
                        (
                            "Ingresa el enlace de "
                            "SharePoint del Excel "
                            "de proveedores."
                        ),
                    )

                    self.status_label.setText(
                        "Revisa el campo marcado "
                        "antes de continuar."
                    )

                    return

                if not (
                    shared_url.startswith(
                        "https://"
                    )
                    or shared_url.startswith(
                        "http://"
                    )
                ):
                    self._set_per_source_error(
                        self.per_url,
                        (
                            "El enlace debe comenzar "
                            "con https://"
                        ),
                    )

                    self.status_label.setText(
                        "El enlace de SharePoint "
                        "no es valido."
                    )

                    return

                self._set_per_source_valid(
                    self.per_url
                )

                self.settings.setValue(
                    "phase1/per_shared_url",
                    shared_url,
                )

            else:
                file_path = (
                    self.per_file.text().strip()
                )

                if not file_path:
                    self._set_per_source_error(
                        self.per_file,
                        (
                            "Selecciona el Excel "
                            "de proveedores."
                        ),
                    )

                    self.status_label.setText(
                        "Revisa el campo marcado "
                        "antes de continuar."
                    )

                    return

                local_file = Path(
                    file_path
                )

                if not local_file.is_file():
                    self._set_per_source_error(
                        self.per_file,
                        (
                            "El archivo seleccionado "
                            "no existe."
                        ),
                    )

                    self.status_label.setText(
                        "El archivo local "
                        "no es valido."
                    )

                    return

                if (
                    local_file.suffix.lower()
                    not in {
                        ".xlsx",
                        ".xlsm",
                    }
                ):
                    self._set_per_source_error(
                        self.per_file,
                        (
                            "Selecciona un archivo "
                            "Excel .xlsx o .xlsm."
                        ),
                    )

                    self.status_label.setText(
                        "El archivo seleccionado "
                        "no es un Excel valido."
                    )

                    return

                self._set_per_source_valid(
                    self.per_file
                )

        self.result_card.hide()
        self.continue_phase2_button.setEnabled(
            False
        )
        self.run_button.setEnabled(False)
        self.progress.show()

        self.status_label.setText(
            "Iniciando procesamiento..."
        )

        self.thread = QThread(self)

        self.worker = Phase1Worker(
            country=self.country,
            source_type=source_type,
            file_path=file_path,
            shared_url=shared_url,
        )

        self.worker.moveToThread(
            self.thread
        )

        self.thread.started.connect(
            self.worker.run
        )

        self.worker.progress.connect(
            self.status_label.setText
        )

        self.worker.finished.connect(
            self._on_finished
        )

        self.worker.failed.connect(
            self._on_failed
        )

        self.worker.finished.connect(
            self.thread.quit
        )

        self.worker.failed.connect(
            self.thread.quit
        )

        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(
            self._cleanup_thread
        )

        self.setEnabled(False)
        self.busy_changed.emit(True)
        self.thread.start()

    def _on_finished(
        self,
        result: dict,
    ):
        self.progress.hide()
        self.run_button.setEnabled(True)

        if not result.get("ok", False):
            message = result.get(
                "message",
                "El proceso no pudo completarse.",
            )

            self.status_label.setText(
                message
            )

            AppDialog.warning(
                self,
                "Proceso no completado",
                message,
            )
            return

        self.last_result = result

        self.phase1_completed.emit(
            self.country,
            dict(result),
        )

        summary = Phase1Summary.from_backend(self.country, result)
        total, valid, errors, users = summary.total, summary.valid, summary.errors, summary.users
        message = summary.message

        self.total_value.setText(
            str(total)
        )
        self.valid_value.setText(
            str(valid)
        )
        self.error_value.setText(
            str(errors)
        )
        self.users_value.setText(
            str(users)
        )

        self.result_message.setText(
            message
        )

        self.result_card.show()

        self.status_label.setText(
            "Proceso completado correctamente."
        )

        self._update_file_buttons()

        run_folder_value = str(
            result.get(
                "run_folder",
                "",
            )
            or ""
        ).strip()

        phase2_available = False

        if run_folder_value:
            manifest = (
                Path(run_folder_value)
                / "usuarios_enviados.xlsx"
            )

            phase2_available = (
                manifest.is_file()
            )

        self.continue_phase2_button.setEnabled(
            phase2_available
        )

        AppDialog.success(
            self,
            "Fase 1 completada",
            (
                "El procesamiento terminó "
                "correctamente.\n\n"
                f"Registros: {total}\n"
                f"Válidos: {valid}\n"
                f"Errores: {errors}\n"
                f"Usuarios: {users}"
            ),
        )

    def _on_failed(
        self,
        error_detail: str,
        full_trace: str,
    ):
        details = build_error_details(
            phase="1",
            country=self.country,
            mode="users",
            error_detail=error_detail,
            full_trace=full_trace,
        )
        error_detail = redact_secrets(error_detail)
        self.progress.hide()
        self.run_button.setEnabled(True)

        self.status_label.setText(
            "Ocurrió un error durante el proceso."
        )

        hint = error_guidance(error_detail, full_trace, mode="users")
        user_message = error_detail
        if hint:
            user_message += f"\n\n{hint}"

        AppDialog.error(
            self,
            "Error en Fase 1",
            user_message,
            details=details,
        )

    def _cleanup_thread(self):
        if self.thread is not None:
            # finished may precede native teardown; join before deleting QThread.
            self.thread.wait()
            self.thread.deleteLater()

        self.worker = None
        self.thread = None
        self.setEnabled(True)
        self.busy_changed.emit(False)

    def _result_path(
        self,
        slv_key: str,
        per_key: str,
    ):
        if not self.last_result:
            return None

        key = (
            slv_key
            if self.country == "SLV"
            else per_key
        )

        value = self.last_result.get(
            key
        )

        if not value:
            return None

        return str(value)

    def _update_file_buttons(self):
        folder = self._result_path(
            "run_folder",
            "run_folder",
        )

        template = self._result_path(
            "path_template",
            "template_path",
        )

        valid = self._result_path(
            "path_validos",
            "valid_path",
        )

        errors = self._result_path(
            "path_errores",
            "error_path",
        )

        self.open_folder_button.setEnabled(
            bool(folder)
        )
        self.open_template_button.setEnabled(
            bool(template)
        )
        self.open_valid_button.setEnabled(
            bool(valid)
        )
        self.open_error_button.setEnabled(
            bool(errors)
        )

    def _open_path(self, value: str | Path | None):
        open_local_path(self, value)

    def _open_run_folder(self):
        self._open_path(
            self._result_path(
                "run_folder",
                "run_folder",
            )
        )

    def _open_template(self):
        self._open_path(
            self._result_path(
                "path_template",
                "template_path",
            )
        )

    def _open_valid(self):
        self._open_path(
            self._result_path(
                "path_validos",
                "valid_path",
            )
        )

    def _open_errors(self):
        self._open_path(
            self._result_path(
                "path_errores",
                "error_path",
            )
        )
