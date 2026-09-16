from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.services.portal_user_result_service import (
    PortalUserResultService,
)
from app.services.provider_creation_status_service import (
    ProviderCreationStatusService,
)


class ProviderPhase2Service:
    MANIFEST_NAME = "usuarios_enviados.xlsx"
    NORMALIZED_NAME = "excel_proveedores_normalizado.xlsx"

    def __init__(self):
        self.portal_service = PortalUserResultService()
        self.creation_status = ProviderCreationStatusService()

    def preview(
        self,
        run_folder: str,
        portal_error_excel: str,
    ) -> dict:
        folder = Path(run_folder)

        if not folder.is_dir():
            raise FileNotFoundError(
                f"No existe carpeta de ejecucion: {folder}"
            )

        manifest_path = (
            folder
            / self.MANIFEST_NAME
        )

        normalized_path = (
            folder
            / self.NORMALIZED_NAME
        )

        portal_path = Path(
            portal_error_excel
        )

        if not manifest_path.is_file():
            raise FileNotFoundError(
                f"No existe manifiesto: {manifest_path}"
            )

        if not normalized_path.is_file():
            raise FileNotFoundError(
                "No existe normalizado de proveedores: "
                f"{normalized_path}"
            )

        if not portal_path.is_file():
            raise FileNotFoundError(
                f"No existe resultado del portal: {portal_path}"
            )

        sent_users = pd.read_excel(
            manifest_path,
            dtype=str,
            keep_default_na=False,
        )

        account_results = (
            self.portal_service.process(
                sent_users=sent_users,
                error_excel_path=
                    str(portal_path),
            )
        )

        normalized = pd.read_excel(
            normalized_path,
            dtype=str,
            keep_default_na=False,
        )

        relation_results = (
            self._build_relation_results(
                normalized=normalized,
                account_results=
                    account_results,
            )
        )

        summary = self._summarize(
            account_results=
                account_results,
            relation_results=
                relation_results,
        )

        return {
            "account_results":
                account_results,
            "relation_results":
                relation_results,
            "summary":
                summary,
            "manifest_path":
                str(
                    manifest_path.resolve()
                ),
            "normalized_path":
                str(
                    normalized_path.resolve()
                ),
        }

    def export_evidence(
        self,
        run_folder: str,
        preview: dict,
    ) -> str:
        folder = Path(run_folder)

        path = (
            folder
            / "fase2_PER_resultado_PREVIEW.xlsx"
        )

        summary_rows = [
            {
                "METRICA": key,
                "VALOR": value,
            }
            for key, value
            in preview[
                "summary"
            ].items()
        ]

        accounts = (
            preview[
                "account_results"
            ].copy()
        )

        relations = (
            preview[
                "relation_results"
            ].copy()
        )

        with pd.ExcelWriter(
            path,
            engine="openpyxl",
        ) as writer:
            pd.DataFrame(
                summary_rows
            ).to_excel(
                writer,
                sheet_name="RESUMEN",
                index=False,
            )

            accounts.to_excel(
                writer,
                sheet_name="CUENTAS_PORTAL",
                index=False,
            )

            relations.to_excel(
                writer,
                sheet_name="RELACIONES",
                index=False,
            )

        return str(
            path.resolve()
        )

    def _build_relation_results(
        self,
        normalized: pd.DataFrame,
        account_results: pd.DataFrame,
    ) -> pd.DataFrame:
        required = {
            "_item_id",
            "email",
            "estado",
            "creado",
        }

        missing = (
            required
            - set(
                normalized.columns
            )
        )

        if missing:
            raise ValueError(
                "Faltan columnas en normalizado: "
                f"{sorted(missing)}"
            )

        account_map = {}

        for _, account in (
            account_results.iterrows()
        ):
            email = (
                self._normalize_email(
                    account.get("email")
                )
            )

            if not email:
                continue

            desired = (
                self._normalize_result_status(
                    account.get("creado")
                )
            )

            if desired not in {
                1,
                2,
            }:
                raise ValueError(
                    "Resultado de cuenta invalido "
                    f"para {email}: "
                    f"{account.get('creado')}"
                )

            previous = (
                account_map.get(
                    email
                )
            )

            if (
                previous
                and previous[
                    "creado"
                ] != desired
            ):
                raise ValueError(
                    "Resultados contradictorios "
                    f"para el correo {email}."
                )

            account_map[email] = {
                "creado":
                    desired,
                "estado_portal":
                    str(
                        account.get(
                            "estado_portal"
                        )
                        or ""
                    ).strip(),
                "mensaje_error":
                    str(
                        account.get(
                            "mensaje_error"
                        )
                        or ""
                    ).strip(),
            }

        rows = []

        for _, row in (
            normalized.iterrows()
        ):
            record = row.to_dict()

            item_id = str(
                row.get("_item_id")
                or ""
            ).strip()

            email = (
                self._normalize_email(
                    row.get("email")
                )
            )

            phase1_state = (
                str(
                    row.get("estado")
                    or ""
                )
                .strip()
                .upper()
            )

            current = (
                self.creation_status
                .normalize(
                    row.get("creado")
                )
            )

            desired = None
            phase2_state = ""
            origin = ""
            message = ""

            if phase1_state == "OK":
                account = (
                    account_map.get(
                        email
                    )
                )

                if not email:
                    phase2_state = (
                        "SIN_CORREO"
                    )
                    origin = (
                        "ERROR_INTERNO"
                    )

                elif account is None:
                    phase2_state = (
                        "SIN_RESULTADO_PORTAL"
                    )
                    origin = (
                        "ERROR_INTERNO"
                    )

                else:
                    desired = (
                        account["creado"]
                    )
                    phase2_state = (
                        account[
                            "estado_portal"
                        ]
                        or (
                            "DISPONIBLE"
                            if desired == 1
                            else "NO_CREADO"
                        )
                    )
                    origin = "PORTAL"
                    message = (
                        account[
                            "mensaje_error"
                        ]
                    )

            elif phase1_state == "ERROR":
                desired = 2
                phase2_state = (
                    "NO_ENVIADO"
                )
                origin = (
                    "VALIDACION_LOCAL"
                )
                message = str(
                    row.get(
                        "observaciones"
                    )
                    or ""
                ).strip()

            elif phase1_state == "OMITIDO":
                if current in {
                    1,
                    2,
                }:
                    desired = current
                    phase2_state = (
                        "YA_CERRADO"
                    )
                    origin = (
                        "ESTADO_PREVIO"
                    )
                else:
                    phase2_state = (
                        "OMITIDO_SIN_ESTADO"
                    )
                    origin = (
                        "ERROR_INTERNO"
                    )

            else:
                phase2_state = (
                    "ESTADO_FASE1_DESCONOCIDO"
                )
                origin = (
                    "ERROR_INTERNO"
                )

            record.update({
                "_item_id":
                    item_id,
                "email":
                    email,
                "creado_fase1":
                    (
                        current
                        if current is not None
                        else ""
                    ),
                "creado_objetivo":
                    (
                        desired
                        if desired is not None
                        else ""
                    ),
                "estado_fase2":
                    phase2_state,
                "origen_fase2":
                    origin,
                "mensaje_fase2":
                    message,
            })

            rows.append(
                record
            )

        return pd.DataFrame(
            rows
        )

    @staticmethod
    def _summarize(
        account_results: pd.DataFrame,
        relation_results: pd.DataFrame,
    ) -> dict:
        account_created = (
            pd.to_numeric(
                account_results.get(
                    "creado",
                    pd.Series(
                        dtype=int
                    ),
                ),
                errors="coerce",
            )
        )

        relation_target = (
            pd.to_numeric(
                relation_results.get(
                    "creado_objetivo",
                    pd.Series(
                        dtype=int
                    ),
                ),
                errors="coerce",
            )
        )

        phase1_state = (
            relation_results.get(
                "estado",
                pd.Series(
                    dtype=str
                ),
            )
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        unresolved = int(
            relation_target.isna().sum()
        )

        return {
            "cuentas_enviadas":
                len(account_results),
            "cuentas_disponibles":
                int(
                    account_created
                    .eq(1)
                    .sum()
                ),
            "cuentas_no_creadas":
                int(
                    account_created
                    .eq(2)
                    .sum()
                ),
            "relaciones_total":
                len(
                    relation_results
                ),
            "relaciones_validas_fase1":
                int(
                    phase1_state
                    .eq("OK")
                    .sum()
                ),
            "relaciones_creado_1":
                int(
                    relation_target
                    .eq(1)
                    .sum()
                ),
            "relaciones_creado_2":
                int(
                    relation_target
                    .eq(2)
                    .sum()
                ),
            "relaciones_sin_resultado":
                unresolved,
        }

    @staticmethod
    def _normalize_email(
        value,
    ) -> str:
        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (
            TypeError,
            ValueError,
        ):
            pass

        return (
            str(value)
            .strip()
            .lower()
            .replace(" ", "")
        )

    @staticmethod
    def _normalize_result_status(
        value,
    ):
        try:
            numeric = float(
                str(value).strip()
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

        if not numeric.is_integer():
            return None

        return int(
            numeric
        )
