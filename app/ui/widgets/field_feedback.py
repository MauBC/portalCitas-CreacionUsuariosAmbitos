"""Inline validation styling shared by the workflow pages."""

from PySide6.QtWidgets import QLabel, QWidget


def set_input_state(widget: QWidget, *, invalid: bool = False, valid: bool = False) -> None:
    widget.setProperty("invalid", invalid)
    widget.setProperty("valid", valid)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def set_field_error(widget: QWidget, label: QLabel, message: str) -> None:
    label.setText(message)
    label.show()
    set_input_state(widget, invalid=True)


def clear_field_error(widget: QWidget, label: QLabel, *, mark_valid: bool = False) -> None:
    label.clear()
    label.hide()
    set_input_state(widget, valid=bool(mark_valid))
