import pandas as pd


class CountryMappingService:

    def map(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        if "pais" not in df.columns:
            raise ValueError(
                "El DataFrame no contiene la columna pais."
            )

        df = df.copy()

        df["pais"] = (
            df["pais"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        slv_mask = df["pais"] == "SLV"

        if slv_mask.any():
            mapping = {
                "nombre": "nombre_personal",
                "apellido": "apellido_personal",
                "email": "email",
                "telefono": "num_celular",
                "numero_documento": "DUI_personal",
                "nombre_proveedor": "nombres",
                "nit_proveedor": "nit_empresa",
                "nombre_cliente": "nombre_cliente",
                "capacitacion": "asistio_capacitacion",
                "creado": "CREADO",
            }

            for target, source in mapping.items():
                if target not in df.columns:
                    df[target] = None

                if source in df.columns:
                    df.loc[slv_mask, target] = (
                        df.loc[slv_mask, source]
                    )

            df.loc[slv_mask, "tipo_documento"] = "DUI"
            df.loc[slv_mask, "perfil"] = "PROVEEDOR"

        return df
