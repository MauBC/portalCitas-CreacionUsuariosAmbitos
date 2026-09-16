import pandas as pd


class RequiredFieldsService:
    COUNTRY_LABELS = {
        "PER": {
            "person_document": "DNI",
            "tax_document": "RUC",
        },
        "SLV": {
            "person_document": "DUI",
            "tax_document": "NIT",
        },
    }

    def get_missing_fields(
        self,
        row,
    ) -> list[str]:
        country = self._country(row)

        labels = self.COUNTRY_LABELS.get(
            country,
            {
                "person_document": "DOCUMENTO",
                "tax_document": "ID TRIBUTARIO",
            },
        )

        missing = []

        if not self._has_value(
            row,
            "_origen_nombre",
            "nombre",
            "nombre_personal",
        ):
            missing.append("NOMBRE")

        if not self._has_value(
            row,
            "_origen_apellido",
            "apellido_pat",
            "apellido",
            "apellido_personal",
        ):
            missing.append(
                "APELLIDO PATERNO"
            )

        if not self._has_value(
            row,
            "_origen_correo",
            "email",
            "correo",
        ):
            missing.append("CORREO")

        if not self._has_value(
            row,
            "_origen_docIdentidad",
            "DUI_personal",
            "dni",
            "DNI",
            "documento",
            "numero_documento",
        ):
            missing.append(
                labels[
                    "person_document"
                ]
            )

        profile = self._text(
            row.get("perfil")
        ).upper()

        if profile == "PROVEEDOR":
            if not self._has_value(
                row,
                "_origen_nombreProveedor",
                "nombre_proveedor",
                "nombres",
            ):
                missing.append(
                    "PROVEEDOR"
                )

            if not self._has_value(
                row,
                "_origen_nombreCliente",
                "nombre_cliente",
            ):
                missing.append(
                    "CLIENTE"
                )

            if not self._has_value(
                row,
                "_origen_rucProveedor",
                "nit_empresa",
                "_ruc_proveedor_original",
                "ruc_proveedor",
                "nit_proveedor",
                "ruc",
            ):
                missing.append(
                    labels[
                        "tax_document"
                    ]
                )

        elif profile == "CLIENTE":
            if not self._has_value(
                row,
                "_origen_nombreCliente",
                "nombre_cliente",
            ):
                missing.append(
                    "CLIENTE"
                )

            if not self._has_value(
                row,
                "_ruc_cliente_original",
                "ruc_cliente",
                "nit_cliente",
            ):
                missing.append(
                    labels[
                        "tax_document"
                    ]
                )

        elif profile == "RANSA":
            if not self._has_value(
                row,
                "negocio",
            ):
                missing.append(
                    "NEGOCIO"
                )

            if not self._has_value(
                row,
                "tipo_cargo",
            ):
                missing.append(
                    "TIPO CARGO"
                )

        return list(
            dict.fromkeys(
                missing
            )
        )

    def get_missing_text(
        self,
        row,
    ) -> str:
        return " | ".join(
            self.get_missing_fields(
                row
            )
        )

    def get_document_labels(
        self,
        country_code: str,
    ) -> tuple[str, str]:
        country = self._text(
            country_code
        ).upper()

        labels = self.COUNTRY_LABELS.get(
            country
        )

        if not labels:
            return (
                "DOCUMENTO",
                "ID TRIBUTARIO",
            )

        return (
            labels["person_document"],
            labels["tax_document"],
        )

    def _country(
        self,
        row,
    ) -> str:
        return self._text(
            row.get("pais")
        ).upper()

    @classmethod
    def _has_value(
        cls,
        row,
        *columns,
    ) -> bool:
        for column in columns:
            if column not in row.index:
                continue

            if cls._text(
                row.get(column)
            ):
                return True

        return False

    @staticmethod
    def _text(
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
