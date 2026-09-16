import os

from app.config.env_loader import load_env


# Pure services can run without .env; entrypoints enforce it when required.
load_env(required=False)


class Settings:
    MS_TENANT_ID = os.getenv(
        "MS_TENANT_ID",
        "",
    ).strip()

    MS_CLIENT_ID = os.getenv(
        "MS_CLIENT_ID",
        "",
    ).strip()

    MS_CLIENT_SECRET = os.getenv(
        "MS_CLIENT_SECRET",
        "",
    ).strip()

    MS_GRAPH_SCOPE = os.getenv(
        "MS_GRAPH_SCOPE",
        "",
    ).strip()

    SHAREPOINT_HOSTNAME = os.getenv(
        "SHAREPOINT_HOSTNAME",
        "",
    ).strip()

    SHAREPOINT_SITE_PATH = os.getenv(
        "SHAREPOINT_SITE_PATH",
        "",
    ).strip()

    SHAREPOINT_LIST_NAME = os.getenv(
        "SHAREPOINT_LIST_NAME",
        "",
    ).strip()

    DB_HOST = os.getenv(
        "DB_HOST",
        "",
    ).strip()

    DB_PORT = os.getenv(
        "DB_PORT",
        "",
    ).strip()

    DB_NAME = os.getenv(
        "DB_NAME",
        "",
    ).strip()

    DB_PER_NAME = os.getenv(
        "DB_PER_NAME",
        DB_NAME,
    ).strip()

    DB_SLV_NAME = os.getenv(
        "DB_SLV_NAME",
        DB_NAME,
    ).strip()

    DB_USER = os.getenv(
        "DB_USER",
        "",
    ).strip()

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        "",
    ).strip()

    DB_SCHEMA = os.getenv(
        "DB_SCHEMA",
        "",
    ).strip()

    DB_SSLMODE = os.getenv(
        "DB_SSLMODE",
        "",
    ).strip()

    FILTER_ONLY_PENDING_SHAREPOINT = (
        os.getenv(
            "FILTER_ONLY_PENDING_SHAREPOINT",
            "True",
        )
        .strip()
        .lower()
        == "true"
    )

    VALIDATE_EMAIL_EXISTS_IN_DB = (
        os.getenv(
            "VALIDATE_EMAIL_EXISTS_IN_DB",
            "true",
        )
        .strip()
        .lower()
        == "true"
    )

    @classmethod
    def get_db_name(
        cls,
        country_code: str | None = None,
    ) -> str:
        country = str(
            country_code or ""
        ).strip().upper()

        database_by_country = {
            "PER":
                cls.DB_PER_NAME,
            "SLV":
                cls.DB_SLV_NAME,
        }

        database = (
            database_by_country.get(
                country
            )
            or cls.DB_NAME
        )

        if not database:
            if country:
                raise ValueError(
                    "No existe base de datos "
                    f"configurada para {country}."
                )

            raise ValueError(
                "No existe DB_NAME configurado."
            )

        return database


settings = Settings()
