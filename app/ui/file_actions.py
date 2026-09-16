"""Shared desktop actions for generated files and execution directories."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget

from app.ui.dialogs.app_dialog import AppDialog


def open_local_path(parent: QWidget, value: str | Path | None) -> bool:
    if not value:
        return False
    path = Path(value)
    if not path.exists():
        AppDialog.warning(parent, "Archivo no encontrado", str(path))
        return False
    opened = QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
    if not opened:
        AppDialog.warning(
            parent,
            "No se pudo abrir",
            f"No se pudo abrir el archivo o carpeta con la aplicacion del sistema:\n{path}",
        )
    return opened
