from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QHBoxLayout, QLabel, QListWidget, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)
from app.services.run_history_service import RunHistory, STATUS_LABELS, inspect_legacy_folder
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.file_actions import open_local_path


class HistoryPage(QWidget):
    resume_requested = Signal(dict)

    def __init__(self):
        super().__init__()
        self.records = []
        self.country = "PER"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        title = QLabel("Historial y recuperación")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        self.info = QLabel()
        self.info.setWordWrap(True)
        layout.addWidget(self.info)
        actions = QHBoxLayout()
        for text, handler in (("Actualizar", self.refresh), ("Recuperar carpeta anterior", self.import_folder)):
            button = QPushButton(text)
            button.setObjectName("secondaryButton")
            button.clicked.connect(handler)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.table = QTableWidget(0, 4)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().hide()
        self.table.setHorizontalHeaderLabels(["Fecha", "Fase", "Modo", "Resultado local"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._selection_changed)
        layout.addWidget(self.table, 2)
        self.file_info = QLabel("Selecciona una ejecución para consultar sus archivos.")
        layout.addWidget(self.file_info)
        self.files = QListWidget()
        self.files.setAccessibleName("Archivos de la ejecución seleccionada")
        layout.addWidget(self.files, 1)
        bottom = QHBoxLayout()
        self.open_button = QPushButton("Abrir archivo o carpeta")
        self.open_button.setObjectName("secondaryButton")
        self.open_button.clicked.connect(self.open_selected)
        self.resume_button = QPushButton("Recuperar entradas")
        self.resume_button.setObjectName("primaryButton")
        self.resume_button.clicked.connect(self.resume_selected)
        bottom.addWidget(self.open_button)
        bottom.addWidget(self.resume_button)
        layout.addLayout(bottom)
        note = QLabel("Recuperar no ejecuta operaciones ni acredita el estado remoto. Revisa los archivos y el enlace de SharePoint; después genera un nuevo preview.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self._selection_changed()

    def refresh(self):
        try:
            records, skipped = RunHistory().list_runs()
        except OSError:
            self.info.setText("No se pudo leer el historial. Comprueba el acceso a la carpeta de salidas.")
            return
        self.records = [record for record in records if record["country"] == self.country]
        self.table.setRowCount(0)
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            mode = {"users": "Usuarios", "preview": "Preview", "apply": "Aplicación",
                    "local_copy": "Copia local", "verify_remote": "Verificación", "final": "Final"}.get(record.get("mode"), record.get("mode", ""))
            for column, value in enumerate((record["created"].replace("T", " "),
                                            f"Fase {record['phase']}", mode,
                                            STATUS_LABELS[record["status"]])):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
        self.info.setText(f"{self.country} · {len(self.records)} registros. {skipped} registros ilegibles omitidos.\nEl resultado describe la ejecución local, no el estado actual de SharePoint.")
        self._selection_changed()

    def _selected(self):
        row = self.table.currentRow()
        return self.records[row] if 0 <= row < len(self.records) else None

    def _selection_changed(self):
        self.files.clear()
        record = self._selected()
        if record:
            values = {**record.get("inputs", {}), **record.get("outputs", {})}
            values.pop("source_type", None)
            for value in dict.fromkeys(values.values()):
                if value and Path(value).exists():
                    self.files.addItem(value)
        if self.files.count():
            self.files.setCurrentRow(0)
        self.file_info.setText(
            f"{self.files.count()} archivos o carpetas disponibles en sus rutas originales."
            if record else "Selecciona una ejecución para consultar sus archivos."
        )
        self.open_button.setEnabled(bool(self.files.count()))
        self.resume_button.setEnabled(record is not None)

    def open_selected(self):
        item = self.files.currentItem()
        if item:
            open_local_path(self, item.text())

    def resume_selected(self):
        if record := self._selected():
            self.resume_requested.emit(record)

    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, f"Carpeta de Fase 1 para {self.country}")
        if not folder:
            return
        try:
            record = inspect_legacy_folder(folder, self.country)
        except (OSError, ValueError) as exc:
            AppDialog.warning(self, "Carpeta no recuperable", str(exc))
            return
        if AppDialog.confirm(self, "Confirmar país de la carpeta", f"¿Esta carpeta corresponde a {self.country}?\n\n{folder}\n\nSe recuperarán las entradas, sin marcar fases como completadas."):
            self.resume_requested.emit(record)
