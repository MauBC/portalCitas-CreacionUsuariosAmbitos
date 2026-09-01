import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MS_TENANT_ID = os.getenv("MS_TENANT_ID", "").strip()
    MS_CLIENT_ID = os.getenv("MS_CLIENT_ID", "").strip()
    MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "").strip()
    MS_GRAPH_SCOPE = os.getenv("MS_GRAPH_SCOPE", "").strip()

    SHAREPOINT_HOSTNAME = os.getenv("SHAREPOINT_HOSTNAME", "").strip()
    SHAREPOINT_SITE_PATH = os.getenv("SHAREPOINT_SITE_PATH", "").strip()
    SHAREPOINT_LIST_NAME = os.getenv("SHAREPOINT_LIST_NAME", "").strip()

    DB_HOST = os.getenv("DB_HOST", "").strip()
    DB_PORT = os.getenv("DB_PORT", "").strip()
    DB_NAME = os.getenv("DB_NAME", "").strip()
    DB_USER = os.getenv("DB_USER", "").strip()
    DB_PASSWORD = os.getenv("DB_PASSWORD", "").strip()
    DB_SCHEMA = os.getenv("DB_SCHEMA", "").strip()
    DB_SSLMODE = os.getenv("DB_SSLMODE", "").strip()

    FILTER_ONLY_PENDING_SHAREPOINT = os.getenv("FILTER_ONLY_PENDING_SHAREPOINT", "True").strip().lower() == "true"
    VALIDATE_EMAIL_EXISTS_IN_DB = os.getenv("VALIDATE_EMAIL_EXISTS_IN_DB", "true").strip().lower() == "true"

settings = Settings()

# Nombre interno de la lista SharePoint
SHAREPOINT_LIST_NAME = os.getenv(
    "SHAREPOINT_LIST_NAME",
    ""
).strip()

