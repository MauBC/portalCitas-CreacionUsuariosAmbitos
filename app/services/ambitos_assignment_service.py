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
            []
        )

        clients = []

        provider_clients = defaultdict(set)

        for relation in relations:

            client = relation.get(
                "cliente_bd"
            ) or {}

            client_name = str(
                client.get("name") or ""
            ).strip()

            provider_ruc = str(
                relation.get(
                    "proveedor_ruc"
                )
                or ""
            ).strip()

            if client_name:

                canonical = (
                    self.config.resolve_alias(
                        country,
                        client_name,
                    )
                    or client_name
                )

                if canonical not in clients:
                    clients.append(canonical)

                if provider_ruc:
                    provider_clients[
                        provider_ruc
                    ].add(canonical)

        catalogs = self.config.build_catalogs(
            country=country,
            client_names=clients,
        )

        business_groups = catalogs[
            "client_business_groups"
        ]

        sede_groups = catalogs[
            "client_sede_groups"
        ]

        # ======================================================
        # ENTIDADES
        # ======================================================

        for entity in result.get(
            "entidades",
            []
        ):

            entity_type = str(
                entity.get(
                    "Tipo Usuario"
                )
                or ""
            ).strip().upper()

            entity_ruc = str(
                entity.get("RUC")
                or ""
            ).strip()

            related_clients = set()

            if entity_type == "CLIENTE":

                name = str(
                    entity.get(
                        "Razon Social"
                    )
                    or ""
                ).strip()

                canonical = (
                    self.config.resolve_alias(
                        country,
                        name,
                    )
                    or name
                )

                related_clients.add(
                    canonical
                )

            elif entity_type == "PROVEEDOR":

                related_clients.update(
                    provider_clients.get(
                        entity_ruc,
                        set(),
                    )
                )

            groups = set()

            for client in related_clients:

                groups.update(
                    business_groups.get(
                        client,
                        []
                    )
                )

            entity[
                "Tipo de negocio Nuevo"
            ] = self._format_groups(
                groups
            )

        # ======================================================
        # AMBITOS
        # ======================================================

        for ambito in result.get(
            "ambitos",
            []
        ):

            provider_ruc = str(
                ambito.get(
                    "Empresa"
                )
                or ""
            ).strip()

            related_clients = (
                provider_clients.get(
                    provider_ruc,
                    set(),
                )
            )

            groups = set()

            for client in related_clients:

                groups.update(
                    sede_groups.get(
                        client,
                        []
                    )
                )

            ambito[
                "Sedes Nuevas"
            ] = self._format_groups(
                groups
            )

        result[
            "tipo_negocio_nuevo"
        ] = catalogs[
            "tipo_negocio_nuevo"
        ]

        result[
            "sede_nueva"
        ] = catalogs[
            "sede_nueva"
        ]

        return result

    @staticmethod
    def _format_groups(
        groups,
    ) -> str:

        """
        Centralizamos aqui el formato.

        Actualmente:
            1
            1,2
            1,2,3

        Si el portal exige otro separador,
        solamente se cambia esta funcion.
        """

        clean = sorted({
            int(group)
            for group in groups
        })

        return ",".join(
            str(group)
            for group in clean
        )
