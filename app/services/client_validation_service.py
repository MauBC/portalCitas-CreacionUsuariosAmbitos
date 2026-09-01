import pandas as pd

from app.config.portal_template_config import (
    COUNTRY_TEMPLATE_CONFIG
)

from app.services.client_assignment_service import (
    ClientAssignmentService
)


class ClientValidationService:

    def __init__(self):

        self.assignment = (
            ClientAssignmentService()
        )

    @staticmethod
    def _clean(value):

        if pd.isna(value):
            return ""

        return str(value).strip()

    @staticmethod
    def _append_observation(
        current,
        new_message,
    ):

        current = ClientValidationService._clean(
            current
        )

        if not current:
            return new_message

        return f"{current} | {new_message}"

    def validate_dataframe(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        result = df.copy()

        columns = {
            "cliente_original": "",
            "cliente_normalizado": "",
            "cliente_candidato": "",
            "cliente_confianza": 0.0,
            "cliente_metodo": "",
            "cliente_estado": "",
            "cliente_observacion": "",
            "requiere_revision_cliente": False,
        }

        for column, default in columns.items():

            if column not in result.columns:
                result[column] = default

        for index, row in result.iterrows():

            country = self._clean(
                row.get("pais")
            ).upper()

            raw_client = self._clean(
                row.get("nombre_cliente")
            )

            country_config = (
                COUNTRY_TEMPLATE_CONFIG.get(
                    country,
                    {}
                )
            )

            details = (
                self.assignment.resolve_with_details(
                    row=row,
                    country_config=country_config,
                )
            )

            result.at[
                index,
                "cliente_original"
            ] = raw_client

            result.at[
                index,
                "cliente_normalizado"
            ] = details[
                "resolved_client"
            ]

            result.at[
                index,
                "cliente_candidato"
            ] = details[
                "candidate_client"
            ]

            result.at[
                index,
                "cliente_confianza"
            ] = details[
                "score"
            ]

            result.at[
                index,
                "cliente_metodo"
            ] = details[
                "method"
            ]

            result.at[
                index,
                "cliente_estado"
            ] = details[
                "status"
            ]

            result.at[
                index,
                "cliente_observacion"
            ] = details[
                "reason"
            ]

            requires_review = (
                details["status"]
                != "OK"
            )

            result.at[
                index,
                "requiere_revision_cliente"
            ] = requires_review

            # ==================================================
            # CLIENTE RESUELTO
            # ==================================================

            if not requires_review:

                resolved = details[
                    "resolved_client"
                ]

                if resolved:
                    result.at[
                        index,
                        "nombre_cliente"
                    ] = resolved

                continue

            # ==================================================
            # CLIENTE NO RESUELTO
            # ==================================================

            # Solo convertimos en ERROR cuando existe
            # un catálogo de clientes para ese país.
            has_catalog = bool(
                self.assignment
                .ambitos_config
                .get_clients(country)
            )

            if not has_catalog:
                continue

            current_state = self._clean(
                row.get("estado")
            ).upper()

            result.at[
                index,
                "estado"
            ] = "ERROR"

            message = (
                "CLIENTE REQUIERE REVISION: "
                + details["reason"]
            )

            result.at[
                index,
                "observaciones"
            ] = self._append_observation(
                row.get("observaciones"),
                message,
            )

        return result
