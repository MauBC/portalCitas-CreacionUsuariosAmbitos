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
from app.ui.result_models import Metric, scope_metrics
from app.ui.widgets.field_feedback import clear_field_error, set_field_error

from app.ui.dialogs.app_dialog import (
    AppDialog,
)

from app.ui.workers.phase3_worker import (
    Phase3Worker,
)


class AmbitosPage(QWidget):
    workflow_status_changed = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.country = "PER"

        self.thread = None
        self.worker = None

        self.last_preview = None
        self.last_final = None

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
        content.setMinimumWidth(
            720
        )

        scroll.setWidget(
            content
        )

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

        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        title = QLabel(
            "Fase 3 · Ámbitos"
        )
        title.setObjectName(
            "pageTitle"
        )

        self.description = QLabel()
        self.description.setObjectName(
            "pageDescription"
        )
        self.description.setWordWrap(
            True
        )

        layout.addWidget(title)
        layout.addWidget(
            self.description
        )
        layout.addSpacing(16)

        # -------------------------------------------------
        # SOURCE
        # -------------------------------------------------

        source_card = QFrame()
        source_card.setObjectName(
            "card"
        )

        source_layout = QVBoxLayout(
            source_card
        )

        source_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        source_layout.setSpacing(10)

        source_title = QLabel(
            "Fuente de relaciones"
        )
        source_title.setObjectName(
            "cardTitle"
        )

        source_layout.addWidget(
            source_title
        )

        report_label = QLabel(
            "Reporte VALIDOS generado por Fase 1"
        )

        report_row = QHBoxLayout()

        self.valid_report = QLineEdit()
        self.valid_report.setPlaceholderText(
            "Selecciona reporte VALIDOS..."
        )

        report_button = QPushButton(
            "Seleccionar reporte"
        )
        report_button.setObjectName(
            "secondaryButton"
        )

        report_button.clicked.connect(
            self._browse_valid_report
        )

        report_row.addWidget(
            self.valid_report,
            1,
        )

        report_row.addWidget(
            report_button
        )

        source_layout.addWidget(
            report_label
        )

        source_layout.addLayout(
            report_row
        )

        self.valid_report_error = QLabel()
        self.valid_report_error.setObjectName(
            "fieldError"
        )
        self.valid_report_error.setWordWrap(
            True
        )
        self.valid_report_error.hide()

        source_layout.addWidget(
            self.valid_report_error
        )

        # -------------------------------------------------
        # PER URL
        # -------------------------------------------------

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

        source_layout.addWidget(
            self.url_label
        )

        source_layout.addWidget(
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

        source_layout.addWidget(
            self.shared_url_error
        )

        # -------------------------------------------------
        # REVIEW FILE
        # -------------------------------------------------

        review_label = QLabel(
            "Archivo de revisión manual"
        )

        review_row = QHBoxLayout()

        self.review_path = QLineEdit()

        self.review_path.setPlaceholderText(
            "Se generará automáticamente "
            "si existen clientes pendientes..."
        )

        review_button = QPushButton(
            "Seleccionar revisión"
        )

        review_button.setObjectName(
            "secondaryButton"
        )

        review_button.clicked.connect(
            self._browse_review
        )

        review_row.addWidget(
            self.review_path,
            1,
        )

        review_row.addWidget(
            review_button
        )

        source_layout.addWidget(
            review_label
        )

        source_layout.addLayout(
            review_row
        )

        self.review_path_error = QLabel()
        self.review_path_error.setObjectName(
            "fieldError"
        )
        self.review_path_error.setWordWrap(
            True
        )
        self.review_path_error.hide()

        source_layout.addWidget(
            self.review_path_error
        )

        # -------------------------------------------------
        # SAFETY
        # -------------------------------------------------

        self.safety_info = QLabel()

        self.safety_info.setObjectName(
            "safeInfo"
        )

        self.safety_info.setWordWrap(
            True
        )

        source_layout.addWidget(
            self.safety_info
        )

        layout.addWidget(
            source_card
        )

        # -------------------------------------------------
        # ACTIONS
        # -------------------------------------------------

        action_card = QFrame()

        action_card.setObjectName(
            "card"
        )

        action_layout = QVBoxLayout(
            action_card
        )

        action_layout.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        action_layout.setSpacing(10)

        action_title = QLabel(
            "Generación"
        )

        action_title.setObjectName(
            "cardTitle"
        )

        self.status_label = QLabel(
            "Selecciona el reporte de Fase 1."
        )

        self.status_label.setObjectName(
            "cardDescription"
        )

        self.status_label.setWordWrap(
            True
        )

        self.progress = QProgressBar()

        self.progress.setRange(
            0,
            0,
        )

        self.progress.setTextVisible(
            False
        )

        self.progress.hide()

        button_row = QHBoxLayout()

        self.preview_button = QPushButton(
            "Generar preview"
        )

        self.preview_button.setObjectName(
            "primaryButton"
        )

        self.preview_button.clicked.connect(
            self._start_preview
        )

        self.final_button = QPushButton(
            "Generar plantilla FINAL"
        )

        self.final_button.setObjectName(
            "accentButton"
        )

        self.final_button.setEnabled(
            False
        )

        self.final_button.clicked.connect(
            self._start_final
        )

        button_row.addWidget(
            self.preview_button
        )

        button_row.addWidget(
            self.final_button
        )

        button_row.addStretch()

        action_layout.addWidget(
            action_title
        )

        action_layout.addWidget(
            self.status_label
        )

        action_layout.addWidget(
            self.progress
        )

        action_layout.addLayout(
            button_row
        )

        layout.addWidget(
            action_card
        )

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

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

        self.result_title = QLabel(
            "Resultado"
        )

        self.result_title.setObjectName(
            "cardTitle"
        )

        result_layout.addWidget(
            self.result_title
        )

        metrics = QGridLayout()

        metrics.setHorizontalSpacing(
            25
        )

        metrics.setVerticalSpacing(
            6
        )

        self.metric_titles = []
        self.metric_values = []

        for column in range(6):
            title_label = QLabel("")

            value_label = QLabel("0")
            value_label.setObjectName(
                "metricValue"
            )

            self.metric_titles.append(
                title_label
            )

            self.metric_values.append(
                value_label
            )

            metrics.addWidget(
                title_label,
                0,
                column,
            )

            metrics.addWidget(
                value_label,
                1,
                column,
            )

        result_layout.addLayout(
            metrics
        )

        self.result_message = QLabel()

        self.result_message.setObjectName(
            "cardDescription"
        )

        self.result_message.setWordWrap(
            True
        )

        result_layout.addWidget(
            self.result_message
        )

        self.review_info = QLabel()

        self.review_info.setWordWrap(
            True
        )

        self.review_info.hide()

        result_layout.addWidget(
            self.review_info
        )

        # -------------------------------------------------
        # FILE BUTTONS
        # -------------------------------------------------

        files_row = QHBoxLayout()

        self.open_preview_button = QPushButton(
            "Abrir PREVIEW"
        )

        self.open_diagnostic_button = QPushButton(
            "Abrir diagnóstico"
        )

        self.open_review_button = QPushButton(
            "Abrir revisión"
        )

        self.open_final_button = QPushButton(
            "Abrir FINAL"
        )

        self.open_folder_button = QPushButton(
            "Abrir carpeta"
        )

        for button in [
            self.open_preview_button,
            self.open_diagnostic_button,
            self.open_review_button,
            self.open_final_button,
            self.open_folder_button,
        ]:
            button.setObjectName(
                "secondaryButton"
            )

            button.setEnabled(
                False
            )

            files_row.addWidget(
                button
            )

        files_row.addStretch()

        self.open_preview_button.clicked.connect(
            self._open_preview
        )

        self.open_diagnostic_button.clicked.connect(
            self._open_diagnostic
        )

        self.open_review_button.clicked.connect(
            self._open_review
        )

        self.open_final_button.clicked.connect(
            self._open_final
        )

        self.open_folder_button.clicked.connect(
            self._open_folder
        )

        result_layout.addLayout(
            files_row
        )

        self.result_card.hide()

        layout.addWidget(
            self.result_card
        )

        layout.addStretch()

        # -------------------------------------------------
        # INVALIDATION
        # -------------------------------------------------

        self.valid_report.textChanged.connect(
            self._on_valid_report_changed
        )

        self.shared_url.textChanged.connect(
            self._on_shared_url_changed
        )

        self.review_path.textChanged.connect(
            self._on_review_path_changed
        )

    # =====================================================
    # COUNTRY
    # =====================================================

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
                "Genera ámbitos usando únicamente "
                "relaciones cuyo estado creado sea 1 "
                "en el Excel real de proveedores."
            )

            self.url_label.show()
            self.shared_url.show()

            self.safety_info.setText(
                "Perú: Fase 3 consulta el Excel de "
                "proveedores en SharePoint para validar "
                "creado=1. No modifica el archivo remoto."
            )

        else:
            self.description.setText(
                "Genera ámbitos usando únicamente "
                "registros cuyo estado CREADO sea 1 "
                "en la lista SharePoint."
            )

            self.url_label.hide()
            self.shared_url.hide()

            self.safety_info.setText(
                "El Salvador: Fase 3 consulta el estado "
                "CREADO real de SharePoint. "
                "No modifica la lista."
            )

    # =====================================================
    # FASE 1 INTEGRATION
    # =====================================================

        if hasattr(
            self,
            "shared_url_error",
        ):
            if self.country != "PER":
                self._clear_inline_error(
                    self.shared_url,
                    self.shared_url_error,
                )
            elif self.shared_url_error.text():
                self.shared_url_error.show()

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

        if country == "PER":
            report = str(
                result.get(
                    "valid_path",
                    "",
                )
                or ""
            ).strip()

        else:
            report = str(
                result.get(
                    "path_validos",
                    "",
                )
                or ""
            ).strip()

        if (
            report
            and Path(report).is_file()
        ):
            self.valid_report.setText(
                report
            )

            self.status_label.setText(
                "Reporte de Fase 1 detectado. "
                "Puedes generar el preview."
            )

    # =====================================================
    # BROWSE
    # =====================================================

    def _browse_valid_report(self):
        path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Seleccionar reporte VALIDOS",
                "",
                "Archivos Excel (*.xlsx *.xlsm)",
            )
        )

        if path:
            self.valid_report.setText(
                path
            )

    def _browse_review(self):
        path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Seleccionar revisión de clientes",
                "",
                "Archivos Excel (*.xlsx *.xlsm)",
            )
        )

        if path:
            self.review_path.setText(
                path
            )

    # =====================================================
    # VALIDATION
    # =====================================================

    def _on_valid_report_changed(self):
        self._invalidate_preview()

        if hasattr(
            self,
            "valid_report_error",
        ):
            self._clear_inline_error(
                self.valid_report,
                self.valid_report_error,
            )

    def _on_shared_url_changed(self):
        self._invalidate_preview()

        if hasattr(
            self,
            "shared_url_error",
        ):
            self._clear_inline_error(
                self.shared_url,
                self.shared_url_error,
            )

    def _on_review_path_changed(self):
        if hasattr(
            self,
            "review_path_error",
        ):
            self._clear_inline_error(
                self.review_path,
                self.review_path_error,
            )

    def _current_signature(self):
        return (
            self.country,
            self.valid_report.text().strip(),
            (
                self.shared_url.text().strip()
                if self.country == "PER"
                else ""
            ),
        )

    def _invalidate_preview(self):
        self.last_preview = None
        self.preview_signature = None

        if hasattr(
            self,
            "final_button",
        ):
            self.final_button.setEnabled(
                False
            )

    def _set_inline_error(self, widget, label, message: str):
        set_field_error(widget, label, message)

    def _clear_inline_error(self, widget, label, *, mark_valid: bool = False):
        clear_field_error(widget, label, mark_valid=mark_valid)

    def _validate_source(self):
        valid = True

        report_value = (
            self.valid_report.text().strip()
        )

        report = Path(
            report_value
        )

        if not report_value:
            self._set_inline_error(
                self.valid_report,
                self.valid_report_error,
                (
                    "Selecciona el reporte VALIDOS "
                    "generado por Fase 1."
                ),
            )

            valid = False

        elif not report.is_file():
            self._set_inline_error(
                self.valid_report,
                self.valid_report_error,
                (
                    "El reporte seleccionado "
                    "no existe."
                ),
            )

            valid = False

        elif (
            report.suffix.lower()
            not in {
                ".xlsx",
                ".xlsm",
            }
        ):
            self._set_inline_error(
                self.valid_report,
                self.valid_report_error,
                (
                    "Selecciona un archivo Excel "
                    ".xlsx o .xlsm."
                ),
            )

            valid = False

        else:
            self._clear_inline_error(
                self.valid_report,
                self.valid_report_error,
                mark_valid=True,
            )

        if self.country == "PER":
            shared_url = (
                self.shared_url.text().strip()
            )

            if not shared_url:
                self._set_inline_error(
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
                self._set_inline_error(
                    self.shared_url,
                    self.shared_url_error,
                    (
                        "El enlace debe comenzar "
                        "con https://"
                    ),
                )

                valid = False

            else:
                self._clear_inline_error(
                    self.shared_url,
                    self.shared_url_error,
                    mark_valid=True,
                )

        else:
            self._clear_inline_error(
                self.shared_url,
                self.shared_url_error,
            )

        if not valid:
            self.status_label.setText(
                "Revisa los campos marcados "
                "antes de generar el preview."
            )

            return False

        return True


    def _start_preview(self):
        if not self._validate_source():
            return

        if self.country == "PER":
            self.settings.setValue(
                "phase1/per_shared_url",
                self.shared_url.text().strip(),
            )

        self._start_worker(
            "preview"
        )

    # =====================================================
    # FINAL
    # =====================================================

    def _start_final(self):
        if (
            self.last_preview is None
            or self.preview_signature
            != self._current_signature()
        ):
            AppDialog.warning(
                self,
                "Preview requerido",
                (
                    "Ejecuta nuevamente el preview "
                    "antes de generar la plantilla final."
                ),
            )

            return

        review = self.review_path.text().strip()

        if (
            review
            and not Path(review).is_file()
        ):
            AppDialog.warning(
                self,
                "Revisión inválida",
                (
                    "El archivo de revisión indicado "
                    "no existe."
                ),
            )

            return

        pending = int(
            self.last_preview.get(
                "no_match",
                0,
            )
        )

        if pending:
            message = (
                f"Existen {pending} relación(es) "
                "que requieren revisión de cliente.\n\n"
                "La plantilla FINAL incorporará las "
                "asignaciones manuales válidas y "
                "dejará fuera cualquier relación "
                "que continúe pendiente.\n\n"
                "¿Deseas generar la plantilla FINAL?"
            )

        else:
            message = (
                "No existen clientes pendientes "
                "de revisión.\n\n"
                "¿Deseas generar la plantilla FINAL?"
            )

        confirmed = AppDialog.confirm(
            self,
            "Generar plantilla FINAL",
            message,
            accept_text="Generar FINAL",
            cancel_text="Cancelar",
        )

        if not confirmed:
            return

        self._start_worker(
            "final"
        )

    # =====================================================
    # WORKER
    # =====================================================

    def _start_worker(
        self,
        mode: str,
    ):
        if self.thread is not None:
            return

        self.preview_button.setEnabled(
            False
        )

        self.final_button.setEnabled(
            False
        )

        self.progress.show()

        if mode == "preview":
            self.status_label.setText(
                "Generando preview de ámbitos..."
            )
        else:
            self.status_label.setText(
                "Generando plantilla FINAL..."
            )

        self.thread = QThread(self)

        self.worker = Phase3Worker(
            country=self.country,
            mode=mode,
            valid_report_path=(
                self.valid_report.text().strip()
            ),
            provider_shared_url=(
                self.shared_url.text().strip()
                if self.country == "PER"
                else None
            ),
            review_path=(
                self.review_path.text().strip()
                or None
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

    # =====================================================
    # RESULTS
    # =====================================================

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

            self.final_button.setEnabled(
                True
            )

            self.status_label.setText(
                "Preview completado correctamente."
            )

        else:
            self.last_final = result

            self.workflow_status_changed.emit(
                self.country,
                "done",
            )

            self._show_final_result(
                result
            )

            self.final_button.setEnabled(
                True
            )

            self.status_label.setText(
                "Plantilla FINAL generada."
            )

            AppDialog.success(
                self,
                "Fase 3 completada",
                (
                    "La plantilla FINAL de ámbitos "
                    "fue generada correctamente."
                ),
            )

    def _set_metrics(self, values: tuple[Metric, ...]):
        for title_label, value_label, metric in zip(self.metric_titles, self.metric_values, values):
            title_label.setText(metric.title)
            value_label.setText(str(metric.value))

    def _show_preview_result(
        self,
        result: dict,
    ):
        self.result_card.show()

        self.result_title.setText(
            "Resultado del PREVIEW"
        )

        self._set_metrics(scope_metrics("preview", result))

        source = int(
            result.get(
                "usuarios_fuente",
                0,
            )
        )

        created = int(
            result.get(
                "usuarios",
                0,
            )
        )

        filtered = int(
            result.get(
                "filtrados_creado",
                0,
            )
        )

        self.result_message.setText(
            (
                f"Relaciones fuente: {source} · "
                f"Estado creado=1 procesado: {created} · "
                f"Filtradas por estado: {filtered} · "
                f"Clientes BD: "
                f"{result.get('clientes_bd', 0)}"
            )
        )

        review = result.get(
            "review_path"
        )

        if review:
            self.review_path.setText(
                str(review)
            )

            pending = int(
                result.get(
                    "no_match",
                    0,
                )
            )

            self.review_info.setObjectName(
                "warningBox"
            )

            self.review_info.setText(
                (
                    f"Hay {pending} relación(es) "
                    "pendiente(s) de cliente. "
                    "Abre el Excel de revisión, completa "
                    "CLIENTE ASIGNADO y guarda el archivo. "
                    "Luego genera la plantilla FINAL."
                )
            )

            self.review_info.show()

            self.open_review_button.setEnabled(
                True
            )

        else:
            self.review_path.clear()

            self.review_info.setObjectName(
                "safeInfo"
            )

            self.review_info.setText(
                "No existen clientes pendientes. "
                "La plantilla FINAL puede generarse "
                "directamente."
            )

            self.review_info.show()

            self.open_review_button.setEnabled(
                False
            )

        self.review_info.style().unpolish(
            self.review_info
        )

        self.review_info.style().polish(
            self.review_info
        )

        self.open_preview_button.setEnabled(
            bool(
                result.get(
                    "template_path"
                )
            )
        )

        self.open_diagnostic_button.setEnabled(
            bool(
                result.get(
                    "diagnostics_path"
                )
            )
        )

        self.open_final_button.setEnabled(
            False
        )

        self.open_folder_button.setEnabled(
            True
        )

    def _show_final_result(
        self,
        result: dict,
    ):
        self.result_card.show()

        self.result_title.setText(
            "Resultado FINAL"
        )

        self._set_metrics(scope_metrics("final", result))

        self.result_message.setText(
            (
                f"Automáticos: "
                f"{result.get('automaticos', 0)} · "
                f"Revisión total: "
                f"{result.get('revision_total', 0)} · "
                f"Manuales asignados: "
                f"{result.get('manuales_asignados', 0)} · "
                f"Manuales incorporados: "
                f"{result.get('manuales_incorporados', 0)} · "
                f"Pendientes totales: "
                f"{result.get('pendientes_total', 0)}"
            )
        )

        pending = int(
            result.get(
                "pendientes_total",
                0,
            )
        )

        if pending:
            self.review_info.setObjectName(
                "warningBox"
            )

            self.review_info.setText(
                (
                    f"La plantilla FINAL fue generada, "
                    f"pero {pending} relación(es) "
                    "continúan pendientes y NO fueron "
                    "incluidas."
                )
            )

        else:
            self.review_info.setObjectName(
                "safeInfo"
            )

            self.review_info.setText(
                "Plantilla FINAL completa. "
                "No existen relaciones pendientes."
            )

        self.review_info.show()

        self.review_info.style().unpolish(
            self.review_info
        )

        self.review_info.style().polish(
            self.review_info
        )

        self.open_final_button.setEnabled(
            bool(
                result.get(
                    "template_path"
                )
            )
        )

        self.open_diagnostic_button.setEnabled(
            bool(
                result.get(
                    "diagnostics_path"
                )
            )
        )

        self.open_folder_button.setEnabled(
            True
        )

    # =====================================================
    # ERROR
    # =====================================================

    def _on_failed(
        self,
        mode: str,
        error_detail: str,
        full_trace: str,
    ):
        details = build_error_details(
            phase="3",
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

        self.final_button.setEnabled(
            self.last_preview is not None
        )

        self.status_label.setText(
            "Ocurrió un error durante Fase 3."
        )


        normalized_error = (
            str(error_detail)
            .lower()
        )

        if (
            "no existen registros"
            in normalized_error
            and "creado"
            in normalized_error
        ):
            user_message = (
                "El Excel publicado en SharePoint "
                "todav?a no contiene registros con "
                "creado=1.\n\n"
                "Si generaste una copia local en "
                "Fase 2, reemplaza primero el Excel "
                "en SharePoint y vuelve a ejecutar "
                "el preview de ?mbitos."
            )

            title = (
                "Fase 2 a?n no est? consolidada"
            )

        else:
            title = "Error en Fase 3"
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

    # =====================================================
    # OPEN FILES
    # =====================================================

    def _open_path(self, value: str | Path | None):
        open_local_path(self, value)

    def _open_preview(self):
        if self.last_preview:
            self._open_path(
                self.last_preview.get(
                    "template_path"
                )
            )

    def _open_diagnostic(self):
        result = (
            self.last_final
            or self.last_preview
        )

        if result:
            self._open_path(
                result.get(
                    "diagnostics_path"
                )
            )

    def _open_review(self):
        self._open_path(
            self.review_path.text().strip()
        )

    def _open_final(self):
        if self.last_final:
            self._open_path(
                self.last_final.get(
                    "template_path"
                )
            )

    def _open_folder(self):
        report = self.valid_report.text().strip()

        if not report:
            return

        path = Path(report)

        if path.is_file():
            self._open_path(
                path.parent
            )
