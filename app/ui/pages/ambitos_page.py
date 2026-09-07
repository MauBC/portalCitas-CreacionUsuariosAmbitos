from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class AmbitosPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 34, 38, 34)
        layout.setSpacing(10)

        title = QLabel("Fase 3 · Ámbitos")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Genera Entidades, RelacionNueva "
            "y Ámbitos para el Portal."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(20)

        warning = QLabel(
            "Cuando se crean proveedores nuevos, el Portal "
            "puede requerir una segunda carga del mismo archivo "
            "para completar RelacionNueva."
        )
        warning.setObjectName("warningBox")
        warning.setWordWrap(True)

        layout.addWidget(warning)
        layout.addSpacing(14)

        card = QFrame()
        card.setObjectName("card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)

        card_title = QLabel(
            "Generación de ámbitos"
        )
        card_title.setObjectName("cardTitle")

        button = QPushButton(
            "Generar plantilla de ámbitos"
        )
        button.setObjectName("primaryButton")
        button.setEnabled(False)

        card_layout.addWidget(card_title)
        card_layout.addSpacing(15)
        card_layout.addWidget(button)

        layout.addWidget(card)
        layout.addStretch()
