from PySide6.QtWidgets import (
    QComboBox,
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


class UsersView(QWidget):
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
            "Pega aquí el enlace del Excel..."
        )
        self.per_url.setClearButtonEnabled(
            True
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

        self.browse_button = QPushButton(
            "Seleccionar Excel"
        )
        self.browse_button.setObjectName(
            "secondaryButton"
        )

        local_layout.addWidget(
            self.per_file,
            1,
        )
        local_layout.addWidget(
            self.browse_button,
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
            QLabel("Válidos"),
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
            QPushButton("Abrir válidos")
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
