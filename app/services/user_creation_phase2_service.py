import glob
import os
import pandas as pd

from app.services.portal_user_result_service import PortalUserResultService


class UserCreationPhase2Service:

    def __init__(self):
        self.portal_service = PortalUserResultService()

    def preview(
        self,
        run_folder: str,
        portal_error_excel: str,
    ) -> pd.DataFrame:

        manifest_path = os.path.join(
            run_folder,
            "usuarios_enviados.xlsx"
        )

        if not os.path.exists(manifest_path):
            raise FileNotFoundError(
                f"No existe manifiesto: {manifest_path}"
            )

        sent_users = pd.read_excel(
            manifest_path,
            dtype=str
        )

        # Resultado de usuarios que SI fueron enviados al portal
        portal_result = self.portal_service.process(
            sent_users=sent_users,
            error_excel_path=portal_error_excel,
        )

        portal_result["origen"] = "PORTAL"

        # -----------------------------------------------------
        # Usuarios rechazados antes de llegar al portal
        # -----------------------------------------------------

        error_files = glob.glob(
            os.path.join(
                run_folder,
                "reporte_ERRORES_*.xlsx"
            )
        )

        local_results = []

        if error_files:

            error_files.sort(
                key=os.path.getmtime,
                reverse=True
            )

            local_error_path = error_files[0]

            # Los reportes nuevos guardan toda la informacion
            # necesaria para procesamiento en DATOS_TECNICOS.
            #
            # Se conserva compatibilidad con reportes antiguos
            # que utilizaban la hoja ERRORES.

            workbook = pd.ExcelFile(
                local_error_path
            )

            if "DATOS_TECNICOS" in workbook.sheet_names:
                sheet_name = "DATOS_TECNICOS"

            elif "ERRORES" in workbook.sheet_names:
                sheet_name = "ERRORES"

            else:
                sheet_name = workbook.sheet_names[0]

            local_errors = pd.read_excel(
                local_error_path,
                sheet_name=sheet_name,
                dtype=str
            )

            for _, row in local_errors.iterrows():

                item_id = str(
                    row.get("_item_id") or ""
                ).strip()

                email = str(
                    row.get("email") or ""
                ).strip().lower()

                mensaje = str(
                    row.get("observaciones") or ""
                ).strip()

                if not item_id:
                    continue

                local_results.append({
                    "_item_id": item_id,
                    "email": email,
                    "creado": 2,
                    "mensaje_error": mensaje,
                    "origen": "VALIDACION_LOCAL",
                })

        if local_results:

            local_df = pd.DataFrame(
                local_results
            )

            final = pd.concat(
                [
                    portal_result,
                    local_df,
                ],
                ignore_index=True
            )

        else:
            final = portal_result.copy()

        final["_item_id"] = (
            final["_item_id"]
            .astype(str)
            .str.strip()
        )

        return final

