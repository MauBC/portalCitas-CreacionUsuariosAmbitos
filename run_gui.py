import sys

from app.config.env_loader import (
    load_env,
)

load_env()

from PySide6.QtWidgets import (
    QApplication,
)

from app.ui.main_window import (
    MainWindow,
)
from app.ui.styles import (
    APP_STYLE,
)


def main():
    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Automatizacion Usuarios y Ambitos"
    )

    app.setOrganizationName(
        "Ransa"
    )

    app.setStyle(
        "Fusion"
    )

    app.setStyleSheet(
        APP_STYLE
    )

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
