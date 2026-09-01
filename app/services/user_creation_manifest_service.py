import os
import pandas as pd


class UserCreationManifestService:

    def save(
        self,
        df_validos: pd.DataFrame,
        output_dir: str,
    ) -> str:

        required = {"_item_id", "email"}

        missing = required - set(df_validos.columns)

        if missing:
            raise ValueError(
                f"Faltan columnas para generar manifiesto: {sorted(missing)}"
            )

        manifest = df_validos.copy()

        columns = [
            "_item_id",
            "email",
        ]

        optional_columns = [
            "pais",
            "numero_documento",
            "nombre",
            "apellido",
            "nombre_proveedor",
        ]

        for col in optional_columns:
            if col in manifest.columns:
                columns.append(col)

        manifest = manifest[columns].copy()

        manifest["email"] = (
            manifest["email"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )

        path = os.path.join(
            output_dir,
            "usuarios_enviados.xlsx",
        )

        manifest.to_excel(
            path,
            index=False,
        )

        return os.path.abspath(path)
