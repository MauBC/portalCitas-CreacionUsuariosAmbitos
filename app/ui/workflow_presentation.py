"""Shared labels for the session overview and sidebar."""
STEPS = ((1, "Usuarios", "users"), (2, "Fase 2", "phase2"), (3, "Ámbitos", "ambitos"))
STATUS_LABELS = {"pending": "Pendiente", "action": "Requiere atención", "done": "Completada"}
STATUS_SYMBOLS = {"pending": "○", "action": "!", "done": "✓"}


def normalize_status(value) -> str:
    normalized = str(value or "pending").strip().lower()
    return normalized if normalized in STATUS_LABELS else "pending"
