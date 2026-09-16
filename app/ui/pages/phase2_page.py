from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QSettings,
    QThread,
    Signal,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services.error_report_service import build_error_details, redact_secrets

from app.ui.file_actions import open_local_path
from app.ui.widgets.field_feedback import clear_field_error, set_field_error

from app.ui.dialogs.app_dialog import (
    AppDialog,
)

from app.ui.workers.phase2_worker import (
    Phase2Worker,
)


class Phase2Page(QWidget):
    navigate_requested = Signal(int)
    workflow_status_changed = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.country = "PER"

        self.thread = None
        self.worker = None
        self.active_mode = None

        self.last_preview = None
        self.last_apply = None
        self.last_local_copy = None
        self.remote_replacement_verified = False
        self.preview_signature = None

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
            "Fase 2 · Resultado del Portal"
        )
        title.setObjectName("pageTitle")

        self.description = QLabel()
        self.description.setObjectName(
            "pageDescription"
        )
        self.description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.description)
        layout.addSpacing(18)

        input_card = QFrame()
        input_card.setObjectName("card")

        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        input_layout.setSpacing(12)

        card_title = QLabel(
            "Archivos de la ejecución"
        )
        card_title.setObjectName("cardTitle")

        input_layout.addWidget(card_title)

        # Carpeta Fase 1

        run_label = QLabel(
            "Carpeta generada por Fase 1"
        )

        run_row = QHBoxLayout()

        self.run_folder = QLineEdit()
        self.run_folder.setPlaceholderText(
            "Selecciona la carpeta de ejecución..."
        )

        run_button = QPushButton(
            "Seleccionar carpeta"
        )
        run_button.setObjectName(
            "secondaryButton"
        )
        run_button.clicked.connect(
            self._browse_run_folder
        )

        run_row.addWidget(
            self.run_folder,
            1,
        )
        run_row.addWidget(run_button)

        input_layout.addWidget(run_label)
        input_layout.addLayout(run_row)

        self.run_folder_error = QLabel()
        self.run_folder_error.setObjectName(
            "fieldError"
        )
        self.run_folder_error.setWordWrap(
            True
        )
        self.run_folder_error.hide()

        input_layout.addWidget(
            self.run_folder_error
        )

        # Resultado Portal

        portal_label = QLabel(
            "Excel devuelto por el Portal"
        )

        portal_row = QHBoxLayout()

        self.portal_result = QLineEdit()
        self.portal_result.setPlaceholderText(
            "Selecciona el resultado del Portal..."
        )

        portal_button = QPushButton(
            "Seleccionar Excel"
        )
        portal_button.setObjectName(
            "secondaryButton"
        )
        portal_button.clicked.connect(
            self._browse_portal_result
        )

        portal_row.addWidget(
            self.portal_result,
            1,
        )
        portal_row.addWidget(portal_button)

        input_layout.addWidget(portal_label)
        input_layout.addLayout(portal_row)

        self.portal_result_error = QLabel()
        self.portal_result_error.setObjectName(
            "fieldError"
        )
        self.portal_result_error.setWordWrap(
            True
        )
        self.portal_result_error.hide()

        input_layout.addWidget(
            self.portal_result_error
        )

        # URL PER

        self.url_label = QLabel(
            "Excel de proveedores en SharePoint"
        )

        self.shared_url = QLineEdit()
        self.shared_url.setPlaceholderText(
            "Enlace compartido del Excel PER..."
        )
        self.shared_url.setClearButtonEnabled(
            True
        )

        saved_url = self.settings.value(
            "phase1/per_shared_url",
            "",
            type=str,
        )

        self.shared_url.setText(
            saved_url
        )

        input_layout.addWidget(
            self.url_label
        )
        input_layout.addWidget(
            self.shared_url
        )

        self.shared_url_error = QLabel()
        self.shared_url_error.setObjectName(
            "fieldError"
        )
        self.shared_url_error.setWordWrap(
            True
        )
        self.shared_url_error.hide()

        input_layout.addWidget(
            self.shared_url_error
        )

        self.safety_info = QLabel()
        self.safety_info.setObjectName(
            "safeInfo"
        )
        self.safety_info.setWordWrap(True)

        input_layout.addWidget(
            self.safety_info
        )

        layout.addWidget(input_card)

        # Acciones

        action_card = QFrame()
        action_card.setObjectName("card")

        action_layout = QVBoxLayout(
            action_card
        )
        action_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        action_layout.setSpacing(12)

        action_title = QLabel(
            "Validación y aplicación"
        )
        action_title.setObjectName(
            "cardTitle"
        )

        self.status_label = QLabel(
            "Primero ejecuta el preview."
        )
        self.status_label.setObjectName(
            "cardDescription"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.hide()

        action_buttons = QHBoxLayout()

        self.preview_button = QPushButton(
            "Generar preview"
        )
        self.preview_button.setObjectName(
            "primaryButton"
        )
        self.preview_button.clicked.connect(
            self._start_preview
        )

        self.local_copy_button = QPushButton(
            "Generar copia local actualizada"
        )
        self.local_copy_button.setObjectName(
            "primaryButton"
        )
        self.local_copy_button.setEnabled(
            False
        )
        self.local_copy_button.clicked.connect(
            self._generate_local_copy
        )

        self.verify_remote_button = QPushButton(
            "Verificar reemplazo"
        )
        self.verify_remote_button.setObjectName(
            "secondaryButton"
        )
        self.verify_remote_button.setEnabled(
            False
        )
        self.verify_remote_button.clicked.connect(
            self._verify_remote_replacement
        )

        self.apply_button = QPushButton(
            "Aplicar cambios"
        )
        self.apply_button.setObjectName(
            "dangerButton"
        )
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(
            self._confirm_apply
        )

        action_buttons.addWidget(
            self.preview_button
        )
        action_buttons.addWidget(
            self.local_copy_button
        )
        action_buttons.addWidget(
            self.verify_remote_button
        )

        self.continue_ambitos_button = QPushButton(
            "Continuar a \u00c1mbitos \u2192"
        )
        self.continue_ambitos_button.setObjectName(
            "primaryButton"
        )
        self.continue_ambitos_button.setEnabled(
            False
        )
        self.continue_ambitos_button.clicked.connect(
            lambda:
            self.navigate_requested.emit(3)
        )

        action_buttons.addWidget(
            self.continue_ambitos_button
        )

        action_buttons.addStretch()

        self.advanced_toggle_button = QPushButton(
            "Opciones avanzadas \u25be"
        )
        self.advanced_toggle_button.setObjectName(
            "advancedToggle"
        )
        self.advanced_toggle_button.setCheckable(
            True
        )
        self.advanced_toggle_button.setChecked(
            False
        )
        self.advanced_toggle_button.clicked.connect(
            self._toggle_advanced_options
        )

        self.advanced_panel = QFrame()
        self.advanced_panel.setObjectName(
            "advancedPanel"
        )

        advanced_layout = QVBoxLayout(
            self.advanced_panel
        )
        advanced_layout.setContentsMargins(
            16,
            14,
            16,
            14,
        )
        advanced_layout.setSpacing(
            10
        )

        self.advanced_description = QLabel(
            "Esta opcion intenta modificar directamente "
            "el Excel remoto. Si otra persona lo tiene "
            "abierto, SharePoint puede bloquear la "
            "escritura. Para Peru se recomienda usar "
            "la copia local."
        )
        self.advanced_description.setObjectName(
            "advancedDescription"
        )
        self.advanced_description.setWordWrap(
            True
        )

        advanced_layout.addWidget(
            self.advanced_description
        )

        advanced_button_row = QHBoxLayout()

        advanced_button_row.addWidget(
            self.apply_button
        )
        advanced_button_row.addStretch()

        advanced_layout.addLayout(
            advanced_button_row
        )

        self.advanced_panel.hide()

        action_layout.addWidget(action_title)
        action_layout.addWidget(
            self.status_label
        )
        action_layout.addWidget(
            self.progress
        )
        action_layout.addLayout(
            action_buttons
        )

        action_layout.addWidget(
            self.advanced_toggle_button
        )

        action_layout.addWidget(
            self.advanced_panel
        )

        self.apply_gate_label = QLabel(
            "PASO 1 - Ejecuta el preview para calcular "
            "y validar los estados de Fase 2."
        )
        self.apply_gate_label.setObjectName(
            "cardDescription"
        )
        self.apply_gate_label.setWordWrap(True)

        action_layout.addWidget(
            self.apply_gate_label
        )

        layout.addWidget(action_card)

        # Resultado

        self.result_card = QFrame()
        self.result_card.setObjectName(
            "card"
        )

        result_layout = QVBoxLayout(
            self.result_card
        )
        result_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )
        result_layout.setSpacing(12)

        result_title = QLabel(
            "Resultado del preview"
        )
        result_title.setObjectName(
            "cardTitle"
        )

        result_layout.addWidget(
            result_title
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(28)
        grid.setVerticalSpacing(7)

        self.metric_1_title = QLabel()
        self.metric_2_title = QLabel()
        self.metric_3_title = QLabel()
        self.metric_4_title = QLabel()

        self.metric_1 = self._metric()
        self.metric_2 = self._metric()
        self.metric_3 = self._metric()
        self.metric_4 = self._metric()

        titles = [
            self.metric_1_title,
            self.metric_2_title,
            self.metric_3_title,
            self.metric_4_title,
        ]

        values = [
            self.metric_1,
            self.metric_2,
            self.metric_3,
            self.metric_4,
        ]

        for column in range(4):
            grid.addWidget(
                titles[column],
                0,
                column,
            )

            grid.addWidget(
                values[column],
                1,
                column,
            )

        result_layout.addLayout(grid)

        self.result_detail = QLabel()
        self.result_detail.setObjectName(
            "cardDescription"
        )
        self.result_detail.setWordWrap(True)

        result_layout.addWidget(
            self.result_detail
        )

        file_buttons = QHBoxLayout()

        self.open_result_button = QPushButton(
            "Abrir resultado"
        )
        self.open_result_button.setObjectName(
            "secondaryButton"
        )

        self.open_evidence_button = QPushButton(
            "Abrir evidencia"
        )
        self.open_evidence_button.setObjectName(
            "secondaryButton"
        )

        self.open_plan_button = QPushButton(
            "Abrir plan"
        )
        self.open_plan_button.setObjectName(
            "secondaryButton"
        )

        self.open_result_button.clicked.connect(
            self._open_result
        )
        self.open_evidence_button.clicked.connect(
            self._open_evidence
        )
        self.open_plan_button.clicked.connect(
            self._open_plan
        )

        file_buttons.addWidget(
            self.open_result_button
        )
        file_buttons.addWidget(
            self.open_evidence_button
        )
        file_buttons.addWidget(
            self.open_plan_button
        )
        file_buttons.addStretch()

        result_layout.addLayout(
            file_buttons
        )

        self.result_card.hide()

        layout.addWidget(
            self.result_card
        )
        layout.addStretch()

        # Si cambian inputs, preview deja de ser válido.

        self.run_folder.textChanged.connect(
            self._on_run_folder_changed
        )

        self.portal_result.textChanged.connect(
            self._on_portal_result_changed
        )

        self.shared_url.textChanged.connect(
            self._on_shared_url_changed
        )

    def _toggle_advanced_options(
        self,
        checked: bool,
    ):
        if self.country != "PER":
            self.advanced_panel.show()
            return

        self.advanced_panel.setVisible(
            bool(checked)
        )

        self.advanced_toggle_button.setText(
            (
                "Opciones avanzadas \u25b4"
                if checked
                else
                "Opciones avanzadas \u25be"
            )
        )

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
        ).strip().upper()

        self._invalidate_preview()

        if self.country == "PER":
            self.description.setText(
                "Interpreta el resultado de cuentas "
                "del Portal y prepara los cambios de "
                "la columna creado del Excel PER."
            )

            self.url_label.show()
            self.shared_url.show()

            self.safety_info.setText(
                "El preview NO modifica SharePoint. "
                "La escritura real solo se realiza "
                "después de confirmar Aplicar cambios."
            )

        else:
            self.description.setText(
                "Interpreta el resultado de cuentas "
                "del Portal y prepara la actualización "
                "del campo CREADO en SharePoint SLV."
            )

            self.url_label.hide()
            self.shared_url.hide()

            self.safety_info.setText(
                "El preview usa dry_run=True y NO "
                "modifica SharePoint. La actualización "
                "real requiere confirmación posterior."
            )

        self.local_copy_button.setVisible(
            self.country == "PER"
        )

        self.verify_remote_button.setVisible(
            self.country == "PER"
        )

        if self.country == "PER":
            self.local_copy_button.setObjectName(
                "primaryButton"
            )

            self.apply_button.setText(
                "Aplicar directamente en SharePoint"
            )

            self.advanced_toggle_button.show()
            self.advanced_toggle_button.setChecked(
                False
            )
            self.advanced_toggle_button.setText(
                "Opciones avanzadas \u25be"
            )
            self.advanced_panel.hide()

            self.advanced_description.setText(
                "Esta opcion intenta reemplazar "
                "directamente el Excel remoto. "
                "Como el archivo es compartido, "
                "SharePoint puede bloquearlo si "
                "alguien lo esta utilizando. "
                "La copia local es el flujo recomendado."
            )

        else:
            self.local_copy_button.setObjectName(
                "secondaryButton"
            )

            self.apply_button.setText(
                "Aplicar cambios en SharePoint"
            )

            self.advanced_toggle_button.hide()
            self.advanced_panel.show()

            self.advanced_description.setText(
                "La actualizacion de CREADO se realiza "
                "directamente en SharePoint."
            )

        for button in [
            self.local_copy_button,
            self.apply_button,
        ]:
            button.style().unpolish(
                button
            )
            button.style().polish(
                button
            )

        self.shared_url_error.setVisible(
            self.country == "PER"
            and bool(
                self.shared_url_error.text()
            )
        )

    def set_phase1_result(
        self,
        country: str,
        result: dict,
    ):
        country = str(
            country or ""
        ).strip().upper()

        if country != self.country:
            return

        folder = str(
            result.get(
                "run_folder",
                "",
            )
            or ""
        ).strip()

        if not folder:
            return

        run_path = Path(folder)

        manifest = (
            run_path
            / "usuarios_enviados.xlsx"
        )

        if manifest.exists():
            self.run_folder.setText(
                folder
            )

            self.status_label.setText(
                "Fase 1 detectada. "
                "Selecciona el resultado del Portal "
                "y genera el preview."
            )

            self.safety_info.setText(
                (
                    "Ejecuci?n de Fase 1 v?lida. "
                    "Se encontr? usuarios_enviados.xlsx. "
                )
                + (
                    "El preview NO modifica SharePoint."
                    if self.country == "PER"
                    else
                    "El preview usa dry_run=True "
                    "y NO modifica SharePoint."
                )
            )

        else:
            self.run_folder.clear()

            self.status_label.setText(
                "La ?ltima ejecuci?n de Fase 1 "
                "no gener? usuarios para enviar."
            )

            self.safety_info.setText(
                "No se encontr? usuarios_enviados.xlsx. "
                "Esto normalmente significa que no habia "
                "cuentas nuevas pendientes y, por tanto, "
                "Fase 2 no corresponde a esa ejecucion."
            )

    def _on_portal_result_changed(self):
        self._invalidate_preview()

        if hasattr(
            self,
            "portal_result_error",
        ):
            self._clear_field_error(
                self.portal_result,
                self.portal_result_error,
            )

    def _on_shared_url_changed(self):
        self._invalidate_preview()

        if hasattr(
            self,
            "shared_url_error",
        ):
            self._clear_field_error(
                self.shared_url,
                self.shared_url_error,
            )

    def _on_run_folder_changed(self):
        self._invalidate_preview()

        if hasattr(
            self,
            "run_folder_error",
        ):
            self._clear_field_error(
                self.run_folder,
                self.run_folder_error,
            )

        value = self.run_folder.text().strip()

        if not value:
            self.status_label.setText(
                "Selecciona la carpeta generada "
                "por Fase 1."
            )
            return

        folder = Path(value)

        if not folder.is_dir():
            self.status_label.setText(
                "La ruta de Fase 1 no existe."
            )
            return

        manifest = (
            folder
            / "usuarios_enviados.xlsx"
        )

        if manifest.exists():
            self.status_label.setText(
                "Carpeta de Fase 1 v?lida. "
                "Selecciona el resultado del Portal "
                "y genera el preview."
            )

            if self.country == "PER":
                self.safety_info.setText(
                    "Se encontr? usuarios_enviados.xlsx. "
                    "El preview NO modifica SharePoint. "
                    "La escritura real requiere "
                    "confirmaci?n posterior."
                )
            else:
                self.safety_info.setText(
                    "Se encontr? usuarios_enviados.xlsx. "
                    "El preview usa dry_run=True y "
                    "NO modifica SharePoint."
                )

        else:
            self.status_label.setText(
                "Esta ejecuci?n no tiene "
                "usuarios_enviados.xlsx."
            )

            self.safety_info.setText(
                "La carpeta seleccionada no contiene "
                "usuarios_enviados.xlsx. Normalmente "
                "esto significa que esa ejecucion "
                "no gener? cuentas para Fase 2."
            )

    def _browse_run_folder(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de Fase 1",
            self.run_folder.text().strip(),
        )

        if path:
            self.run_folder.setText(path)

    def _browse_portal_result(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar resultado del Portal",
            "",
            "Archivos Excel (*.xlsx *.xlsm)",
        )

        if path:
            self.portal_result.setText(path)

    def _current_signature(self):
        return (
            self.country,
            self.run_folder.text().strip(),
            self.portal_result.text().strip(),
            (
                self.shared_url.text().strip()
                if self.country == "PER"
                else ""
            ),
        )

    def _invalidate_preview(self):
        self.last_preview = None
        self.preview_signature = None

        self.remote_replacement_verified = False

        if hasattr(
            self,
            "continue_ambitos_button",
        ):
            self.continue_ambitos_button.setEnabled(
                False
            )

        if hasattr(
            self,
            "apply_button",
        ):
            self.apply_button.setEnabled(
                False
            )

        if hasattr(
            self,
            "local_copy_button",
        ):
            self.local_copy_button.setEnabled(
                False
            )


        if hasattr(
            self,
            "verify_remote_button",
        ):
            self.verify_remote_button.setEnabled(
                False
            )
            self.verify_remote_button.setText(
                "Verificar reemplazo"
            )

        if hasattr(
            self,
            "apply_gate_label",
        ):
            self.apply_gate_label.setText(
                "Ejecuta el preview para validar "
                "si existen cambios seguros."
            )

    def _set_field_error(self, widget, label, message: str):
        set_field_error(widget, label, message)

    def _clear_field_error(self, widget, label, *, mark_valid: bool = False):
        clear_field_error(widget, label, mark_valid=mark_valid)

    def _clear_inline_errors(self):
        for widget, label in [
            (
                self.run_folder,
                self.run_folder_error,
            ),
            (
                self.portal_result,
                self.portal_result_error,
            ),
            (
                self.shared_url,
                self.shared_url_error,
            ),
        ]:
            self._clear_field_error(
                widget,
                label,
            )

    def _validate_inputs(self):
        self._clear_inline_errors()

        valid = True

        folder_value = (
            self.run_folder.text().strip()
        )

        portal_value = (
            self.portal_result.text().strip()
        )

        folder = Path(
            folder_value
        )

        portal = Path(
            portal_value
        )

        # --------------------------------------------
        # Carpeta Fase 1
        # --------------------------------------------

        if not folder_value:
            self._set_field_error(
                self.run_folder,
                self.run_folder_error,
                (
                    "Selecciona la carpeta "
                    "generada por Fase 1."
                ),
            )

            valid = False

        elif not folder.is_dir():
            self._set_field_error(
                self.run_folder,
                self.run_folder_error,
                (
                    "La carpeta seleccionada "
                    "no existe."
                ),
            )

            valid = False

        else:
            manifest = (
                folder
                / "usuarios_enviados.xlsx"
            )

            if not manifest.is_file():
                self._set_field_error(
                    self.run_folder,
                    self.run_folder_error,
                    (
                        "Esta ejecuci?n no contiene "
                        "usuarios_enviados.xlsx. "
                        "Normalmente significa que "
                        "Fase 2 no corresponde a "
                        "esta ejecuci?n."
                    ),
                )

                valid = False

            else:
                self._clear_field_error(
                    self.run_folder,
                    self.run_folder_error,
                    mark_valid=True,
                )

        # --------------------------------------------
        # Resultado Portal
        # --------------------------------------------

        if not portal_value:
            self._set_field_error(
                self.portal_result,
                self.portal_result_error,
                (
                    "Selecciona el Excel devuelto "
                    "por el Portal."
                ),
            )

            valid = False

        elif not portal.is_file():
            self._set_field_error(
                self.portal_result,
                self.portal_result_error,
                (
                    "El archivo seleccionado "
                    "no existe."
                ),
            )

            valid = False

        elif (
            portal.suffix.lower()
            not in {
                ".xlsx",
                ".xlsm",
            }
        ):
            self._set_field_error(
                self.portal_result,
                self.portal_result_error,
                (
                    "Selecciona un archivo Excel "
                    ".xlsx o .xlsm."
                ),
            )

            valid = False

        else:
            self._clear_field_error(
                self.portal_result,
                self.portal_result_error,
                mark_valid=True,
            )

        # --------------------------------------------
        # URL PER
        # --------------------------------------------

        if self.country == "PER":
            shared_url = (
                self.shared_url.text().strip()
            )

            if not shared_url:
                self._set_field_error(
                    self.shared_url,
                    self.shared_url_error,
                    (
                        "Ingresa el enlace del Excel "
                        "de proveedores en SharePoint."
                    ),
                )

                valid = False

            elif not (
                shared_url.startswith(
                    "https://"
                )
                or shared_url.startswith(
                    "http://"
                )
            ):
                self._set_field_error(
                    self.shared_url,
                    self.shared_url_error,
                    (
                        "El enlace debe comenzar "
                        "con https://"
                    ),
                )

                valid = False

            else:
                self._clear_field_error(
                    self.shared_url,
                    self.shared_url_error,
                    mark_valid=True,
                )

        else:
            self._clear_field_error(
                self.shared_url,
                self.shared_url_error,
            )

        # --------------------------------------------
        # Resultado general
        # --------------------------------------------

        if not valid:
            self.status_label.setText(
                "Revisa los campos marcados "
                "antes de continuar."
            )

            self.apply_gate_label.setText(
                "DATOS INCOMPLETOS - "
                "Corrige los campos indicados "
                "y vuelve a ejecutar el preview."
            )

            return False

        return True


    def _start_preview(self):
        if not self._validate_inputs():
            return

        if self.country == "PER":
            self.settings.setValue(
                "phase1/per_shared_url",
                self.shared_url.text().strip(),
            )

        self._start_worker(
            "preview"
        )

    def _generate_local_copy(self):
        if (
            self.last_preview is None
            or self.preview_signature
            != self._current_signature()
        ):
            AppDialog.warning(
                self,
                "Preview requerido",
                (
                    "Los datos cambiaron. Ejecuta "
                    "nuevamente el preview antes "
                    "de generar la copia local."
                ),
            )
            return

        self._start_worker(
            "local_copy"
        )

    def _verify_remote_replacement(self):
        if self.country != "PER":
            return

        if not self._validate_inputs():
            return

        if (
            self.last_local_copy is None
            and not self.remote_replacement_verified
        ):
            confirmed = AppDialog.confirm(
                self,
                "Verificar Excel remoto",
                (
                    "No hay una copia local generada "
                    "en esta sesion.\n\n"
                    "Puedes continuar si ya reemplazaste "
                    "manualmente el Excel de SharePoint."
                ),
                accept_text="Verificar",
                cancel_text="Cancelar",
            )

            if not confirmed:
                return

        self._start_worker(
            "verify_remote"
        )

    def _confirm_apply(self):
        if (
            self.last_preview is None
            or self.preview_signature
            != self._current_signature()
        ):
            AppDialog.warning(
                self,
                "Preview requerido",
                (
                    "Los datos cambiaron. Ejecuta "
                    "nuevamente el preview antes "
                    "de aplicar."
                ),
            )
            return

        if self.country == "PER":
            title = (
                "Confirmar modificación del Excel"
            )

            message = (
                "Esta acción modificará la columna "
                "creado del Excel real de proveedores "
                "en SharePoint.\n\n"
                "El backend generará backup y "
                "verificará el archivo después "
                "de subirlo.\n\n"
                "¿Deseas continuar?"
            )

        else:
            title = (
                "Confirmar actualización SharePoint"
            )

            message = (
                "Esta acción actualizará el campo "
                "CREADO de los registros reales "
                "de El Salvador en SharePoint.\n\n"
                "¿Deseas continuar?"
            )

        confirmed = AppDialog.confirm(
            self,
            title,
            message,
            accept_text="Aplicar cambios",
            cancel_text="Cancelar",
            destructive=True,
        )

        if not confirmed:
            return

        self._start_worker(
            "apply"
        )

    def _start_worker(
        self,
        mode: str,
    ):
        if self.thread is not None:
            return

        self.active_mode = mode

        self.preview_button.setEnabled(
            False
        )
        self.apply_button.setEnabled(
            False
        )
        self.local_copy_button.setEnabled(
            False
        )
        self.verify_remote_button.setEnabled(
            False
        )
        self.continue_ambitos_button.setEnabled(
            False
        )

        self.progress.show()

        if mode == "preview":
            self.status_label.setText(
                "Generando preview..."
            )
        elif mode == "local_copy":
            self.status_label.setText(
                "Generando copia local actualizada..."
            )
        elif mode == "verify_remote":
            self.status_label.setText(
                "Verificando reemplazo en SharePoint..."
            )
        else:
            self.status_label.setText(
                "Aplicando cambios remotos..."
            )

        self.thread = QThread(self)

        self.worker = Phase2Worker(
            country=self.country,
            mode=mode,
            run_folder=(
                self.run_folder.text().strip()
            ),
            portal_result=(
                self.portal_result.text().strip()
            ),
            shared_url=(
                self.shared_url.text().strip()
                if self.country == "PER"
                else None
            ),
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
        mode: str,
        result: dict,
    ):
        self.progress.hide()
        self.preview_button.setEnabled(
            True
        )

        if mode == "preview":
            self.last_preview = result
            self.preview_signature = (
                self._current_signature()
            )

            self._show_preview_result(
                result
            )

            can_apply = False
            reasons = []
            pending_changes = 0

            if self.country == "PER":
                backend_ok = bool(
                    result.get(
                        "ok",
                        False,
                    )
                )

                ready = bool(
                    result.get(
                        "listo_para_escritura",
                        False,
                    )
                )

                missing_results = int(
                    result.get(
                        "relaciones_sin_resultado",
                        0,
                    )
                )

                conflicts = int(
                    result.get(
                        "conflictos_remotos",
                        0,
                    )
                )

                verification_errors = int(
                    result.get(
                        "errores_verificacion_remota",
                        0,
                    )
                )

                invalid_states = int(
                    result.get(
                        "estados_remotos_invalidos",
                        0,
                    )
                )

                pending_changes = int(
                    result.get(
                        "actualizaciones_remotas_preview",
                        0,
                    )
                )

                if not backend_ok:
                    reasons.append(
                        "El backend marc? el preview "
                        "como no seguro."
                    )

                if not ready:
                    reasons.append(
                        "El Excel remoto no est? "
                        "listo para escritura."
                    )

                if missing_results:
                    reasons.append(
                        f"{missing_results} relaci?n(es) "
                        "sin resultado del Portal."
                    )

                if conflicts:
                    reasons.append(
                        f"{conflicts} conflicto(s) "
                        "con estados remotos."
                    )

                if verification_errors:
                    reasons.append(
                        f"{verification_errors} error(es) "
                        "de verificaci?n remota."
                    )

                if invalid_states:
                    reasons.append(
                        f"{invalid_states} estado(s) "
                        "remotos inv?lidos."
                    )

                safe = (
                    backend_ok
                    and ready
                    and missing_results == 0
                    and conflicts == 0
                    and verification_errors == 0
                    and invalid_states == 0
                )

            else:
                backend_ok = bool(
                    result.get(
                        "ok",
                        False,
                    )
                )

                failed = result.get(
                    "failed",
                    [],
                )

                preview_rows = result.get(
                    "preview",
                    [],
                )

                pending_changes = len(
                    preview_rows
                )

                if not backend_ok:
                    reasons.append(
                        "El backend marc? el preview "
                        "como no seguro."
                    )

                if failed:
                    reasons.append(
                        f"{len(failed)} registro(s) "
                        "fallaron durante el preview."
                    )

                safe = (
                    backend_ok
                    and not failed
                )

            can_apply = (
                safe
                and pending_changes > 0
            )

            self.apply_button.setEnabled(
                can_apply
            )

            self.local_copy_button.setEnabled(
                can_apply
                and self.country == "PER"
            )

            if can_apply:
                self.status_label.setText(
                    "Preview correcto. "
                    "Los cambios pueden aplicarse."
                )

                self.apply_gate_label.setText(
                    "PREVIEW SEGURO - "
                    f"{pending_changes} cambio(s) "
                    "pendiente(s) de aplicar."
                )

            elif safe:
                self.status_label.setText(
                    "Preview correcto. "
                    "No hay cambios pendientes."
                )

                self.apply_gate_label.setText(
                    "PREVIEW SEGURO - "
                    "El estado remoto ya coincide "
                    "con el resultado calculado. "
                    "No es necesario aplicar cambios."
                )

            else:
                self.status_label.setText(
                    "Preview requiere revisi?n. "
                    "La escritura permanece bloqueada."
                )

                detail = "\n".join(
                    f"- {reason}"
                    for reason in reasons
                )

                if not detail:
                    detail = (
                        "- El backend no indic? "
                        "un motivo espec?fico."
                    )

                self.apply_gate_label.setText(
                    "ESCRITURA BLOQUEADA:\n"
                    + detail
                )

        elif mode == "verify_remote":
            verified = bool(
                result.get(
                    "replacement_verified",
                    False,
                )
            )

            reasons = list(
                result.get(
                    "verification_reasons",
                    [],
                )
                or []
            )

            self.remote_replacement_verified = (
                verified
            )

            if verified:
                self.workflow_status_changed.emit(
                    self.country,
                    "done",
                )

                self.continue_ambitos_button.setEnabled(
                    True
                )

                self.verify_remote_button.setEnabled(
                    False
                )
                self.verify_remote_button.setText(
                    "Reemplazo verificado"
                )

                self.apply_button.setEnabled(
                    False
                )

                self.local_copy_button.setEnabled(
                    False
                )

                self.status_label.setText(
                    "Excel remoto verificado."
                )

                self.apply_gate_label.setText(
                    "REEMPLAZO VERIFICADO - "
                    "El Excel de SharePoint ya contiene "
                    "todos los estados creado=1/2 "
                    "esperados. Puedes continuar "
                    "con Fase 3 - Ambitos."
                )

                AppDialog.success(
                    self,
                    "Reemplazo verificado",
                    (
                        "El Excel publicado en SharePoint "
                        "coincide con el resultado "
                        "calculado por Fase 2.\n\n"
                        "Ya puedes continuar con "
                        "Fase 3 - Ambitos."
                    ),
                )

            else:
                self.workflow_status_changed.emit(
                    self.country,
                    "action",
                )

                self.continue_ambitos_button.setEnabled(
                    False
                )

                self.verify_remote_button.setEnabled(
                    True
                )
                self.verify_remote_button.setText(
                    "Verificar reemplazo"
                )

                # La copia local sigue disponible
                # para volver a reemplazar el remoto.
                self.local_copy_button.setEnabled(
                    self.last_local_copy is not None
                )

                self.status_label.setText(
                    "El reemplazo todav?a no coincide."
                )

                detail = "\n".join(
                    f"- {reason}"
                    for reason in reasons
                )

                if not detail:
                    detail = (
                        "- El Excel remoto no coincide "
                        "todavia con Fase 2."
                    )

                self.apply_gate_label.setText(
                    "REEMPLAZO NO VERIFICADO:\n"
                    + detail
                )

                AppDialog.warning(
                    self,
                    "Reemplazo no verificado",
                    (
                        "El Excel remoto todav?a no "
                        "coincide completamente con "
                        "el resultado de Fase 2.\n\n"
                        + detail
                    ),
                )

        elif mode == "local_copy":
            self.last_local_copy = result

            self.apply_button.setEnabled(
                False
            )

            self.local_copy_button.setEnabled(
                True
            )

            self._show_local_copy_result(
                result
            )

            self.status_label.setText(
                "Copia local actualizada generada."
            )

            self.apply_gate_label.setText(
                "COPIA LOCAL LISTA - "
                "SharePoint NO fue modificado. "
                "Reemplaza manualmente el Excel "
                "remoto con la copia generada y, "
                "despu?s, verifica el reemplazo."
            )

            candidate = str(
                result.get(
                    "candidate_path",
                    "",
                )
                or ""
            )

            AppDialog.success(
                self,
                "Copia local generada",
                (
                    "La copia local fue generada "
                    "y verificada correctamente.\n\n"
                    "SharePoint NO fue modificado.\n\n"
                    "Archivo generado:\n"
                    f"{candidate}"
                ),
            )

        else:
            self.last_apply = result

            self.workflow_status_changed.emit(
                self.country,
                "done",
            )

            self.apply_button.setEnabled(
                False
            )

            self.local_copy_button.setEnabled(
                False
            )

            self._show_apply_result(
                result
            )

            self.continue_ambitos_button.setEnabled(
                True
            )

            self.status_label.setText(
                "Aplicaci?n completada."
            )

            self.apply_gate_label.setText(
                "CAMBIOS APLICADOS - "
                "El estado remoto fue actualizado "
                "y verificado."
            )

            AppDialog.success(
                self,
                "Fase 2 completada",
                (
                    "Los cambios fueron aplicados "
                    "y verificados correctamente."
                ),
            )

    def _show_preview_result(
        self,
        result: dict,
    ):
        self.last_local_copy = None

        self.open_result_button.setText(
            "Abrir resultado"
        )

        self.open_plan_button.setText(
            "Abrir plan"
        )

        self.result_card.show()

        if self.country == "PER":
            self.metric_1_title.setText(
                "Cuentas enviadas"
            )
            self.metric_2_title.setText(
                "Disponibles"
            )
            self.metric_3_title.setText(
                "No creadas"
            )
            self.metric_4_title.setText(
                "Cambios remotos"
            )

            self.metric_1.setText(
                str(
                    result.get(
                        "cuentas_enviadas",
                        0,
                    )
                )
            )

            self.metric_2.setText(
                str(
                    result.get(
                        "cuentas_disponibles",
                        0,
                    )
                )
            )

            self.metric_3.setText(
                str(
                    result.get(
                        "cuentas_no_creadas",
                        0,
                    )
                )
            )

            self.metric_4.setText(
                str(
                    result.get(
                        "actualizaciones_remotas_preview",
                        0,
                    )
                )
            )

            detail = (
                f"Relaciones: "
                f"{result.get('relaciones_total', 0)} · "
                f"creado=1: "
                f"{result.get('relaciones_creado_1', 0)} · "
                f"creado=2: "
                f"{result.get('relaciones_creado_2', 0)} · "
                f"sin resultado: "
                f"{result.get('relaciones_sin_resultado', 0)} · "
                f"conflictos: "
                f"{result.get('conflictos_remotos', 0)}"
            )

            self.open_result_button.setEnabled(
                bool(
                    result.get(
                        "preview_path"
                    )
                )
            )

            self.open_evidence_button.setEnabled(
                bool(
                    result.get(
                        "evidence_path"
                    )
                )
            )

            self.open_plan_button.setEnabled(
                bool(
                    result.get(
                        "plan_path"
                    )
                )
            )

        else:
            self.metric_1_title.setText(
                "Resultados"
            )
            self.metric_2_title.setText(
                "Creados"
            )
            self.metric_3_title.setText(
                "Errores"
            )
            self.metric_4_title.setText(
                "Cambios preview"
            )

            self.metric_1.setText(
                str(
                    result.get(
                        "total",
                        0,
                    )
                )
            )

            self.metric_2.setText(
                str(
                    result.get(
                        "creados",
                        0,
                    )
                )
            )

            self.metric_3.setText(
                str(
                    result.get(
                        "errores",
                        0,
                    )
                )
            )

            preview = result.get(
                "preview",
                [],
            )

            self.metric_4.setText(
                str(len(preview))
            )

            detail = (
                f"Actualizados en dry-run: "
                f"{result.get('updated', 0)} · "
                f"omitidos: "
                f"{result.get('skipped', 0)} · "
                f"fallidos: "
                f"{len(result.get('failed', []))}"
            )

            self.open_result_button.setEnabled(
                bool(
                    result.get(
                        "result_path"
                    )
                )
            )

            self.open_evidence_button.setEnabled(
                False
            )
            self.open_plan_button.setEnabled(
                False
            )

        self.result_detail.setText(
            detail
        )

    def _show_local_copy_result(
        self,
        result: dict,
    ):
        self.result_card.show()

        self.metric_1_title.setText(
            "Cambios locales"
        )
        self.metric_2_title.setText(
            "Verificado = 1"
        )
        self.metric_3_title.setText(
            "Verificado = 2"
        )
        self.metric_4_title.setText(
            "Filas verificadas"
        )

        self.metric_1.setText(
            str(
                result.get(
                    "cambios_aplicados",
                    0,
                )
            )
        )

        self.metric_2.setText(
            str(
                result.get(
                    "verificado_creado_1",
                    0,
                )
            )
        )

        self.metric_3.setText(
            str(
                result.get(
                    "verificado_creado_2",
                    0,
                )
            )
        )

        self.metric_4.setText(
            str(
                result.get(
                    "filas_verificadas",
                    0,
                )
            )
        )

        self.result_detail.setText(
            "Copia local generada y verificada. "
            "SharePoint NO fue modificado. "
            "Esta copia representa el estado del "
            "Excel descargado en este momento."
        )

        self.open_result_button.setText(
            "Abrir copia local"
        )
        self.open_result_button.setEnabled(
            bool(
                result.get(
                    "candidate_path"
                )
            )
        )

        self.open_evidence_button.setEnabled(
            bool(
                result.get(
                    "evidence_path"
                )
            )
        )

        self.open_plan_button.setText(
            "Abrir reporte local"
        )
        self.open_plan_button.setEnabled(
            bool(
                result.get(
                    "report_path"
                )
            )
        )

    def _show_apply_result(
        self,
        result: dict,
    ):
        self.result_card.show()

        if self.country == "PER":
            self.metric_1_title.setText(
                "Relaciones"
            )
            self.metric_2_title.setText(
                "Verificado = 1"
            )
            self.metric_3_title.setText(
                "Verificado = 2"
            )
            self.metric_4_title.setText(
                "Filas verificadas"
            )

            self.metric_1.setText(
                str(
                    result.get(
                        "relaciones_total",
                        0,
                    )
                )
            )

            self.metric_2.setText(
                str(
                    result.get(
                        "verificado_creado_1",
                        0,
                    )
                )
            )

            self.metric_3.setText(
                str(
                    result.get(
                        "verificado_creado_2",
                        0,
                    )
                )
            )

            self.metric_4.setText(
                str(
                    result.get(
                        "filas_verificadas",
                        0,
                    )
                )
            )

            self.result_detail.setText(
                "Excel remoto actualizado, "
                "descargado nuevamente y verificado."
            )

        else:
            self.metric_1_title.setText(
                "Resultados"
            )
            self.metric_2_title.setText(
                "CREADO = 1"
            )
            self.metric_3_title.setText(
                "CREADO = 2"
            )
            self.metric_4_title.setText(
                "Actualizados"
            )

            self.metric_1.setText(
                str(
                    result.get(
                        "total",
                        0,
                    )
                )
            )

            self.metric_2.setText(
                str(
                    result.get(
                        "creados",
                        0,
                    )
                )
            )

            self.metric_3.setText(
                str(
                    result.get(
                        "errores",
                        0,
                    )
                )
            )

            self.metric_4.setText(
                str(
                    result.get(
                        "updated",
                        0,
                    )
                )
            )

            self.result_detail.setText(
                "Estados CREADO actualizados "
                "en SharePoint."
            )

    def _on_failed(
        self,
        mode: str,
        error_detail: str,
        full_trace: str,
    ):
        details = build_error_details(
            phase="2",
            country=self.country,
            mode=mode,
            error_detail=error_detail,
            full_trace=full_trace,
        )
        error_detail = redact_secrets(error_detail)
        self.progress.hide()

        self.preview_button.setEnabled(
            True
        )

        self.apply_button.setEnabled(
            False
        )

        if (
            mode == "verify_remote"
            and self.country == "PER"
        ):
            self.verify_remote_button.setEnabled(
                True
            )


        normalized_error = (
            str(error_detail)
            .lower()
        )

        locked = (
            "http 423"
            in normalized_error
            or "resourcelocked"
            in normalized_error
            or (
                "excel remoto"
                in normalized_error
                and "bloqueado"
                in normalized_error
            )
        )

        if (
            self.country == "PER"
            and mode == "apply"
            and locked
        ):
            self.status_label.setText(
                "El Excel esta bloqueado. "
                "No se aplicaron cambios."
            )

            self.apply_gate_label.setText(
                "ARCHIVO BLOQUEADO - "
                "Cierra el Excel en Excel Desktop, "
                "Teams o Excel Online. "
                "Luego genera un nuevo preview "
                "antes de volver a aplicar."
            )

            title = (
                "Excel bloqueado en SharePoint"
            )

            user_message = (
                "No se pudo actualizar el Excel porque "
                "SharePoint lo mantiene bloqueado para "
                "edici?n.\n\n"
                "Cierra el archivo en Excel Desktop, "
                "Teams y Excel Online. Si otra persona "
                "lo tiene abierto, tambien debe "
                "cerrarlo.\n\n"
                "Despu?s vuelve a generar el Preview "
                "y aplica nuevamente los cambios.\n\n"
                "El archivo remoto no fue modificado."
            )

        else:
            self.status_label.setText(
                "Ocurri? un error."
            )

            title = (
                "Error en Fase 2"
            )

            user_message = str(
                error_detail
            )


        AppDialog.error(
            self,
            title,
            user_message,
            details=details,
        )

    def _cleanup_thread(self):
        if self.worker is not None:
            self.worker.deleteLater()

        if self.thread is not None:
            self.thread.deleteLater()

        self.worker = None
        self.thread = None
        self.active_mode = None

    def _open_path(self, value: str | Path | None):
        open_local_path(self, value)

    def _open_result(self):
        if self.last_local_copy:
            self._open_path(
                self.last_local_copy.get(
                    "candidate_path"
                )
            )
            return

        if not self.last_preview:
            return

        key = (
            "preview_path"
            if self.country == "PER"
            else "result_path"
        )

        self._open_path(
            self.last_preview.get(key)
        )

    def _open_evidence(self):
        if not self.last_preview:
            return

        self._open_path(
            self.last_preview.get(
                "evidence_path"
            )
        )

    def _open_plan(self):
        if self.last_local_copy:
            self._open_path(
                self.last_local_copy.get(
                    "report_path"
                )
            )
            return

        if not self.last_preview:
            return

        self._open_path(
            self.last_preview.get(
                "plan_path"
            )
        )
