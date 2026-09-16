import pandas as pd


class ProviderExcelMappingService:
    COLUMN_MAP = {
        "nombre": "nombre",
        "apellido": "apellido",
        "apellidomaterno": "apellidomaterno",
        "nombrecliente": "nombreCliente",
        "rucproveedor": "rucProveedor",
        "nombreproveedor": "nombreProveedor",
        "correo": "correo",
        "tipousuario": "tipoUsuario",
        "docidentidad": "docIdentidad",
        "creado": "creado",
    }

    REQUIRED_COLUMNS = {
        "nombre",
        "apellido",
        "nombreCliente",
        "rucProveedor",
        "nombreProveedor",
        "correo",
        "tipoUsuario",
        "docIdentidad",
        "creado",
    }

    OPTIONAL_COLUMNS = {
        "apellidomaterno",
    }

    SUPPORTED_COUNTRIES = {
        "PER",
        "SLV",
    }

    def map(
        self,
        df: pd.DataFrame,
        country_code: str,
    ) -> pd.DataFrame:
        country = str(
            country_code or ""
        ).strip().upper()

        if country not in self.SUPPORTED_COUNTRIES:
            raise ValueError(
                f"Pais no soportado: {country}"
            )

        source = self._canonicalize_columns(df)
        rows = []

        for index, row in source.iterrows():
            user_type = str(
                row.get("tipoUsuario") or ""
            ).strip()

            if not user_type:
                user_type = "PROVEEDOR"

            record = {
                "_item_id":
                    f"EXCEL-{index + 1:06d}",
                "origen":
                    "EXCEL_PROVEEDORES",
                "pais":
                    country,
                "creado":
                    row.get(
                        "creado",
                        "",
                    ),
                "nombre":
                    row.get(
                        "nombre",
                        "",
                    ),
                "apellido":
                    row.get(
                        "apellido",
                        "",
                    ),
                "apellido_pat":
                    row.get(
                        "apellido",
                        "",
                    ),
                "apellido_mat":
                    row.get(
                        "apellidomaterno",
                        "",
                    ),
                "email":
                    row.get(
                        "correo",
                        "",
                    ),
                "numero_documento":
                    row.get(
                        "docIdentidad",
                        "",
                    ),
                "perfil":
                    user_type,
                "nombre_cliente":
                    row.get(
                        "nombreCliente",
                        "",
                    ),
                "nombre_proveedor":
                    row.get(
                        "nombreProveedor",
                        "",
                    ),
                "telefono":
                    "",
                "num_telefono":
                    "",
                "capacitacion":
                    "",
                "negocio":
                    "",
                "tipo_cargo":
                    "",
                "sede":
                    "",
                "ruc_cliente":
                    "",
                "ruc_proveedor":
                    (
                        row.get(
                            "rucProveedor",
                            "",
                        )
                        if country == "PER"
                        else ""
                    ),
                "nit_proveedor":
                    (
                        row.get(
                            "rucProveedor",
                            "",
                        )
                        if country == "SLV"
                        else ""
                    ),
            }

            for column in source.columns:
                record[
                    f"_origen_{column}"
                ] = row.get(
                    column,
                    "",
                )

            rows.append(record)

        return pd.DataFrame(rows)

    def _canonicalize_columns(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        source = df.copy()
        rename = {}

        for column in source.columns:
            normalized = (
                self._normalize_header(
                    column
                )
            )

            target = self.COLUMN_MAP.get(
                normalized
            )

            if target:
                rename[column] = target

        source = source.rename(
            columns=rename
        )

        missing = (
            self.REQUIRED_COLUMNS
            - set(source.columns)
        )

        if missing:
            raise ValueError(
                "Columnas no reconocidas: "
                + ", ".join(
                    sorted(missing)
                )
            )

        for column in self.OPTIONAL_COLUMNS:
            if column not in source.columns:
                source[column] = ""

        return source

    @staticmethod
    def _normalize_header(
        value,
    ) -> str:
        return (
            str(value or "")
            .strip()
            .replace(" ", "")
            .replace("_", "")
            .lower()
        )
