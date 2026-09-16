from pathlib import Path
import json
import re
import unicodedata

from app.config.paths import CONFIG_ROOT


class AmbitosConfigService:

    def __init__(
        self,
        config_path=None,
    ):
        self.config_path = Path(
            config_path
            or CONFIG_ROOT
            / "ambitos_config.json"
        )

        self.config = self._load()

    def _load(self) -> dict:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"No existe configuracion: "
                f"{self.config_path}"
            )

        with self.config_path.open(
            "r",
            encoding="utf-8-sig",
        ) as file:
            return json.load(file)

    def get_country_clients(
        self,
        country_code: str,
    ) -> dict:
        country_code = self._normalize(
            country_code
        )

        return (
            self.config
            .get("countries", {})
            .get(country_code, {})
            .get("clients", {})
        )

    def get_clients(
        self,
        country_code: str,
    ) -> dict:
        return self.get_country_clients(
            country_code
        )

    def normalize(
        self,
        value,
    ) -> str:
        return self._normalize_alias(
            value
        )

    def resolve_alias(
        self,
        country_code: str,
        value,
    ):
        target = self._normalize_alias(
            value
        )

        if not target:
            return None

        clients = self.get_country_clients(
            country_code
        )

        for canonical, config in clients.items():
            candidates = [
                canonical,
                config.get("db_name"),
                *config.get("aliases", []),
            ]

            for candidate in candidates:
                if (
                    self._normalize_alias(
                        candidate
                    )
                    == target
                ):
                    return canonical

        return None

    def get_client_config(
        self,
        country_code: str,
        value,
    ):
        canonical = self.resolve_alias(
            country_code,
            value,
        )

        if canonical:
            config = (
                self.get_country_clients(
                    country_code
                )
                .get(canonical)
            )

            if config:
                return {
                    "canonical": canonical,
                    "config": config,
                }

        target = self._normalize_alias(
            value
        )

        for canonical, config in (
            self.get_country_clients(
                country_code
            ).items()
        ):
            db_name = (
                config.get("db_name")
                or canonical
            )

            if (
                self._normalize_alias(
                    db_name
                )
                == target
            ):
                return {
                    "canonical": canonical,
                    "config": config,
                }

        return None

    def get_client_names(
        self,
        country_code: str,
    ) -> list[str]:
        return list(
            self.get_country_clients(
                country_code
            ).keys()
        )

    def get_tipo_negocio_rows(
        self,
    ) -> list[dict]:
        rows = (
            self.config
            .get("catalogos", {})
            .get(
                "tipo_negocio_nuevo",
                [],
            )
        )

        return [
            dict(row)
            for row in rows
        ]

    def get_sede_rows(
        self,
        country_code: str,
    ) -> list[dict]:
        rows = []

        for _, config in (
            self.get_country_clients(
                country_code
            ).items()
        ):
            sede_group = config.get(
                "sede_group"
            )

            sede = config.get(
                "sede"
            )

            tipo = config.get(
                "sede_tipo_negocio"
            )

            if (
                sede_group is not None
                and sede
                and tipo
            ):
                rows.append({
                    "Grupo": int(sede_group),
                    "Sede": str(sede).strip(),
                    "Tipo de negocio":
                        str(tipo).strip(),
                })

        return sorted(
            rows,
            key=lambda row: row["Grupo"],
        )

    def get_relation_group(
        self,
        country_code: str,
        client_name,
    ):
        item = self.get_client_config(
            country_code,
            client_name,
        )

        if not item:
            return None

        value = item["config"].get(
            "relation_group"
        )

        return (
            int(value)
            if value is not None
            else None
        )

    def get_business_group(
        self,
        country_code: str,
        client_name,
    ):
        item = self.get_client_config(
            country_code,
            client_name,
        )

        if not item:
            return None

        value = item["config"].get(
            "tipo_negocio_group"
        )

        return (
            int(value)
            if value is not None
            else None
        )

    def get_sede_group(
        self,
        country_code: str,
        client_name,
    ):
        item = self.get_client_config(
            country_code,
            client_name,
        )

        if not item:
            return None

        value = item["config"].get(
            "sede_group"
        )

        return (
            int(value)
            if value is not None
            else None
        )

    @staticmethod
    def _normalize_alias(
        value,
    ) -> str:
        text = str(
            value or ""
        ).strip().upper()

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = "".join(
            char
            for char in text
            if not unicodedata.combining(char)
        )

        text = re.sub(
            r"[^A-Z0-9]+",
            " ",
            text,
        )

        return " ".join(
            text.split()
        )

    @staticmethod
    def _normalize(value) -> str:
        return " ".join(
            str(value or "")
            .strip()
            .upper()
            .split()
        )
