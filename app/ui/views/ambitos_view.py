from PySide6.QtWidgets import (
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


class AmbitosView(QWidget):
    """Visual controls only; the page owns settings, events and workflow state."""

    def __init__(self):
        super().__init__()
        self._build_ui()

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

        self.report_button = QPushButton(
            "Seleccionar reporte"
        )
        self.report_button.setObjectName(
            "secondaryButton"
        )

        report_row.addWidget(
            self.valid_report,
            1,
        )

        report_row.addWidget(
            self.report_button
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

        self.review_button = QPushButton(
            "Seleccionar revisión"
        )

        self.review_button.setObjectName(
            "secondaryButton"
        )

        review_row.addWidget(
            self.review_path,
            1,
        )

        review_row.addWidget(
            self.review_button
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

        self.final_button = QPushButton(
            "Generar plantilla FINAL"
        )

        self.final_button.setObjectName(
            "accentButton"
        )

        self.final_button.setEnabled(
            False
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
