from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Phase2Page(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 34, 38, 34)
        layout.setSpacing(10)

        title = QLabel(
            "Fase 2 · Resultado del Portal"
        )
        title.setObjectName("pageTitle")

        description = QLabel(
            "Procesa el archivo devuelto por el Portal "
            "y actualiza el estado de creación."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(24)

        card = QFrame()
        card.setObjectName("card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)

        card_title = QLabel(
            "Resultado de creación"
        )
        card_title.setObjectName("cardTitle")

        button = QPushButton(
            "Seleccionar resultado del Portal"
        )
        button.setObjectName("primaryButton")
        button.setEnabled(False)

        card_layout.addWidget(card_title)
        card_layout.addSpacing(15)
        card_layout.addWidget(button)

        layout.addWidget(card)
        layout.addStretch()
