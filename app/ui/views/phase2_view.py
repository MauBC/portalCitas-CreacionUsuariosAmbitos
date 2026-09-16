from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QProgressBar,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)


class Phase2View(QWidget):
    """Visual controls only; Phase2Page owns settings, events and workflow state."""

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

        layout.addWidget(self._build_inputs())
        layout.addWidget(self._build_actions())
        layout.addWidget(self._build_results())
        layout.addStretch()

    def _build_inputs(self):
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

        self.browse_run_button = QPushButton(
            "Seleccionar carpeta"
        )
        self.browse_run_button.setObjectName(
            "secondaryButton"
        )

        run_row.addWidget(
            self.run_folder,
            1,
        )
        run_row.addWidget(self.browse_run_button)

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

        self.browse_portal_button = QPushButton(
            "Seleccionar Excel"
        )
        self.browse_portal_button.setObjectName(
            "secondaryButton"
        )

        portal_row.addWidget(
            self.portal_result,
            1,
        )
        portal_row.addWidget(self.browse_portal_button)

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

        return input_card


    def _build_actions(self):
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

        self.local_copy_button = QPushButton(
            "Generar copia local actualizada"
        )
        self.local_copy_button.setObjectName(
            "primaryButton"
        )
        self.local_copy_button.setEnabled(
            False
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

        self.apply_button = QPushButton(
            "Aplicar cambios"
        )
        self.apply_button.setObjectName(
            "dangerButton"
        )
        self.apply_button.setEnabled(False)

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

        return action_card


    def _build_results(self):
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

        return self.result_card

    def _metric(self):
        label = QLabel("0")
        label.setObjectName(
            "metricValue"
        )
        return label
