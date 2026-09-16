from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QSettings,
    QThread,
    Signal,
)
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.services.error_report_service import build_error_details, redact_secrets

from app.ui.file_actions import open_local_path
from app.ui.widgets.field_feedback import set_input_state

from app.ui.dialogs.app_dialog import (
    AppDialog,
)

from app.ui.workers.phase1_worker import (
    Phase1Worker,
)


class UsersPage(QWidget):
    phase1_completed = Signal(str, dict)
    navigate_requested = Signal(int)

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

        self._build_ui()
        self.set_country("PER")

    def _build_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        root_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        content = QWidget()
        content.setObjectName(
            "pageContent"
        )

        # Evita que Qt comprima controles
        # cuando la ventana pierde espacio.
        content.setMinimumWidth(
            720
        )

        scroll.setWidget(content)

        root_layout.addWidget(
            scroll
        )

        self.page_scroll = scroll
        self.page_content = content

        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            38,
            34,
            38,
            34,
        )
        layout.setSpacing(10)

        title = QLabel(
            "Fase 1 · Usuarios"
        )
        title.setObjectName("pageTitle")

        self.description = QLabel()
        self.description.setObjectName(
            "pageDescription"
        )
        self.description.setWordWrap(
            True
        )

        layout.addWidget(title)
        layout.addWidget(self.description)
        layout.addSpacing(20)

        self.source_card = self._build_source_card()
        self.source_card.setMinimumHeight(
            300
        )
        layout.addWidget(
            self.source_card
        )

        layout.addSpacing(10)

        self.run_card = self._build_run_card()
        self.run_card.setMinimumHeight(
            150
        )
        layout.addWidget(
            self.run_card
        )

        layout.addSpacing(10)

        self.result_card = self._build_result_card()
        self.result_card.setMinimumHeight(
            225
        )
        self.result_card.hide()

        layout.addWidget(self.result_card)
        layout.addStretch()

    def _build_source_card(self):
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        layout.setSpacing(12)

        title = QLabel("Origen de datos")
        title.setObjectName("cardTitle")

        layout.addWidget(title)

        self.source_stack = QStackedWidget()
        self.source_stack.setMinimumHeight(
            215
        )
        self.source_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        # ------------------------------------------
        # SLV
        # ------------------------------------------

        slv_page = QWidget()
        slv_layout = QVBoxLayout(slv_page)
        slv_layout.setContentsMargins(
            0,
            5,
            0,
            0,
        )

        slv_title = QLabel(
            "Lista SharePoint · El Salvador"
        )
        slv_title.setObjectName(
            "sectionTitle"
        )

        slv_info = QLabel(
            "La lista configurada en .env sera "
            "consultada automaticamente. "
            "Fase 1 no modifica SharePoint."
        )
        slv_info.setObjectName(
            "cardDescription"
        )
        slv_info.setWordWrap(True)

        slv_layout.addWidget(slv_title)
        slv_layout.addWidget(slv_info)

        # ------------------------------------------
        # PER
        # ------------------------------------------

        per_page = QWidget()
        per_layout = QVBoxLayout(per_page)
        per_layout.setContentsMargins(
            0,
            5,
            0,
            0,
        )
        per_layout.setSpacing(10)

        source_label = QLabel(
            "Fuente del Excel de proveedores"
        )
        source_label.setObjectName(
            "sectionTitle"
        )

        self.per_source_combo = QComboBox()
        self.per_source_combo.addItem(
            "SharePoint",
            "sharepoint",
        )
        self.per_source_combo.addItem(
            "Archivo local",
            "local",
        )

        self.per_source_combo.currentIndexChanged.connect(
            self._update_per_source
        )

        self.per_input_stack = (
            QStackedWidget()
        )
        self.per_input_stack.setMinimumHeight(
            75
        )
        self.per_input_stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )

        # URL SharePoint

        sharepoint_widget = QWidget()
        sharepoint_layout = QVBoxLayout(
            sharepoint_widget
        )
        sharepoint_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        url_label = QLabel(
            "Enlace compartido de SharePoint"
        )

        self.per_url = QLineEdit()
        self.per_url.setPlaceholderText(
            "Pega aqu? el enlace del Excel..."
        )
        self.per_url.setClearButtonEnabled(
            True
        )

        saved_url = self.settings.value(
            "phase1/per_shared_url",
            "",
            type=str,
        )

        self.per_url.setText(
            saved_url
        )

        self.per_url.textChanged.connect(
            self._clear_per_source_validation
        )

        sharepoint_layout.addWidget(
            url_label
        )
        sharepoint_layout.addWidget(
            self.per_url
        )

        # Archivo local

        local_widget = QWidget()
        local_layout = QHBoxLayout(
            local_widget
        )
        local_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.per_file = QLineEdit()
        self.per_file.setReadOnly(True)
        self.per_file.setPlaceholderText(
            "Selecciona el Excel de proveedores..."
        )

        self.per_file.textChanged.connect(
            self._clear_per_source_validation
        )

        browse_button = QPushButton(
            "Seleccionar Excel"
        )
        browse_button.setObjectName(
            "secondaryButton"
        )
        browse_button.clicked.connect(
            self._browse_per_file
        )

        local_layout.addWidget(
            self.per_file,
            1,
        )
        local_layout.addWidget(
            browse_button,
        )

        self.per_input_stack.addWidget(
            sharepoint_widget
        )
        self.per_input_stack.addWidget(
            local_widget
        )

        info = QLabel(
            "Solo se leen los datos. "
            "Esta fase no actualiza el campo creado "
            "del Excel remoto."
        )
        info.setObjectName(
            "safeInfo"
        )
        info.setWordWrap(True)

        per_layout.addWidget(
            source_label
        )
        per_layout.addWidget(
            self.per_source_combo
        )
        per_layout.addWidget(
            self.per_input_stack
        )

        self.per_source_error = QLabel()
        self.per_source_error.setObjectName(
            "fieldError"
        )
        self.per_source_error.setWordWrap(
            True
        )
        self.per_source_error.hide()

        per_layout.addWidget(
            self.per_source_error
        )
        per_layout.addWidget(info)

        self.source_stack.addWidget(
            slv_page
        )
        self.source_stack.addWidget(
            per_page
        )

        layout.addWidget(
            self.source_stack
        )

        return card

    def _build_run_card(self):
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        layout.setSpacing(12)

        title = QLabel(
            "Procesamiento"
        )
        title.setObjectName(
            "cardTitle"
        )

        self.status_label = QLabel(
            "Listo para ejecutar."
        )
        self.status_label.setObjectName(
            "cardDescription"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()

        self.run_button = QPushButton(
            "Ejecutar automatizacion"
        )
        self.run_button.setObjectName(
            "primaryButton"
        )

        self.run_button.clicked.connect(
            self._start_phase1
        )

        layout.addWidget(title)
        layout.addWidget(
            self.status_label
        )
        layout.addWidget(
            self.progress
        )
        layout.addWidget(
            self.run_button
        )

        return card

    def _build_result_card(self):
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        layout.setSpacing(14)

        title = QLabel(
            "Resultado"
        )
        title.setObjectName("cardTitle")

        layout.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(30)
        grid.setVerticalSpacing(10)

        self.total_value = self._metric()
        self.valid_value = self._metric()
        self.error_value = self._metric()
        self.users_value = self._metric()

        grid.addWidget(
            QLabel("Registros"),
            0,
            0,
        )
        grid.addWidget(
            self.total_value,
            1,
            0,
        )

        grid.addWidget(
            QLabel("V?lidos"),
            0,
            1,
        )
        grid.addWidget(
            self.valid_value,
            1,
            1,
        )

        grid.addWidget(
            QLabel("Errores"),
            0,
            2,
        )
        grid.addWidget(
            self.error_value,
            1,
            2,
        )

        grid.addWidget(
            QLabel("Usuarios"),
            0,
            3,
        )
        grid.addWidget(
            self.users_value,
            1,
            3,
        )

        layout.addLayout(grid)

        self.result_message = QLabel()
        self.result_message.setObjectName(
            "cardDescription"
        )
        self.result_message.setWordWrap(
            True
        )

        layout.addWidget(
            self.result_message
        )

        buttons = QHBoxLayout()

        self.open_folder_button = (
            QPushButton("Abrir carpeta")
        )
        self.open_folder_button.setObjectName(
            "secondaryButton"
        )

        self.open_template_button = (
            QPushButton("Abrir plantilla")
        )
        self.open_template_button.setObjectName(
            "secondaryButton"
        )

        self.open_valid_button = (
            QPushButton("Abrir v?lidos")
        )
        self.open_valid_button.setObjectName(
            "secondaryButton"
        )

        self.open_error_button = (
            QPushButton("Abrir errores")
        )
        self.open_error_button.setObjectName(
            "secondaryButton"
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

        buttons.addWidget(
            self.open_folder_button
        )
        buttons.addWidget(
            self.open_template_button
        )
        buttons.addWidget(
            self.open_valid_button
        )
        buttons.addWidget(
            self.open_error_button
        )

        self.continue_phase2_button = QPushButton(
            "Continuar a Fase 2 \u2192"
        )
        self.continue_phase2_button.setObjectName(
            "primaryButton"
        )
        self.continue_phase2_button.setEnabled(
            False
        )
        self.continue_phase2_button.clicked.connect(
            lambda:
            self.navigate_requested.emit(2)
        )

        buttons.addWidget(
            self.continue_phase2_button
        )

        buttons.addStretch()

        layout.addLayout(buttons)

        return card

    def _metric(self):
        label = QLabel("0")
        label.setObjectName(
            "metricValue"
        )
        return label

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
                "Valida los registros de Per? "
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

        self.thread.finished.connect(
            self._cleanup_thread
        )

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

        if self.country == "SLV":
            total = int(
                result.get("total", 0)
            )
            valid = int(
                result.get("validos", 0)
            )
            errors = int(
                result.get("errores", 0)
            )

            users = valid

            message = (
                "La plantilla de usuarios de "
                "El Salvador fue generada."
            )

        else:
            total = int(
                result.get("total", 0)
            )
            valid = int(
                result.get(
                    "valid_relations",
                    0,
                )
            )
            errors = int(
                result.get("errors", 0)
            )
            users = int(
                result.get(
                    "unique_users",
                    0,
                )
            )

            already_created = int(
                result.get(
                    "already_created",
                    0,
                )
            )

            previous_errors = int(
                result.get(
                    "previous_errors",
                    0,
                )
            )

            message = (
                f"Ya creados omitidos: "
                f"{already_created} · "
                f"Errores previos: "
                f"{previous_errors}"
            )

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
                "El procesamiento termin? "
                "correctamente.\n\n"
                f"Registros: {total}\n"
                f"V?lidos: {valid}\n"
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
            "Ocurri? un error durante el proceso."
        )

        AppDialog.error(
            self,
            "Error en Fase 1",
            (
                f"{error_detail}\n\n"
                "Puedes consultar el detalle "
                "t?cnico si lo necesitas."
            ),
            details=details,
        )

    def _cleanup_thread(self):
        if self.worker is not None:
            self.worker.deleteLater()

        if self.thread is not None:
            self.thread.deleteLater()

        self.worker = None
        self.thread = None

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
