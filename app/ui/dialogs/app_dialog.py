from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)
from app.services.error_report_service import redact_secrets


class AppDialog(QDialog):
    ACCENTS = {
        "success": "dialogAccentSuccess",
        "info": "dialogAccentInfo",
        "warning": "dialogAccentWarning",
        "error": "dialogAccentError",
    }

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        *,
        kind: str = "info",
        details: str | None = None,
        confirm: bool = False,
        accept_text: str = "Aceptar",
        cancel_text: str = "Cancelar",
        destructive: bool = False,
    ):
        super().__init__(parent)

        self.setModal(True)

        self.setWindowFlags(
            Qt.Dialog
            | Qt.FramelessWindowHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground,
            True,
        )

        self.setMinimumWidth(520)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            12,
            12,
            12,
            12,
        )

        card = QFrame()
        card.setObjectName(
            "dialogCard"
        )

        outer.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            0,
            0,
            0,
            20,
        )
        layout.setSpacing(0)

        accent = QFrame()
        accent.setFixedHeight(6)
        accent.setObjectName(
            self.ACCENTS.get(
                kind,
                "dialogAccentInfo",
            )
        )

        layout.addWidget(accent)

        content = QVBoxLayout()
        content.setContentsMargins(
            24,
            20,
            24,
            0,
        )
        content.setSpacing(14)

        header = QHBoxLayout()

        title_label = QLabel(title)
        title_label.setObjectName(
            "dialogTitle"
        )

        close_button = QPushButton("×")
        close_button.setObjectName(
            "dialogCloseButton"
        )
        close_button.setFixedSize(
            30,
            30,
        )
        close_button.clicked.connect(
            self.reject
        )

        header.addWidget(
            title_label,
            1,
        )
        header.addWidget(
            close_button
        )

        content.addLayout(header)

        message_label = QLabel(message)
        message_label.setTextFormat(Qt.PlainText)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_label.setObjectName(
            "dialogMessage"
        )
        message_label.setWordWrap(True)

        content.addWidget(
            message_label
        )

        self.details_box = None

        if details:
            self.details_button = QPushButton(
                "Ver detalles técnicos"
            )
            details_button = self.details_button
            details_button.setObjectName(
                "dialogDetailsButton"
            )

            self.details_box = (
                QPlainTextEdit()
            )
            self.details_box.setObjectName(
                "dialogDetails"
            )
            self.details_box.setReadOnly(
                True
            )
            self.details_box.setPlainText(
                redact_secrets(details)
            )
            self.details_box.setMaximumHeight(
                180
            )
            self.details_box.hide()

            details_button.clicked.connect(
                self._toggle_details
            )

            content.addWidget(
                details_button,
                0,
                Qt.AlignLeft,
            )

            content.addWidget(
                self.details_box
            )
            self.copy_details_button = QPushButton("Copiar diagnóstico")
            self.copy_details_button.setObjectName("secondaryButton")
            self.copy_details_button.clicked.connect(self._copy_details)
            content.addWidget(self.copy_details_button, 0, Qt.AlignLeft)

        buttons = QHBoxLayout()
        buttons.addStretch()

        if confirm:
            cancel_button = QPushButton(
                cancel_text
            )
            cancel_button.setObjectName(
                "secondaryButton"
            )
            cancel_button.clicked.connect(
                self.reject
            )

            buttons.addWidget(
                cancel_button
            )

        accept_button = QPushButton(
            accept_text
        )

        accept_button.setObjectName(
            (
                "accentButton"
                if destructive
                else "primaryButton"
            )
        )

        accept_button.clicked.connect(
            self.accept
        )

        buttons.addWidget(
            accept_button
        )

        content.addLayout(
            buttons
        )

        layout.addLayout(
            content
        )

    def _toggle_details(self):
        if self.details_box is None:
            return

        self.details_box.setVisible(
            not self.details_box.isVisible()
        )
        self.details_button.setText(
            "Ocultar detalles técnicos" if self.details_box.isVisible() else "Ver detalles técnicos"
        )

        self.adjustSize()

    def _copy_details(self):
        if self.details_box is not None:
            QApplication.clipboard().setText(self.details_box.toPlainText())
            self.copy_details_button.setText("Diagnóstico copiado")

    @classmethod
    def _show(
        cls,
        parent,
        title: str,
        message: str,
        **kwargs,
    ) -> bool:
        dialog = cls(
            parent,
            title,
            message,
            **kwargs,
        )

        return (
            dialog.exec()
            == QDialog.Accepted
        )

    @classmethod
    def success(
        cls,
        parent,
        title: str,
        message: str,
    ) -> None:
        cls._show(
            parent,
            title,
            message,
            kind="success",
        )

    @classmethod
    def info(
        cls,
        parent,
        title: str,
        message: str,
    ) -> None:
        cls._show(
            parent,
            title,
            message,
            kind="info",
        )

    @classmethod
    def warning(
        cls,
        parent,
        title: str,
        message: str,
    ) -> None:
        cls._show(
            parent,
            title,
            message,
            kind="warning",
        )

    @classmethod
    def error(
        cls,
        parent,
        title: str,
        message: str,
        *,
        details: str | None = None,
    ) -> None:
        cls._show(
            parent,
            title,
            message,
            kind="error",
            details=details,
        )

    @classmethod
    def confirm(
        cls,
        parent,
        title: str,
        message: str,
        *,
        accept_text: str = "Continuar",
        cancel_text: str = "Cancelar",
        destructive: bool = False,
    ) -> bool:
        return cls._show(
            parent,
            title,
            message,
            kind="warning",
            confirm=True,
            accept_text=accept_text,
            cancel_text=cancel_text,
            destructive=destructive,
        )
