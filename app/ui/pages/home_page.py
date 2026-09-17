from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from app.ui.workflow_presentation import STEPS, STATUS_LABELS, normalize_status


class HomePage(QWidget):
    """Session overview; navigation never starts a pipeline."""
    navigate_requested = Signal(int)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        root.addWidget(scroll)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(18)
        scroll.setWidget(content)

        self.country_label = QLabel()
        self.country_label.setObjectName("phaseNumber")
        layout.addWidget(self.country_label)
        title = QLabel("Tu flujo de trabajo")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        description = QLabel("Prepara usuarios, reconcilia el resultado del Portal y genera ámbitos.")
        description.setWordWrap(True)
        description.setObjectName("pageDescription")
        layout.addWidget(description)

        summary = QFrame()
        summary.setObjectName("card")
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(22, 18, 22, 18)
        self.progress_label = QLabel()
        self.progress_label.setObjectName("cardTitle")
        summary_layout.addWidget(self.progress_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 3)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)
        self.progress.setAccessibleName("Fases completadas en esta sesión")
        summary_layout.addWidget(self.progress)
        self.next_button = QPushButton()
        self.next_button.setObjectName("primaryButton")
        self.next_button.clicked.connect(lambda: self.navigate_requested.emit(self.next_index))
        summary_layout.addWidget(self.next_button, 0, Qt.AlignLeft)
        layout.addWidget(summary)

        self.status_labels = {}
        self.phase_buttons = {}
        self.descriptions = {}
        grid = QGridLayout()
        grid.setSpacing(14)
        descriptions = (
            "Valida los registros y genera la plantilla para cargarla manualmente al Portal.",
            "Procesa el resultado del Portal y verifica los estados publicados.",
            "Genera ámbitos solo para las relaciones con estado creado=1 publicado.",
        )
        for row, (index, title, key) in enumerate(STEPS):
            card = QFrame()
            card.setObjectName("card")
            card_layout = QGridLayout(card)
            card_layout.setContentsMargins(20, 16, 20, 16)
            number = QLabel(f"0{index}")
            number.setObjectName("phaseNumber")
            card_layout.addWidget(number, 0, 0, 2, 1)
            heading = QLabel(title)
            heading.setObjectName("cardTitle")
            card_layout.addWidget(heading, 0, 1)
            description = QLabel(descriptions[row])
            description.setWordWrap(True)
            description.setObjectName("cardDescription")
            card_layout.addWidget(description, 1, 1)
            self.descriptions[key] = description
            status = QLabel()
            status.setObjectName("workflowBadge")
            card_layout.addWidget(status, 0, 2)
            self.status_labels[key] = status
            button = QPushButton("Abrir fase")
            button.setAccessibleName(f"Abrir {title}")
            button.setObjectName("secondaryButton")
            button.clicked.connect(lambda checked=False, i=index: self.navigate_requested.emit(i))
            card_layout.addWidget(button, 1, 2)
            self.phase_buttons[key] = button
            card_layout.setColumnStretch(1, 1)
            grid.addWidget(card, row, 0)
        layout.addLayout(grid)
        note = QLabel("El progreso corresponde a esta sesión. Las cargas al Portal y el reemplazo manual en SharePoint siguen siendo acciones tuyas.")
        note.setWordWrap(True)
        note.setObjectName("pageDescription")
        layout.addWidget(note)
        layout.addStretch()
        self.set_workflow("PER", {})

    def set_workflow(self, country: str, states: dict):
        self.country_label.setText("PERÚ · PORTAL DE CITAS" if country == "PER" else "EL SALVADOR · PORTAL DE CITAS")
        normalized = {key: normalize_status(states.get(key)) for _, _, key in STEPS}
        completed = sum(value == "done" for value in normalized.values())
        self.progress_label.setText(f"{completed} de 3 fases completadas")
        self.progress.setValue(completed)
        self.descriptions["phase2"].setText(
            "Genera la copia local, reemplaza el Excel en SharePoint y verifica la publicación."
            if country == "PER" else
            "Revisa el resultado del Portal y aplica los estados a la lista de SharePoint."
        )
        for index, title, key in STEPS:
            label = self.status_labels[key]
            label.setText(STATUS_LABELS[normalized[key]])
            label.setProperty("workflowStatus", normalized[key])
            label.style().unpolish(label)
            label.style().polish(label)
        next_step = next((step for step in STEPS if normalized[step[2]] != "done"), STEPS[-1])
        self.next_index = next_step[0]
        self.next_button.setText(
            "Revisar Ámbitos" if completed == 3 else f"Continuar: {next_step[1]}"
        )
