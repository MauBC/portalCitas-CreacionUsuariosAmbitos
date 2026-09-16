import re

import pandas as pd

from app.config.country_data_rules import (
    COUNTRY_DATA_RULES,
)
from app.services.common_cleaning_service import (
    CommonCleaningService,
)


class SlvCleaningService:
    PERFILES_VALIDOS = {
        "CLIENTE",
        "PROVEEDOR",
    }

    REQUIRED_COLUMNS = [
        "_item_id",
        "pais",
        "creado",
        "nombre",
        "apellido",
        "apellido_pat",
        "apellido_mat",
        "email",
        "telefono",
        "tipo_documento",
        "numero_documento",
        "perfil",
        "nombre_proveedor",
        "nit_proveedor",
        "nombre_cliente",
        "capacitacion",
    ]

    def __init__(self):
        self.common = CommonCleaningService()
        self.rules = COUNTRY_DATA_RULES["SLV"]

    def clean(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        result = df.copy()

        for column in self.REQUIRED_COLUMNS:
            if column not in result.columns:
                result[column] = ""

        result["pais"] = "SLV"
        result["tipo_documento"] = "DUI"

        result["_numero_documento_original"] = (
            result["numero_documento"].copy()
        )
        result["_nit_proveedor_original"] = (
            result["nit_proveedor"].copy()
        )

        for column in [
            "nombre",
            "apellido",
            "apellido_pat",
            "apellido_mat",
            "nombre_proveedor",
            "nombre_cliente",
        ]:
            result[column] = result[column].apply(
                self.common.clean_text
            )

        result["email"] = result["email"].apply(
            self.common.clean_email
        )

        for column in [
            "telefono",
            "numero_documento",
            "nit_proveedor",
        ]:
            result[column] = result[column].apply(
                self.common.clean_digits
            )

        result["perfil"] = result["perfil"].apply(
            self.common.clean_text
        )

        result.loc[
            result["perfil"].eq(""),
            "perfil",
        ] = "PROVEEDOR"

        result["dui_valido"] = (
            result["numero_documento"]
            .apply(
                lambda value:
                    self.common.valid_exact_digits(
                        value,
                        self.rules[
                            "person_document_length"
                        ],
                    )
            )
        )

        result["nit_valido"] = (
            result.apply(
                lambda row:
                    self._valid_nit(
                        clean_value=row.get(
                            "nit_proveedor"
                        ),
                        original_value=row.get(
                            "_nit_proveedor_original"
                        ),
                    ),
                axis=1,
            )
        )

        result["correo_valido"] = (
            result["email"]
            .apply(
                self.common.valid_email
            )
        )

        validation = result.apply(
            self._validate_row,
            axis=1,
            result_type="expand",
        )

        result["observaciones"] = (
            validation["errores"]
        )
        result["advertencias"] = (
            validation["advertencias"]
        )

        result["estado"] = (
            result["observaciones"]
            .apply(
                lambda value:
                    "OK"
                    if not str(value or "").strip()
                    else "ERROR"
            )
        )

        return result

    def _valid_nit(
        self,
        clean_value,
        original_value,
    ) -> bool:
        if not self.common.numeric_input_has_valid_chars(
            original_value
        ):
            return False

        return self.common.valid_exact_digits(
            clean_value,
            self.rules[
                "company_document_length"
            ],
        )

    def _validate_row(
        self,
        row,
    ) -> pd.Series:
        errors = []
        warnings = []

        nombre = str(
            row.get("nombre") or ""
        ).strip()

        apellido = self._get_paternal_last_name(
            row
        )

        email = str(
            row.get("email") or ""
        ).strip()

        document = str(
            row.get("numero_documento")
            or ""
        ).strip()

        original_document = str(
            row.get("_numero_documento_original")
            or ""
        ).strip()

        profile = str(
            row.get("perfil") or ""
        ).strip()

        provider_name = str(
            row.get("nombre_proveedor")
            or ""
        ).strip()

        client_name = str(
            row.get("nombre_cliente")
            or ""
        ).strip()

        nit = str(
            row.get("nit_proveedor")
            or ""
        ).strip()

        original_nit = str(
            row.get("_nit_proveedor_original")
            or ""
        ).strip()

        if not nombre:
            errors.append(
                "NOMBRE OBLIGATORIO"
            )

        if not apellido:
            errors.append(
                "APELLIDO PATERNO OBLIGATORIO"
            )

        if not email:
            errors.append(
                "CORREO OBLIGATORIO"
            )
        elif not bool(
            row.get("correo_valido")
        ):
            errors.append(
                "CORREO INVALIDO"
            )

        if not original_document:
            errors.append(
                "DUI OBLIGATORIO"
            )
        elif not bool(
            row.get("dui_valido")
        ):
            warnings.append(
                "DUI CON FORMATO INUSUAL"
            )

        phone = str(
            row.get("telefono") or ""
        ).strip()

        if phone and not self._valid_phone(
            phone
        ):
            warnings.append(
                "TELEFONO CON FORMATO INUSUAL"
            )

        if profile not in self.PERFILES_VALIDOS:
            errors.append(
                "TIPO DE USUARIO INVALIDO"
            )

        if profile == "PROVEEDOR":
            if len(provider_name) <= 2:
                errors.append(
                    "NOMBRE PROVEEDOR OBLIGATORIO"
                )

            if not original_nit:
                errors.append(
                    "NIT PROVEEDOR OBLIGATORIO"
                )
            elif not bool(
                row.get("nit_valido")
            ):
                errors.append(
                    "NIT PROVEEDOR INVALIDO"
                )

            if len(client_name) <= 2:
                errors.append(
                    "NOMBRE CLIENTE OBLIGATORIO"
                )

        elif profile == "CLIENTE":
            if len(client_name) <= 2:
                errors.append(
                    "NOMBRE CLIENTE OBLIGATORIO"
                )

        return pd.Series({
            "errores":
                self.common.join_messages(
                    errors
                ),
            "advertencias":
                self.common.join_messages(
                    warnings
                ),
        })

    def _get_paternal_last_name(
        self,
        row,
    ) -> str:
        paternal = str(
            row.get("apellido_pat")
            or ""
        ).strip()

        if paternal:
            return paternal

        return str(
            row.get("apellido")
            or ""
        ).strip()

    @staticmethod
    def _valid_phone(value) -> bool:
        digits = str(
            value or ""
        ).strip()

        if digits.startswith("503"):
            digits = digits[3:]

        return bool(
            re.fullmatch(
                r"\d{8}",
                digits,
            )
        )
