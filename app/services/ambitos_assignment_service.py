from collections import defaultdict

from app.services.ambitos_config_service import (
    AmbitosConfigService
)


class AmbitosAssignmentService:

    def __init__(self):
        self.config = AmbitosConfigService()

    def enrich(
        self,
        result: dict,
        country: str,
    ) -> dict:
        relations = result.get(
            "matched_relations",
            [],
        )

        provider_clients = defaultdict(set)
        account_clients = defaultdict(set)

        for relation in relations:
            client = relation.get(
                "cliente_bd"
            ) or {}

            client_name = str(
                client.get("name")
                or ""
            ).strip()

            provider_ruc = str(
                relation.get(
                    "proveedor_ruc"
                )
                or ""
            ).strip()

            provider_email = str(
                relation.get(
                    "proveedor_email"
                )
                or ""
            ).strip().lower()

            client_item = (
                self.config.get_client_config(
                    country,
                    client_name,
                )
            )

            if not client_item:
                continue

            canonical = client_item[
                "canonical"
            ]

            if provider_ruc:
                provider_clients[
                    provider_ruc
                ].add(canonical)

            if (
                provider_email
                and provider_ruc
            ):
                account_clients[
                    (
                        provider_email,
                        provider_ruc,
                    )
                ].add(canonical)

        for entity in result.get(
            "entidades",
            [],
        ):
            entity_type = str(
                entity.get("_entity_type")
                or entity.get("Tipo Usuario")
                or ""
            ).strip().upper()

            entity_ruc = str(
                entity.get("RUC")
                or ""
            ).strip()

            if entity_type == "PROVEEDOR":
                groups = set()

                for client_name in (
                    provider_clients.get(
                        entity_ruc,
                        set(),
                    )
                ):
                    group = (
                        self.config
                        .get_business_group(
                            country,
                            client_name,
                        )
                    )

                    if group is not None:
                        groups.add(group)

                entity[
                    "Tipo de negocio Nuevo"
                ] = self._format_groups(
                    groups
                )

            elif entity_type == "CLIENTE":
                name = str(
                    entity.get(
                        "Razon Social"
                    )
                    or ""
                ).strip()

                group = (
                    self.config
                    .get_relation_group(
                        country,
                        name,
                    )
                )

                entity[
                    "Relacion Nueva"
                ] = (
                    group
                    if group is not None
                    else ""
                )

                entity[
                    "Tipo de negocio Nuevo"
                ] = ""

        for ambito in result.get(
            "ambitos",
            [],
        ):
            email = str(
                ambito.get("Email")
                or ""
            ).strip().lower()

            provider_ruc = str(
                ambito.get("Empresa")
                or ""
            ).strip()

            related_clients = (
                account_clients.get(
                    (
                        email,
                        provider_ruc,
                    ),
                    set(),
                )
            )

            groups = set()

            for client_name in related_clients:
                group = (
                    self.config
                    .get_sede_group(
                        country,
                        client_name,
                    )
                )

                if group is not None:
                    groups.add(group)

            ambito[
                "Sedes Nuevas"
            ] = self._format_groups(
                groups
            )

        result[
            "tipo_negocio_nuevo"
        ] = (
            self.config
            .get_tipo_negocio_rows()
        )

        result[
            "sede_nueva"
        ] = (
            self.config
            .get_sede_rows(
                country
            )
        )

        return result

    @staticmethod
    def _format_groups(
        groups,
    ) -> str:
        clean = sorted({
            int(group)
            for group in groups
            if group is not None
            and str(group).strip() != ""
        })

        return ",".join(
            str(group)
            for group in clean
        )
