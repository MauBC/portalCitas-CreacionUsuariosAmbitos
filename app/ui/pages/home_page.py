from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(38, 34, 38, 34)
        layout.setSpacing(10)

        title = QLabel(
            "Automatización de Usuarios y Ámbitos"
        )
        title.setObjectName("pageTitle")

        description = QLabel(
            "Gestiona el flujo de creación de usuarios, "
            "resultado del Portal y generación de ámbitos."
        )
        description.setObjectName("pageDescription")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(25)

        cards = QHBoxLayout()
        cards.setSpacing(18)

        cards.addWidget(
            self._create_card(
                "Fase 1",
                "Usuarios",
                "Validar información y generar "
                "la plantilla de usuarios.",
            )
        )

        cards.addWidget(
            self._create_card(
                "Fase 2",
                "Resultado Portal",
                "Procesar el resultado de creación "
                "devuelto por el Portal.",
            )
        )

        cards.addWidget(
            self._create_card(
                "Fase 3",
                "Ámbitos",
                "Generar Entidades, relaciones "
                "y ámbitos de acceso.",
            )
        )

        layout.addLayout(cards)
        layout.addStretch()

    def _create_card(
        self,
        phase,
        title,
        description,
    ):
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(8)

        phase_label = QLabel(phase)
        phase_label.setObjectName("phaseNumber")

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        description_label = QLabel(description)
        description_label.setObjectName(
            "cardDescription"
        )
        description_label.setWordWrap(True)

        status = QLabel("Pendiente")
        status.setObjectName("statusPending")

        layout.addWidget(phase_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()
        layout.addWidget(status)

        return card
