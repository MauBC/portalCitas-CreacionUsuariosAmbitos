"""Explicit read-only connectivity checks; never run automatically at startup."""
from app.clients.postgres_client import PostgresClient
from app.clients.sharepoint_client import SharePointClient
from app.config.settings import settings
from app.services.error_report_service import redact_secrets


def check_connections(country, progress):
    results = []
    for name in ("PostgreSQL", "SharePoint"):
        progress(f"Comprobando {name}...")
        try:
            if name == "PostgreSQL":
                PostgresClient(country_code=country).fetch_all("SELECT 1 AS connection_ok")
                detail = "Consulta de conexión completada."
            else:
                client = SharePointClient()
                if country == "SLV":
                    client.get_list_id(settings.SHAREPOINT_LIST_NAME)
                    detail = "Sitio y lista accesibles."
                else:
                    client.get_site_id()
                    detail = "Sitio accesible; no verifica permisos de cada archivo compartido."
            results.append({"name": name, "ok": True, "detail": detail})
        except Exception as exc:
            results.append({"name": name, "ok": False, "detail": redact_secrets(f"{type(exc).__name__}: {exc}")})
    return results
