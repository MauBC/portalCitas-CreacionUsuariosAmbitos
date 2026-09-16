import glob
import os

import pandas as pd

from app.services.portal_user_result_service import (
    PortalUserResultService,
)


class UserCreationPhase2Service:

    def __init__(self):
        self.portal_service = (
            PortalUserResultService()
        )

    def preview(
        self,
        run_folder: str,
        portal_error_excel: str,
    ) -> pd.DataFrame:

        manifest_path = os.path.join(
            run_folder,
            "usuarios_enviados.xlsx",
        )

        if not os.path.exists(
            manifest_path
        ):
            raise FileNotFoundError(
                f"No existe manifiesto: "
                f"{manifest_path}"
            )

        sent_users = pd.read_excel(
            manifest_path,
            dtype=str,
        )

        portal_result = (
            self.portal_service.process(
                sent_users=sent_users,
                error_excel_path=portal_error_excel,
            )
        )

        portal_result["origen"] = (
            "PORTAL"
        )

        portal_result = (
            self._enrich_portal_result(
                portal_result=portal_result,
                run_folder=run_folder,
            )
        )

        local_errors = (
            self._load_local_errors(
                run_folder
            )
        )

        if not local_errors.empty:

            final = pd.concat(
                [
                    portal_result,
                    local_errors,
                ],
                ignore_index=True,
                sort=False,
            )

        else:

            final = (
                portal_result.copy()
            )

        final["_item_id"] = (
            final["_item_id"]
            .astype(str)
            .str.strip()
        )

        final["email"] = (
            final["email"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        return final

    def _enrich_portal_result(
        self,
        portal_result,
        run_folder,
    ):

        valid_files = glob.glob(
            os.path.join(
                run_folder,
                "reporte_VALIDOS_*.xlsx",
            )
        )

        if not valid_files:
            return portal_result

        valid_files.sort(
            key=os.path.getmtime,
            reverse=True,
        )

        valid_path = (
            valid_files[0]
        )

        with pd.ExcelFile(valid_path) as workbook:
            if "DATOS_TECNICOS" not in workbook.sheet_names:
                return portal_result

            source = pd.read_excel(
                workbook,
                sheet_name="DATOS_TECNICOS",
                dtype=str,
            )

        if (
            "_item_id"
            not in source.columns
        ):
            return portal_result

        source["_item_id"] = (
            source["_item_id"]
            .astype(str)
            .str.strip()
        )

        extra_columns = [
            column
            for column in source.columns
            if (
                column not in portal_result.columns
                and column != "_item_id"
            )
        ]

        if not extra_columns:
            return portal_result

        source = source[
            [
                "_item_id",
                *extra_columns,
            ]
        ].drop_duplicates(
            subset=["_item_id"]
        )

        return portal_result.merge(
            source,
            on="_item_id",
            how="left",
        )

    def _load_local_errors(
        self,
        run_folder,
    ):

        error_files = glob.glob(
            os.path.join(
                run_folder,
                "reporte_ERRORES_*.xlsx",
            )
        )

        if not error_files:
            return pd.DataFrame()

        error_files.sort(
            key=os.path.getmtime,
            reverse=True,
        )

        path = error_files[0]

        with pd.ExcelFile(path) as workbook:
            if "DATOS_TECNICOS" in workbook.sheet_names:
                sheet_name = "DATOS_TECNICOS"
            elif "ERRORES" in workbook.sheet_names:
                sheet_name = "ERRORES"
            else:
                sheet_name = workbook.sheet_names[0]

            source = pd.read_excel(
                workbook,
                sheet_name=sheet_name,
                dtype=str,
            )

        rows = []

        for _, row in source.iterrows():

            item_id = str(
                row.get("_item_id") or ""
            ).strip()

            if not item_id:
                continue

            record = row.to_dict()

            record.update({
                "_item_id":
                    item_id,
                "email":
                    str(
                        row.get("email") or ""
                    ).strip().lower(),
                "creado":
                    2,
                "estado_portal":
                    "NO_ENVIADO",
                "mensaje_error":
                    str(
                        row.get(
                            "observaciones"
                        )
                        or ""
                    ).strip(),
                "origen":
                    "VALIDACION_LOCAL",
            })

            rows.append(
                record
            )

        return pd.DataFrame(
            rows
        )
