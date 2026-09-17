from app.config.paths import PROJECT_ROOT

from PySide6.QtCore import Qt, QSignalBlocker
from PySide6.QtGui import QCloseEvent, QIcon
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
from app.ui.dialogs.app_dialog import AppDialog
from app.ui.workflow_presentation import STEPS, STATUS_LABELS, STATUS_SYMBOLS, normalize_status
from app.ui.pages.history_page import HistoryPage
from app.ui.pages.connection_page import ConnectionPage
from app.services.run_history_service import recovery_inputs


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "Automatización Usuarios y Ámbitos"
        )
        self.resize(1180, 760)
        self.setMinimumSize(1020, 680)

        icon_path = PROJECT_ROOT / "Ransalogo.ico"

        if icon_path.exists():
            self.setWindowIcon(
                QIcon(str(icon_path))
            )

        self.pages = QStackedWidget()

        self.home_page = HomePage()
        self.users_page = UsersPage()
        self.phase2_page = Phase2Page()
        self.ambitos_page = AmbitosPage()
        self.history_page = HistoryPage()
        self.connection_page = ConnectionPage()

        self.workflow_states = {
            "PER": {
                "users": "pending",
                "phase2": "pending",
                "ambitos": "pending",
            },
            "SLV": {
                "users": "pending",
                "phase2": "pending",
                "ambitos": "pending",
            },
        }

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
        self.pages.addWidget(self.history_page)
        self.pages.addWidget(self.connection_page)
        self.history_page.resume_requested.connect(self._restore_execution)

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
        self.home_page.navigate_requested.connect(self._show_page)

        for page in self._operation_pages():
            page.busy_changed.connect(self._refresh_operation_state)

        self.country_combo.currentIndexChanged.connect(
            self._country_changed
        )

        self.users_page.phase1_completed.connect(
            self.phase2_page.set_phase1_result
        )

        self.users_page.phase1_completed.connect(
            self.ambitos_page.set_phase1_result
        )

        self.users_page.navigate_requested.connect(
            self._show_page
        )

        self.phase2_page.navigate_requested.connect(
            self._show_page
        )

        self.users_page.phase1_completed.connect(
            self._on_phase1_workflow_completed
        )

        self.phase2_page.workflow_status_changed.connect(
            self._on_phase2_workflow_status
        )

        self.ambitos_page.workflow_status_changed.connect(
            self._on_ambitos_workflow_status
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
            ("Historial", 4),
            ("Conexión", 5),
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
        if self._operation_in_progress():
            with QSignalBlocker(self.country_combo):
                self.country_combo.setCurrentIndex(
                    self.country_combo.findData(self.users_page.country)
                )
            return

        country = (
            self.country_combo
            .currentData()
        )

        self.users_page.set_country(
            country
        )

        self.phase2_page.set_country(
            country
        )

        self.ambitos_page.set_country(
            country
        )
        self.history_page.country = country
        self.connection_page.set_country(country)
        if self.pages.currentIndex() == 4:
            self.history_page.refresh()

        self._refresh_workflow_navigation()

    def _current_country(self):
        return str(
            self.country_combo.currentData()
            or "PER"
        ).strip().upper()

    def _on_phase1_workflow_completed(
        self,
        country: str,
        result: dict,
    ):
        country = str(
            country or ""
        ).strip().upper()

        if country not in self.workflow_states:
            return

        self.workflow_states[
            country
        ]["users"] = "done"

        self.workflow_states[country]["phase2"] = "pending"

        self.workflow_states[
            country
        ]["ambitos"] = "pending"

        self._refresh_workflow_navigation()

    def _on_phase2_workflow_status(
        self,
        country: str,
        status: str,
    ):
        country = str(
            country or ""
        ).strip().upper()

        status = normalize_status(status)

        if country not in self.workflow_states:
            return

        self.workflow_states[
            country
        ]["phase2"] = status

        if status == "done":
            self.workflow_states[
                country
            ]["ambitos"] = "pending"

        self._refresh_workflow_navigation()

    def _on_ambitos_workflow_status(
        self,
        country: str,
        status: str,
    ):
        country = str(
            country or ""
        ).strip().upper()

        status = normalize_status(status)

        if country not in self.workflow_states:
            return

        self.workflow_states[
            country
        ]["ambitos"] = status

        self._refresh_workflow_navigation()

    def _refresh_workflow_navigation(self):
        states = self.workflow_states.get(self._current_country(), {})
        self.home_page.set_workflow(self._current_country(), states)
        for index, label, key in STEPS:
            button = self.nav_buttons[index]
            status = normalize_status(states.get(key))
            button.setText(f"{STATUS_SYMBOLS[status]}  {label}")
            button.setProperty("workflowStatus", status)
            button.setToolTip(STATUS_LABELS[status])
            button.style().unpolish(button)
            button.style().polish(button)

    def _show_page(
        self,
        index: int,
    ):
        if self._operation_in_progress():
            return

        self.pages.setCurrentIndex(
            index
        )
        if index == 4:
            self.history_page.refresh()

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

    def _operation_pages(self):
        return (self.users_page, self.phase2_page, self.ambitos_page, self.connection_page)

    def _operation_in_progress(self) -> bool:
        # Keep the guard until queued results and thread cleanup have completed.
        return any(page.thread is not None for page in self._operation_pages())

    def _refresh_operation_state(self, _busy: bool):
        busy = self._operation_in_progress()
        self.country_combo.setEnabled(not busy)
        self.home_page.setEnabled(not busy)
        self.history_page.setEnabled(not busy)
        for button in self.nav_buttons:
            button.setEnabled(not busy)
        if busy:
            self.statusBar().showMessage(
                "Procesamiento en curso. Espera a que termine para cambiar de fase o país."
            )
        else:
            self.statusBar().clearMessage()

    def closeEvent(self, event: QCloseEvent):
        if self._operation_in_progress():
            event.ignore()
            AppDialog.warning(
                self,
                "Procesamiento en curso",
                "Espera a que termine la operación antes de cerrar la aplicación.",
            )
            return
        super().closeEvent(event)

    def _restore_execution(self, record):
        if self._operation_in_progress() or record.get("country") not in {"PER", "SLV"}:
            return
        try:
            inputs = recovery_inputs(record)
        except OSError:
            inputs = {}
        if not any(key in inputs for key in ("run_folder", "valid_report_path", "file_path")):
            AppDialog.warning(self, "Entradas no disponibles", "Los archivos necesarios ya no están en sus rutas originales. Selecciónalos manualmente o recupera otra carpeta.")
            return
        country = record["country"]
        self.country_combo.setCurrentIndex(self.country_combo.findData(country))
        self.users_page.set_country(country)
        self.phase2_page._invalidate_preview()
        self.ambitos_page._invalidate_preview()
        self.phase2_page.run_folder.clear()
        self.phase2_page.portal_result.clear()
        self.ambitos_page.valid_report.clear()
        self.ambitos_page.review_path.clear()
        self.workflow_states[country] = {"users": "pending", "phase2": "pending", "ambitos": "pending"}
        self._refresh_workflow_navigation()
        self.phase2_page.run_folder.setText(inputs.get("run_folder", ""))
        self.phase2_page.portal_result.setText(inputs.get("portal_result", ""))
        self.ambitos_page.valid_report.setText(inputs.get("valid_report_path", ""))
        self.ambitos_page.review_path.setText(inputs.get("review_path", ""))
        if record["phase"] == 3 and "valid_report_path" in inputs:
            index = 3
        elif "run_folder" in inputs:
            index = 2
        elif "valid_report_path" in inputs:
            index = 3
        else:
            self.users_page.set_country(country)
            self.users_page.per_source_combo.setCurrentIndex(1)
            self.users_page.per_file.setText(inputs["file_path"])
            index = 1
        self._show_page(index)
        self.statusBar().showMessage("Entradas recuperadas. Revisa el país, los archivos y el enlace de SharePoint. Genera un nuevo preview antes de continuar.")
