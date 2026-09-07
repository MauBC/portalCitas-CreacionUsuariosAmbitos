import os
from datetime import datetime

import pandas as pd

from app.config.portal_access_config import (
    PORTAL_ACCESS_SERVICE,
)
from app.config.portal_template_config import (
    COUNTRY_TEMPLATE_CONFIG,
    USER_TYPE_CONFIG,
)
from app.services.portal_user_template_service import (
    PortalUserTemplateService,
)
from app.services.required_fields_service import (
    RequiredFieldsService,
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

    def __init__(
        self,
        output_dir: str,
    ):
        self.output_dir = output_dir

        os.makedirs(
            self.output_dir,
            exist_ok=True,
        )

        self.portal_template = (
            PortalUserTemplateService()
        )

        self.required_fields = (
            RequiredFieldsService()
        )

    def export_validos_errores(
        self,
        df: pd.DataFrame,
        base_name: str = "reporte",
    ) -> dict:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

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
            context_df=df,
        )

        self._export_validation_report(
            df=errores,
            path=error_path,
            summary_sheet="ERRORES_RESUMEN",
            context_df=df,
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
        context_df: pd.DataFrame | None = None,
    ) -> None:
        resumen = (
            self._build_validation_summary(
                df
            )
        )

        is_error_report = (
            summary_sheet
            == "ERRORES_RESUMEN"
        )

        with pd.ExcelWriter(
            path,
            engine="openpyxl",
        ) as writer:
            if is_error_report:
                pendientes = (
                    self._build_business_pending_report(
                        df=df,
                        resumen=resumen,
                        context_df=(
                            context_df
                            if context_df is not None
                            else df
                        ),
                    )
                )

                pendientes.to_excel(
                    writer,
                    sheet_name="PENDIENTES_CUENTA",
                    index=False,
                )

            resumen.to_excel(
                writer,
                sheet_name=summary_sheet,
                index=False,
            )

            df.to_excel(
                writer,
                sheet_name="DATOS_TECNICOS",
                index=False,
            )

            for worksheet in (
                writer.book.worksheets
            ):
                worksheet.freeze_panes = "A2"

                if (
                    worksheet.max_row >= 1
                    and worksheet.max_column >= 1
                ):
                    worksheet.auto_filter.ref = (
                        worksheet.dimensions
                    )

                for column_index in range(
                    1,
                    worksheet.max_column + 1,
                ):
                    cell = worksheet.cell(
                        row=1,
                        column=column_index,
                    )

                    letter = (
                        cell.column_letter
                    )

                    values = [
                        str(
                            worksheet.cell(
                                row=row_index,
                                column=column_index,
                            ).value
                            or ""
                        )
                        for row_index in range(
                            1,
                            min(
                                worksheet.max_row,
                                200,
                            )
                            + 1
                        )
                    ]

                    max_length = max(
                        [
                            len(value)
                            for value in values
                        ]
                        or [10]
                    )

                    worksheet.column_dimensions[
                        letter
                    ].width = min(
                        max(
                            max_length + 2,
                            12,
                        ),
                        60,
                    )



    def _build_business_pending_report(
        self,
        df: pd.DataFrame,
        resumen: pd.DataFrame,
        context_df: pd.DataFrame,
    ) -> pd.DataFrame:
        columns = [
            "PAIS",
            "NOMBRE COMPLETO",
            "CORREO",
            "PROVEEDOR",
            "CLIENTE",
            "DATOS POR COMPLETAR",
            "MOTIVO",
            "ACCION REQUERIDA",
            "ESTADO CUENTA",
        ]

        if df.empty:
            return pd.DataFrame(
                columns=columns
            )

        technical = (
            df.reset_index(
                drop=True
            )
        )

        human = (
            resumen.reset_index(
                drop=True
            )
        )

        context = (
            context_df.reset_index(
                drop=True
            )
        )

        valid_email_keys = set()

        if (
            "email" in context.columns
            and "estado" in context.columns
        ):
            for _, context_row in (
                context.iterrows()
            ):
                state = (
                    str(
                        context_row.get(
                            "estado"
                        )
                        or ""
                    )
                    .strip()
                    .upper()
                )

                email = (
                    str(
                        context_row.get(
                            "email"
                        )
                        or ""
                    )
                    .strip()
                    .lower()
                )

                if (
                    state == "OK"
                    and email
                ):
                    valid_email_keys.add(
                        email
                    )

        rows = []

        for position, row in (
            technical.iterrows()
        ):
            email_key = (
                str(
                    row.get("email")
                    or ""
                )
                .strip()
                .lower()
            )

            if (
                email_key
                and email_key
                in valid_email_keys
            ):
                continue

            summary = (
                human.iloc[position]
                if position < len(human)
                else pd.Series(
                    dtype=object
                )
            )

            nombre = str(
                summary.get(
                    "NOMBRE"
                )
                or ""
            ).strip()

            apellido = str(
                summary.get(
                    "APELLIDO"
                )
                or ""
            ).strip()

            full_name = " ".join(
                part
                for part in [
                    nombre,
                    apellido,
                ]
                if part
            )

            email = str(
                summary.get(
                    "CORREO"
                )
                or ""
            ).strip()

            provider = str(
                summary.get(
                    "PROVEEDOR"
                )
                or ""
            ).strip()

            normalized_client = str(
                summary.get(
                    "CLIENTE NORMALIZADO"
                )
                or ""
            ).strip()

            entered_client = str(
                summary.get(
                    "CLIENTE INGRESADO"
                )
                or ""
            ).strip()

            client = (
                normalized_client
                or entered_client
            )

            missing = str(
                summary.get(
                    "FALTA LLENAR"
                )
                or ""
            ).strip()

            error = str(
                summary.get(
                    "ERROR"
                )
                or ""
            ).strip()

            rows.append({
                "PAIS":
                    str(
                        summary.get(
                            "PAIS"
                        )
                        or ""
                    ).strip(),
                "NOMBRE COMPLETO":
                    full_name
                    or "SIN NOMBRE",
                "CORREO":
                    email
                    or "SIN CORREO",
                "PROVEEDOR":
                    provider
                    or "SIN PROVEEDOR",
                "CLIENTE":
                    client
                    or "SIN CLIENTE",
                "DATOS POR COMPLETAR":
                    missing,
                "MOTIVO":
                    error,
                "ACCION REQUERIDA":
                    self._business_action(
                        missing=missing,
                        error=error,
                    ),
                "ESTADO CUENTA":
                    "NO GENERADA",
            })

        return pd.DataFrame(
            rows,
            columns=columns,
        )


    @staticmethod
    def _business_action(
        missing: str,
        error: str,
    ) -> str:
        missing = str(
            missing or ""
        ).strip()

        error_upper = str(
            error or ""
        ).strip().upper()

        if missing:
            return (
                "Completar los siguientes datos: "
                + missing.replace(
                    " | ",
                    ", ",
                )
            )

        if (
            "CORREO INVALIDO"
            in error_upper
        ):
            return (
                "Corregir el correo ingresado"
            )

        if (
            "CLIENTE NO RECONOCIDO"
            in error_upper
        ):
            return (
                "Revisar y corregir "
                "el cliente ingresado"
            )

        if (
            "TIPO DE USUARIO INVALIDO"
            in error_upper
        ):
            return (
                "Corregir el tipo de usuario"
            )

        if (
            "RUC PROVEEDOR INVALIDO"
            in error_upper
        ):
            return (
                "Corregir el RUC del proveedor"
            )

        return (
            "Corregir los datos indicados "
            "en la columna MOTIVO"
        )

    def _build_validation_summary(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        country = (
            self._resolve_report_country(
                df
            )
        )

        (
            person_document_label,
            tax_document_label,
        ) = (
            self.required_fields
            .get_document_labels(
                country
            )
        )

        person_original_column = (
            f"{person_document_label} "
            "ORIGINAL"
        )
        person_clean_column = (
            f"{person_document_label} "
            "LIMPIO"
        )
        tax_original_column = (
            f"{tax_document_label} "
            "ORIGINAL"
        )
        tax_clean_column = (
            f"{tax_document_label} "
            "LIMPIO"
        )

        rows = []

        for _, row in df.iterrows():
            profile = (
                self._first_value(
                    row,
                    "perfil",
                )
                .upper()
            )

            tax_clean = (
                self._tax_clean_value(
                    row=row,
                    profile=profile,
                    country=country,
                )
            )

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
                    self._summary_apellido(
                        row
                    ),
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
                person_original_column:
                    self._first_value(
                        row,
                        "_origen_docIdentidad",
                        "DUI_personal",
                        "dni",
                        "DNI",
                        "documento",
                        "numero_documento",
                    ),
                person_clean_column:
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
                        "num_telefono",
                    ),
                tax_original_column:
                    self._first_value(
                        row,
                        "_origen_rucProveedor",
                        "nit_empresa",
                        "_ruc_proveedor_original",
                        "_ruc_cliente_original",
                        "ruc",
                        "ruc_proveedor",
                        "nit_proveedor",
                    ),
                tax_clean_column:
                    tax_clean,
                "PERFIL":
                    profile,
                "FALTA LLENAR":
                    self.required_fields
                    .get_missing_text(
                        row
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
            person_original_column,
            person_clean_column,
            "TELEFONO ORIGINAL",
            "TELEFONO LIMPIO",
            tax_original_column,
            tax_clean_column,
            "PERFIL",
            "FALTA LLENAR",
            "ESTADO",
            "ERROR",
        ]

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    def _resolve_report_country(
        self,
        df: pd.DataFrame,
    ) -> str:
        if (
            df.empty
            or "pais" not in df.columns
        ):
            return ""

        countries = {
            self._normalize(
                value
            ).upper()
            for value in df["pais"]
            if self._normalize(
                value
            )
        }

        if len(countries) == 1:
            return next(
                iter(countries)
            )

        return ""

    def _tax_clean_value(
        self,
        row,
        profile: str,
        country: str,
    ) -> str:
        if profile == "CLIENTE":
            return self._first_value(
                row,
                "ruc_cliente",
                "nit_cliente",
            )

        if country == "SLV":
            return self._first_value(
                row,
                "nit_proveedor",
                "ruc_proveedor",
            )

        return self._first_value(
            row,
            "ruc_proveedor",
            "nit_proveedor",
        )

    def _summary_apellido(
        self,
        row,
    ) -> str:
        paternal = self._first_value(
            row,
            "apellido_pat",
        )

        maternal = self._first_value(
            row,
            "apellido_mat",
        )

        if paternal or maternal:
            return " ".join(
                part
                for part in [
                    paternal,
                    maternal,
                ]
                if part
            )

        return self._first_value(
            row,
            "apellido",
            "apellido_personal",
        )


    def export_template(
        self,
        df_validos: pd.DataFrame,
    ) -> str:
        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        path = os.path.join(
            self.output_dir,
            (
                "plantilla_usuarios_"
                f"{timestamp}.xlsx"
            ),
        )

        usuarios = (
            self._build_usuarios_sheet(
                df_validos
            )
        )

        country_code = (
            self._resolve_template_country(
                df_validos
            )
        )

        service_name = (
            PORTAL_ACCESS_SERVICE.get(
                country_code
            )
        )

        if not service_name:
            raise ValueError(
                "No existe servicio de acceso "
                f"configurado para {country_code}"
            )

        return (
            self.portal_template
            .write(
                usuarios=usuarios,
                output_path=path,
                service_name=
                    service_name,
            )
        )

    def _resolve_template_country(
        self,
        df: pd.DataFrame,
    ) -> str:
        if "pais" not in df.columns:
            return "PER"

        countries = {
            (
                self._normalize(
                    value
                ).upper()
                or "PER"
            )
            for value in df["pais"]
        }

        if len(countries) != 1:
            raise ValueError(
                "La plantilla de usuarios debe "
                "generarse para un solo pais. "
                f"Paises encontrados: "
                f"{sorted(countries)}"
            )

        return next(
            iter(countries)
        )

    def _build_usuarios_sheet(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        rows = []

        for _, row in df.iterrows():
            country_code = (
                self._normalize(
                    row.get("pais")
                ).upper()
            )

            if not country_code:
                country_code = "PER"

            country_config = (
                COUNTRY_TEMPLATE_CONFIG
                .get(
                    country_code
                )
            )

            if country_config is None:
                raise ValueError(
                    "No existe configuracion "
                    "de plantilla para el pais: "
                    f"{country_code}"
                )

            user_profile = (
                self._normalize(
                    row.get("perfil")
                ).upper()
            )

            if not user_profile:
                user_profile = "PROVEEDOR"

            type_config = (
                USER_TYPE_CONFIG.get(
                    user_profile
                )
            )

            if type_config is None:
                raise ValueError(
                    "Tipo de usuario "
                    "no configurado: "
                    f"{user_profile}"
                )

            nombre = self._normalize(
                row.get("nombre")
            )

            apellido = (
                self._build_apellido(
                    row=row,
                    country_code=
                        country_code,
                )
            )

            email = (
                self._normalize(
                    row.get("email")
                )
                .lower()
            )

            documento = (
                self._build_documento(
                    row=row,
                    country_code=
                        country_code,
                )
            )

            rows.append({
                "NOMBRE":
                    nombre,
                "APELLIDO":
                    apellido,
                "CORREO":
                    email,
                "PAIS":
                    country_config[
                        "pais"
                    ],
                "PERFIL DE USUARIO":
                    country_config[
                        "perfil_usuario"
                    ],
                "TIPO DE USUARIO":
                    type_config[
                        "tipo_usuario"
                    ],
                "TIPO DE DOCUMENTO IDENTIDAD":
                    country_config[
                        "tipo_documento"
                    ],
                "DOCUMENTO":
                    documento,
                "SOCIEDAD":
                    country_config[
                        "sociedad"
                    ],
                "CLIENTE":
                    "",
                "SERVICIO":
                    type_config[
                        "servicio"
                    ],
            })

        return pd.DataFrame(
            rows,
            columns=
                self.USUARIOS_COLUMNS,
        )

    def _build_apellido(
        self,
        row,
        country_code: str,
    ) -> str:
        paternal = self._normalize(
            row.get("apellido_pat")
        )

        maternal = self._normalize(
            row.get("apellido_mat")
        )

        if paternal or maternal:
            return " ".join(
                part
                for part in [
                    paternal,
                    maternal,
                ]
                if part
            )

        return self._normalize(
            row.get("apellido")
            or row.get("apellido_personal")
        )


    def _build_documento(
        self,
        row,
        country_code: str,
    ) -> str:
        value = self._normalize(
            row.get(
                "numero_documento"
            )
        )

        digits = "".join(
            char
            for char in value
            if char.isdigit()
        )

        return digits or value

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
    def _normalize(
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

        return str(value).strip()
