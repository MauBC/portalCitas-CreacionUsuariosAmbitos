from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.pages.ambitos_page import (
    AmbitosPage,
)
from app.ui.pages.home_page import (
    HomePage,
)
from app.ui.pages.phase2_page import (
    Phase2Page,
)
from app.ui.pages.users_page import (
    UsersPage,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Automatización Usuarios y Ámbitos"
        )
        self.resize(1180, 760)
        self.setMinimumSize(1020, 680)

        icon_path = Path(
            "Ransalogo.ico"
        )

        if icon_path.exists():
            self.setWindowIcon(
                QIcon(str(icon_path))
            )

        self.pages = QStackedWidget()

        self.home_page = HomePage()
        self.users_page = UsersPage()
        self.phase2_page = Phase2Page()
        self.ambitos_page = AmbitosPage()

        self.pages.addWidget(
            self.home_page
        )
        self.pages.addWidget(
            self.users_page
        )
        self.pages.addWidget(
            self.phase2_page
        )
        self.pages.addWidget(
            self.ambitos_page
        )

        root = QWidget()

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        root_layout.setSpacing(0)

        root_layout.addWidget(
            self._build_sidebar()
        )

        root_layout.addWidget(
            self.pages,
            1,
        )

        self.setCentralWidget(root)

        self.country_combo.currentIndexChanged.connect(
            self._country_changed
        )

        self._show_page(0)
        self._country_changed()

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(
            20,
            25,
            20,
            25,
        )
        layout.setSpacing(8)

        title = QLabel("RANSA")
        title.setObjectName(
            "brandTitle"
        )

        subtitle = QLabel(
            "Portal de Citas"
        )
        subtitle.setObjectName(
            "brandSubtitle"
        )

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(28)

        self.nav_buttons = []

        navigation = [
            ("Inicio", 0),
            ("Usuarios", 1),
            ("Fase 2", 2),
            ("Ámbitos", 3),
        ]

        for text, index in navigation:
            button = QPushButton(text)
            button.setProperty(
                "nav",
                True,
            )

            button.clicked.connect(
                lambda checked=False, i=index:
                self._show_page(i)
            )

            self.nav_buttons.append(
                button
            )

            layout.addWidget(
                button
            )

        layout.addStretch()

        country_label = QLabel(
            "PAÍS DE TRABAJO"
        )
        country_label.setObjectName(
            "sidebarLabel"
        )

        self.country_combo = (
            QComboBox()
        )

        self.country_combo.addItem(
            "Perú",
            "PER",
        )

        self.country_combo.addItem(
            "El Salvador",
            "SLV",
        )

        layout.addWidget(
            country_label
        )
        layout.addWidget(
            self.country_combo
        )
        layout.addSpacing(18)

        footer = QLabel(
            "Backend estable"
        )
        footer.setAlignment(
            Qt.AlignCenter
        )
        footer.setObjectName(
            "brandSubtitle"
        )

        layout.addWidget(footer)

        return sidebar

    def _country_changed(self):
        country = (
            self.country_combo
            .currentData()
        )

        self.users_page.set_country(
            country
        )

    def _show_page(
        self,
        index: int,
    ):
        self.pages.setCurrentIndex(
            index
        )

        for current, button in enumerate(
            self.nav_buttons
        ):
            button.setProperty(
                "selected",
                current == index,
            )

            button.style().unpolish(
                button
            )
            button.style().polish(
                button
            )
