import argparse
import os
import sys

from app.config.env_loader import load_env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Automatizacion Usuarios y Ambitos")
    parser.add_argument("--self-check", metavar="REPORT_JSON",
                        help="Verifica GUI y recursos sin red; guarda un reporte JSON.")
    args = parser.parse_args(argv)
    if args.self_check:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from app.ui.self_check import run_self_check
        return run_self_check(args.self_check)

    from PySide6.QtWidgets import QApplication
    from app.ui.dialogs.app_dialog import AppDialog
    from app.ui.main_window import MainWindow
    from app.ui.styles import APP_STYLE

    app = QApplication(sys.argv)
    app.setApplicationName("Automatizacion Usuarios y Ambitos")
    app.setOrganizationName("Ransa")
    app.setStyle("Fusion")
    app.setStyleSheet(APP_STYLE)
    try:
        load_env()
    except FileNotFoundError as exc:
        AppDialog.error(None, "Falta configuracion",
                        "Crea el archivo .env junto al ejecutable o en la raiz del proyecto.",
                        details=str(exc))
        return 1

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
