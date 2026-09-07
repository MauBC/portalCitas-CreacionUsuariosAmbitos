import re

import pandas as pd

from app.config.country_data_rules import (
    COUNTRY_DATA_RULES,
)
from app.services.common_cleaning_service import (
    CommonCleaningService,
)


class PerCleaningService:
    PERFILES_VALIDOS = {
        "RANSA",
        "CLIENTE",
        "PROVEEDOR",
    }

    REQUIRED_COLUMNS = [
        "_item_id",
        "pais",
        "creado",
        "tipo_documento",
        "numero_documento",
        "nombre",
        "apellido",
        "apellido_pat",
        "apellido_mat",
        "email",
        "num_telefono",
        "perfil",
        "negocio",
        "tipo_cargo",
        "capacitacion",
        "sede",
        "nombre_cliente",
        "ruc_cliente",
        "nombre_proveedor",
        "ruc_proveedor",
    ]

    def __init__(self):
        self.common = CommonCleaningService()
        self.rules = COUNTRY_DATA_RULES["PER"]

    def clean(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        result = df.copy()

        for column in self.REQUIRED_COLUMNS:
            if column not in result.columns:
                result[column] = ""

        result["pais"] = "PER"
        result["tipo_documento"] = "DNI"

        result["_numero_documento_original"] = (
            result["numero_documento"].copy()
        )
        result["_ruc_cliente_original"] = (
            result["ruc_cliente"].copy()
        )
        result["_ruc_proveedor_original"] = (
            result["ruc_proveedor"].copy()
        )

        for column in [
            "nombre",
            "apellido",
            "apellido_pat",
            "apellido_mat",
            "nombre_cliente",
            "nombre_proveedor",
            "negocio",
            "tipo_cargo",
        ]:
            result[column] = result[column].apply(
                self.common.clean_text
            )

        result["email"] = result["email"].apply(
            self.common.clean_email
        )

        for column in [
            "numero_documento",
            "ruc_cliente",
            "ruc_proveedor",
            "num_telefono",
        ]:
            result[column] = result[column].apply(
                self.common.clean_digits
            )

        result["perfil"] = result["perfil"].apply(
            self.common.clean_text
        )

        result["dni_valido"] = (
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

        result["correo_valido"] = (
            result["email"]
            .apply(
                self.common.valid_email
            )
        )

        result["ruc_cliente_valido"] = (
            result.apply(
                lambda row:
                    self._valid_ruc(
                        clean_value=row.get(
                            "ruc_cliente"
                        ),
                        original_value=row.get(
                            "_ruc_cliente_original"
                        ),
                    ),
                axis=1,
            )
        )

        result["ruc_proveedor_valido"] = (
            result.apply(
                lambda row:
                    self._valid_ruc(
                        clean_value=row.get(
                            "ruc_proveedor"
                        ),
                        original_value=row.get(
                            "_ruc_proveedor_original"
                        ),
                    ),
                axis=1,
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

    def _valid_ruc(
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
                "DNI OBLIGATORIO"
            )
        elif not bool(
            row.get("dni_valido")
        ):
            warnings.append(
                "DNI CON FORMATO INUSUAL"
            )

        phone = str(
            row.get("num_telefono")
            or ""
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

        elif profile == "PROVEEDOR":
            self._validate_provider(
                row,
                errors,
            )

        elif profile == "CLIENTE":
            self._validate_client(
                row,
                errors,
            )

        elif profile == "RANSA":
            if not str(
                row.get("negocio") or ""
            ).strip():
                errors.append(
                    "NEGOCIO OBLIGATORIO"
                )

            if not str(
                row.get("tipo_cargo") or ""
            ).strip():
                errors.append(
                    "TIPO CARGO OBLIGATORIO"
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

    def _validate_provider(
        self,
        row,
        errors,
    ):
        provider_name = str(
            row.get("nombre_proveedor")
            or ""
        ).strip()

        client_name = str(
            row.get("nombre_cliente")
            or ""
        ).strip()

        ruc = str(
            row.get("ruc_proveedor")
            or ""
        ).strip()

        original_ruc = str(
            row.get("_ruc_proveedor_original")
            or ""
        ).strip()

        if len(provider_name) <= 2:
            errors.append(
                "NOMBRE PROVEEDOR OBLIGATORIO"
            )

        if not original_ruc:
            errors.append(
                "RUC PROVEEDOR OBLIGATORIO"
            )
        elif not bool(
            row.get("ruc_proveedor_valido")
        ):
            errors.append(
                "RUC PROVEEDOR INVALIDO"
            )

        if len(client_name) <= 2:
            errors.append(
                "NOMBRE CLIENTE OBLIGATORIO"
            )

    def _validate_client(
        self,
        row,
        errors,
    ):
        client_name = str(
            row.get("nombre_cliente")
            or ""
        ).strip()

        ruc = str(
            row.get("ruc_cliente")
            or ""
        ).strip()

        original_ruc = str(
            row.get("_ruc_cliente_original")
            or ""
        ).strip()

        if len(client_name) <= 2:
            errors.append(
                "NOMBRE CLIENTE OBLIGATORIO"
            )

        if not original_ruc:
            errors.append(
                "RUC CLIENTE OBLIGATORIO"
            )
        elif not bool(
            row.get("ruc_cliente_valido")
        ):
            errors.append(
                "RUC CLIENTE INVALIDO"
            )

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

        if digits.startswith("51"):
            digits = digits[2:]

        return bool(
            re.fullmatch(
                r"9\d{8}|\d{7,8}",
                digits,
            )
        )
