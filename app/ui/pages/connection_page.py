from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QLabel, QPlainTextEdit, QPushButton, QVBoxLayout, QWidget
from app.services.connection_check_service import check_connections
from app.ui.error_guidance import error_guidance


class ConnectionWorker(QObject):
    progress = Signal(str)
    finished = Signal(list)

    def __init__(self, country):
        super().__init__()
        self.country = country

    @Slot()
    def run(self):
        self.finished.emit(check_connections(self.country, self.progress.emit))


class ConnectionPage(QWidget):
    busy_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.thread = self.worker = None
        self.country = "PER"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        title = QLabel("Comprobar conexión")
        title.setObjectName("pageTitle")
        layout.addWidget(title)
        note = QLabel("Consulta PostgreSQL y los metadatos de SharePoint sin modificar datos. Conecta la VPN antes de iniciar. La prueba no garantiza permisos de escritura ni el acceso a cada archivo.")
        note.setWordWrap(True)
        layout.addWidget(note)
        self.button = QPushButton("Comprobar PER")
        self.button.setObjectName("primaryButton")
        self.button.clicked.connect(self.start)
        layout.addWidget(self.button)
        self.status = QLabel("La comprobación solo se ejecuta cuando la solicitas.")
        layout.addWidget(self.status)
        self.results = QPlainTextEdit()
        self.results.setReadOnly(True)
        layout.addWidget(self.results)

    def set_country(self, country):
        self.country = country
        self.button.setText(f"Comprobar {country}")
        self.results.clear()
        self.status.setText("La comprobación solo se ejecuta cuando la solicitas.")

    def start(self):
        if self.thread is not None:
            return
        self.results.clear()
        self.thread = QThread(self)
        self.worker = ConnectionWorker(self.country)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(self._finished)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self._cleanup)
        self.button.setEnabled(False)
        self.busy_changed.emit(True)
        self.thread.start()

    def _finished(self, results):
        self.results.setPlainText("\n\n".join(
            f"{item['name']}: {'OK' if item['ok'] else 'ERROR'}\n{item['detail']}\n"
            + (error_guidance(item['detail']) if not item['ok'] else "") for item in results
        ))
        self.status.setText("Comprobación terminada. No se modificaron datos.")

    def _cleanup(self):
        self.thread.wait()
        self.thread.deleteLater()
        self.thread = self.worker = None
        self.button.setEnabled(True)
        self.busy_changed.emit(False)
