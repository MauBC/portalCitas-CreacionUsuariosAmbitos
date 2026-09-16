"""Persistent GUI error reports, independent of widgets and console availability."""

from datetime import datetime
import os
import re

from app.config.paths import create_run_folder


def redact_secrets(text: str) -> str:
    """Remove configured credentials and common credential fields from diagnostics."""
    result = str(text)
    for name in ("MS_CLIENT_SECRET", "DB_PASSWORD"):
        value = os.getenv(name)
        if value:
            result = result.replace(value, "[REDACTED]")
    result = re.sub(
        r"(?i)(bearer\s+)[^\s\"']+",
        r"\1[REDACTED]",
        result,
    )
    return re.sub(
        r"(?i)(\b(?:password|client_secret|access_token|refresh_token)"
        r"[\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s&,;]+)",
        r"\1[REDACTED]",
        result,
    )


def build_error_details(
    *,
    phase: str,
    country: str,
    mode: str,
    error_detail: str,
    full_trace: str,
) -> str:
    """Save a report and return displayable details; disk errors never hide the failure."""
    report = redact_secrets(
        f"Fecha: {datetime.now().isoformat(timespec='seconds')}\n"
        f"Fase: {phase}\nPais: {country}\nModo: {mode}\n"
        f"Error: {error_detail}\n\n{full_trace}"
    )
    try:
        folder = create_run_folder("error_gui")
        path = folder / "error.log"
        path.write_text(report, encoding="utf-8")
    except OSError:
        return f"No se pudo guardar el log. Conserva este detalle:\n\n{report}"
    return f"Log guardado en: {path}\n\n{report}"
