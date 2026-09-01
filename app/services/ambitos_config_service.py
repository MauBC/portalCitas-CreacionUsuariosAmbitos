import json
import os
import re
import unicodedata


class AmbitosConfigService:

    def __init__(self, config_path: str | None = None):

        if config_path is None:
            config_path = os.path.abspath(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "config",
                    "ambitos_config.json",
                )
            )

        self.config_path = config_path

        with open(
            self.config_path,
            "r",
            encoding="utf-8-sig",
        ) as file:
            self.config = json.load(file)

    # ==========================================================
    # NORMALIZACION
    # ==========================================================

    @staticmethod
    def normalize(value) -> str:

        if value is None:
            return ""

        text = str(value).strip().upper()

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

    # ==========================================================
    # CLIENTES
    # ==========================================================

    def get_country_config(
        self,
        country: str,
    ) -> dict:

        country = self.normalize(country)

        return (
            self.config
            .get("countries", {})
            .get(country, {})
        )

    def get_clients(
        self,
        country: str,
    ) -> dict:

        return (
            self.get_country_config(country)
            .get("clients", {})
        )

    def resolve_alias(
        self,
        country: str,
        value: str,
    ) -> str | None:

        query = self.normalize(value)

        if not query:
            return None

        clients = self.get_clients(country)

        for canonical, config in clients.items():

            candidates = [
                canonical,
                config.get(
                    "db_name",
                    canonical,
                ),
            ]

            candidates.extend(
                config.get(
                    "aliases",
                    []
                )
            )

            for candidate in candidates:

                if self.normalize(candidate) == query:
                    return canonical

        return None

    def get_client_config(
        self,
        country: str,
        client: str,
    ) -> dict | None:

        canonical = (
            self.resolve_alias(
                country,
                client,
            )
            or client
        )

        clients = self.get_clients(country)

        return clients.get(canonical)

    # ==========================================================
    # CONSTRUCCION DE CATALOGOS
    # ==========================================================

    def build_catalogs(
        self,
        country: str,
        client_names: list[str],
    ) -> dict:

        business_rows = []
        sede_rows = []

        business_groups = {}
        sede_groups = {}

        client_business_groups = {}
        client_sede_groups = {}

        business_counter = 1
        sede_counter = 1

        for client_name in client_names:

            canonical = (
                self.resolve_alias(
                    country,
                    client_name,
                )
                or client_name
            )

            client_config = self.get_client_config(
                country,
                canonical,
            )

            if not client_config:
                continue

            client_business_groups.setdefault(
                canonical,
                [],
            )

            client_sede_groups.setdefault(
                canonical,
                [],
            )

            for business in client_config.get(
                "negocios",
                []
            ):

                tipo = str(
                    business.get("tipo") or ""
                ).strip()

                rubro = str(
                    business.get("rubro") or ""
                ).strip()

                business_key = (
                    self.normalize(tipo),
                    self.normalize(rubro),
                )

                if business_key not in business_groups:

                    business_groups[
                        business_key
                    ] = business_counter

                    business_rows.append({
                        "Grupo":
                            business_counter,
                        "Tipo de negocio":
                            tipo,
                        "Rubro":
                            rubro,
                    })

                    business_counter += 1

                negocio_group = business_groups[
                    business_key
                ]

                if negocio_group not in client_business_groups[
                    canonical
                ]:
                    client_business_groups[
                        canonical
                    ].append(
                        negocio_group
                    )

                for sede in business.get(
                    "sedes",
                    []
                ):

                    sede = str(
                        sede
                    ).strip()

                    sede_key = (
                        self.normalize(sede),
                        self.normalize(tipo),
                    )

                    if sede_key not in sede_groups:

                        sede_groups[
                            sede_key
                        ] = sede_counter

                        sede_rows.append({
                            "Grupo":
                                sede_counter,
                            "Sede":
                                sede,
                            "Tipo de negocio":
                                tipo,
                        })

                        sede_counter += 1

                    sede_group = sede_groups[
                        sede_key
                    ]

                    if sede_group not in client_sede_groups[
                        canonical
                    ]:
                        client_sede_groups[
                            canonical
                        ].append(
                            sede_group
                        )

        return {
            "tipo_negocio_nuevo":
                business_rows,

            "sede_nueva":
                sede_rows,

            "client_business_groups":
                client_business_groups,

            "client_sede_groups":
                client_sede_groups,
        }
