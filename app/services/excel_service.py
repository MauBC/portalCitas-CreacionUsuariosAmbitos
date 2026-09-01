import os
from datetime import datetime

import pandas as pd

from app.services.client_assignment_service import ClientAssignmentService
from app.config.portal_template_config import (
    COUNTRY_TEMPLATE_CONFIG,
    USER_TYPE_CONFIG,
    SERVICES_SHEET,
)


class ExcelService:

    USUARIOS_COLUMNS = [
        "NOMBRE",
        "APELLIDO",
        "CORREO",
        "PAIS",
        "PERFIL DE USUARIO",
        "TIPO DE USUARIO",
        "TIPO DE DOCUMENTO IDENTIDAD",
        "DOCUMENTO",
        "SOCIEDAD",
        "CLIENTE",
        "SERVICIO",
    ]

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.client_assignment = ClientAssignmentService()

    # ==========================================================
    # REPORTES DE VALIDACION
    # ==========================================================

    def export_validos_errores(
        self,
        df: pd.DataFrame,
        base_name: str = "reporte",
    ) -> dict:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        validos = df[
            df["estado"] == "OK"
        ].copy()

        errores = df[
            df["estado"] == "ERROR"
        ].copy()

        valid_path = os.path.join(
            self.output_dir,
            f"{base_name}_VALIDOS_{timestamp}.xlsx",
        )

        error_path = os.path.join(
            self.output_dir,
            f"{base_name}_ERRORES_{timestamp}.xlsx",
        )

        self._export_validation_report(
            df=validos,
            path=valid_path,
            summary_sheet="VALIDOS_RESUMEN",
        )

        self._export_validation_report(
            df=errores,
            path=error_path,
            summary_sheet="ERRORES_RESUMEN",
        )

        return {
            "validos": valid_path,
            "errores": error_path,
        }

    def _export_validation_report(
        self,
        df: pd.DataFrame,
        path: str,
        summary_sheet: str,
    ) -> None:

        resumen = self._build_validation_summary(df)

        with pd.ExcelWriter(
            path,
            engine="openpyxl",
        ) as writer:

            # Hoja pensada para revision humana
            resumen.to_excel(
                writer,
                sheet_name=summary_sheet,
                index=False,
            )

            # Hoja completa para auditoria y procesamiento interno.
            #
            # IMPORTANTE:
            # Si en el futuro Gemini genera nuevas columnas,
            # estas apareceran automaticamente aqui.
            df.to_excel(
                writer,
                sheet_name="DATOS_TECNICOS",
                index=False,
            )

    def _build_validation_summary(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        rows = []

        for _, row in df.iterrows():

            rows.append({
                "ID SHAREPOINT":
                    self._first_value(
                        row,
                        "_item_id",
                    ),

                "PAIS":
                    self._first_value(
                        row,
                        "pais",
                    ),

                "NOMBRE":
                    self._first_value(
                        row,
                        "nombre",
                        "nombre_personal",
                    ),

                "APELLIDO":
                    self._summary_apellido(row),

                "CORREO":
                    self._first_value(
                        row,
                        "email",
                        "correo",
                    ),

                "PROVEEDOR":
                    self._first_value(
                        row,
                        "nombre_proveedor",
                        "nombres",
                    ),

                "CLIENTE INGRESADO":
                    self._first_value(
                        row,
                        "nombre_cliente",
                    ),

                # FUTURO GEMINI:
                #
                # Cuando Gemini vuelva a formar parte del flujo,
                # recomendamos guardar su resultado en la columna
                # cliente_normalizado.
                #
                # El reporte ya esta preparado para mostrarla.
                "CLIENTE NORMALIZADO":
                    self._first_value(
                        row,
                        "cliente_normalizado",
                        "cliente_canonico",
                        "cliente_asignado",
                    ),

                "CONFIANZA CLIENTE":
                    self._first_value(
                        row,
                        "cliente_confianza",
                        "confianza_cliente",
                    ),

                "DOCUMENTO ORIGINAL":
                    self._first_value(
                        row,
                        "DUI_personal",
                        "dni",
                        "DNI",
                        "documento",
                    ),

                "DOCUMENTO LIMPIO":
                    self._first_value(
                        row,
                        "numero_documento",
                    ),

                "TELEFONO ORIGINAL":
                    self._first_value(
                        row,
                        "num_celular",
                        "telefono_original",
                    ),

                "TELEFONO LIMPIO":
                    self._first_value(
                        row,
                        "telefono",
                    ),

                "NIT ORIGINAL":
                    self._first_value(
                        row,
                        "nit_empresa",
                        "ruc",
                    ),

                "NIT LIMPIO":
                    self._first_value(
                        row,
                        "nit_proveedor",
                    ),

                "PERFIL":
                    self._first_value(
                        row,
                        "perfil",
                    ),

                "ESTADO":
                    self._first_value(
                        row,
                        "estado",
                    ),

                "ERROR":
                    self._first_value(
                        row,
                        "observaciones",
                    ),
            })

        columns = [
            "ID SHAREPOINT",
            "PAIS",
            "NOMBRE",
            "APELLIDO",
            "CORREO",
            "PROVEEDOR",
            "CLIENTE INGRESADO",
            "CLIENTE NORMALIZADO",
            "CONFIANZA CLIENTE",
            "DOCUMENTO ORIGINAL",
            "DOCUMENTO LIMPIO",
            "TELEFONO ORIGINAL",
            "TELEFONO LIMPIO",
            "NIT ORIGINAL",
            "NIT LIMPIO",
            "PERFIL",
            "ESTADO",
            "ERROR",
        ]

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    def _summary_apellido(self, row) -> str:

        apellido = self._first_value(
            row,
            "apellido",
            "apellido_personal",
        )

        if apellido:
            return apellido

        paterno = self._first_value(
            row,
            "apellido_pat",
        )

        materno = self._first_value(
            row,
            "apellido_mat",
        )

        return " ".join(
            part
            for part in [paterno, materno]
            if part
        )

    # ==========================================================
    # PLANTILLA DEL PORTAL
    # ==========================================================

    def export_template(
        self,
        df_validos: pd.DataFrame,
    ) -> str:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        path = os.path.join(
            self.output_dir,
            f"plantilla_usuarios_{timestamp}.xlsx",
        )

        usuarios = self._build_usuarios_sheet(
            df_validos
        )

        servicios = pd.DataFrame(
            SERVICES_SHEET,
            columns=[
                "SERVICIO",
                "PARAMETRO",
                "GRUPO",
            ],
        )

        with pd.ExcelWriter(
            path,
            engine="openpyxl",
        ) as writer:

            usuarios.to_excel(
                writer,
                sheet_name="USUARIOS",
                index=False,
            )

            servicios.to_excel(
                writer,
                sheet_name="SERVICIOS",
                index=False,
            )

        return path

    # ==========================================================
    # USUARIOS
    # ==========================================================

    def _build_usuarios_sheet(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:

        rows = []

        for _, row in df.iterrows():

            country_code = self._normalize(
                row.get("pais")
            ).upper()

            if not country_code:
                country_code = "PER"

            country_config = COUNTRY_TEMPLATE_CONFIG.get(
                country_code
            )

            if country_config is None:
                raise ValueError(
                    f"No existe configuracion de plantilla "
                    f"para el pais: {country_code}"
                )

            user_profile = self._normalize(
                row.get("perfil")
            ).upper()

            if not user_profile:
                user_profile = "PROVEEDOR"

            type_config = USER_TYPE_CONFIG.get(
                user_profile
            )

            if type_config is None:
                raise ValueError(
                    f"Tipo de usuario no configurado: "
                    f"{user_profile}"
                )

            nombre = self._normalize(
                row.get("nombre")
            )

            apellido = self._build_apellido(
                row=row,
                country_code=country_code,
            )

            email = self._normalize(
                row.get("email")
            ).lower()

            documento = self._build_documento(
                row=row,
                country_code=country_code,
            )

            cliente = self._build_cliente(
                row=row,
                country_config=country_config,
            )

            rows.append({
                "NOMBRE": nombre,
                "APELLIDO": apellido,
                "CORREO": email,
                "PAIS":
                    country_config["pais"],
                "PERFIL DE USUARIO":
                    country_config["perfil_usuario"],
                "TIPO DE USUARIO":
                    type_config["tipo_usuario"],
                "TIPO DE DOCUMENTO IDENTIDAD":
                    country_config["tipo_documento"],
                "DOCUMENTO":
                    documento,
                "SOCIEDAD":
                    country_config["sociedad"],
                "CLIENTE":
                    cliente,
                "SERVICIO":
                    type_config["servicio"],
            })

        return pd.DataFrame(
            rows,
            columns=self.USUARIOS_COLUMNS,
        )

    # ==========================================================
    # HELPERS PLANTILLA
    # ==========================================================

    def _build_apellido(
        self,
        row,
        country_code: str,
    ) -> str:

        if country_code == "SLV":
            return self._normalize(
                row.get("apellido")
            )

        apellido = self._normalize(
            row.get("apellido")
        )

        if apellido:
            return apellido

        paterno = self._normalize(
            row.get("apellido_pat")
        )

        materno = self._normalize(
            row.get("apellido_mat")
        )

        return " ".join(
            part
            for part in [paterno, materno]
            if part
        )

    def _build_documento(
        self,
        row,
        country_code: str,
    ) -> str:

        value = self._normalize(
            row.get("numero_documento")
        )

        digits = "".join(
            c for c in value
            if c.isdigit()
        )

        if country_code == "SLV":
            if len(digits) == 9:
                return f"{digits[:8]}-{digits[8]}"

        return digits or value

    def _build_cliente(
        self,
        row,
        country_config: dict,
    ) -> str:

        return self.client_assignment.resolve(
            row=row,
            country_config=country_config,
        )

    # ==========================================================
    # HELPERS GENERALES
    # ==========================================================

    @classmethod
    def _first_value(
        cls,
        row,
        *columns,
    ) -> str:

        for column in columns:

            if column not in row.index:
                continue

            value = cls._normalize(
                row.get(column)
            )

            if value:
                return value

        return ""

    @staticmethod
    def _normalize(value) -> str:

        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        return str(value).strip()
