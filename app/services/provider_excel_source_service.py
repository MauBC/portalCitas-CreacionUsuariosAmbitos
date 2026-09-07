from base64 import urlsafe_b64encode
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

from app.auth.msal_auth import MsalAuthService


class ProviderExcelSourceService:
    SHEET_NAME = "Proveedores"

    REQUIRED_COLUMNS = [
        "nombre",
        "apellido",
        "nombreCliente",
        "rucProveedor",
        "nombreProveedor",
        "correo",
        "tipoUsuario",
        "docIdentidad",
        "creado",
    ]

    OPTIONAL_COLUMNS = [
        "apellidomaterno",
    ]

    SUPPORTED_EXTENSIONS = {
        ".xlsx",
        ".xlsm",
        ".xls",
    }

    def load_local(
        self,
        file_path: str,
    ) -> pd.DataFrame:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"No existe Excel: {path}"
            )

        if (
            path.suffix.lower()
            not in self.SUPPORTED_EXTENSIONS
        ):
            raise ValueError(
                "El archivo debe ser Excel."
            )

        data = self._read_provider_sheet(
            path
        )
        self._validate_columns(
            data
        )

        return data

    def load_sharepoint(
        self,
        shared_url: str,
    ) -> pd.DataFrame:
        shared_url = str(
            shared_url or ""
        ).strip()

        if not shared_url:
            raise ValueError(
                "Falta URL compartida "
                "de SharePoint/OneDrive."
            )

        encoded = self._encode_shared_url(
            shared_url
        )

        token = (
            MsalAuthService()
            .get_access_token()
        )

        endpoint = (
            "https://graph.microsoft.com/v1.0/"
            f"shares/{encoded}/driveItem/content"
        )

        with requests.get(
            endpoint,
            headers={
                "Authorization":
                    f"Bearer {token}",
            },
            timeout=120,
            allow_redirects=True,
        ) as response:
            if not response.ok:
                detail = (
                    response.text[:1000]
                    if response.text
                    else ""
                )

                raise RuntimeError(
                    "No se pudo descargar el Excel "
                    "desde SharePoint/OneDrive. "
                    f"HTTP {response.status_code}. "
                    f"{detail}"
                )

            content = response.content

        if not content:
            raise RuntimeError(
                "Graph devolvio "
                "un archivo vacio."
            )

        data = self._read_provider_sheet(
            BytesIO(content)
        )

        self._validate_columns(
            data
        )

        return data

    def _read_provider_sheet(
        self,
        source,
    ) -> pd.DataFrame:
        with pd.ExcelFile(
            source
        ) as workbook:
            if self.SHEET_NAME not in (
                workbook.sheet_names
            ):
                raise ValueError(
                    "El Excel no contiene la hoja "
                    f"'{self.SHEET_NAME}'. "
                    "Hojas encontradas: "
                    + ", ".join(
                        workbook.sheet_names
                    )
                )

            data = pd.read_excel(
                workbook,
                sheet_name=self.SHEET_NAME,
                dtype=str,
                keep_default_na=False,
            )

        return (
            self._drop_empty_business_rows(
                data
            )
        )


    def _drop_empty_business_rows(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        business_headers = {
            "nombre",
            "apellido",
            "apellidomaterno",
            "nombrecliente",
            "rucproveedor",
            "nombreproveedor",
            "correo",
            "docidentidad",
        }

        columns = [
            column
            for column in df.columns
            if self._normalize_header(
                column
            )
            in business_headers
        ]

        if not columns:
            return df.copy()

        work = df.copy()

        non_empty = (
            work[columns]
            .fillna("")
            .astype(str)
            .apply(
                lambda column:
                    column.str.strip()
            )
            .ne("")
            .any(axis=1)
        )

        return (
            work[non_empty]
            .copy()
        )

    def _validate_columns(
        self,
        df: pd.DataFrame,
    ) -> None:
        normalized = {
            self._normalize_header(
                column
            )
            for column in df.columns
        }

        missing = [
            column
            for column
            in self.REQUIRED_COLUMNS
            if (
                self._normalize_header(
                    column
                )
                not in normalized
            )
        ]

        if missing:
            raise ValueError(
                "Faltan columnas obligatorias "
                "en la hoja Proveedores: "
                + ", ".join(
                    missing
                )
            )

    @staticmethod
    def _cell_text(
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

    @staticmethod
    def _encode_shared_url(
        shared_url: str,
    ) -> str:
        encoded = urlsafe_b64encode(
            shared_url.encode(
                "utf-8"
            )
        ).decode(
            "ascii"
        ).rstrip("=")

        return "u!" + encoded
