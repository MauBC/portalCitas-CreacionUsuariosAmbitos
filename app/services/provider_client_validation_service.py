import re
import unicodedata

import pandas as pd


class ProviderClientValidationService:
    PER_CLIENT = "DOLLARCITY"

    PER_ALIASES = {
        "DOLLARCITY",
        "DOLARCITY",
        "DOLLACITY",
        "DOLLAYCITY",
    }

    @staticmethod
    def _normalize(value) -> str:
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

        text = str(
            value
        ).strip().upper()

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = "".join(
            char
            for char in text
            if not unicodedata.combining(
                char
            )
        )

        return re.sub(
            r"[^A-Z0-9]+",
            "",
            text,
        )

    @staticmethod
    def _append_message(
        current,
        message: str,
    ) -> str:
        text = str(
            current or ""
        ).strip()

        if text.lower() == "nan":
            text = ""

        if not text:
            return message

        parts = [
            part.strip()
            for part in text.split("|")
            if part.strip()
        ]

        if message not in parts:
            parts.append(
                message
            )

        return " | ".join(
            parts
        )

    def apply(
        self,
        df: pd.DataFrame,
        country_code: str,
    ) -> pd.DataFrame:
        result = df.copy()

        country = str(
            country_code or ""
        ).strip().upper()

        if (
            country != "PER"
            or result.empty
        ):
            return result

        if (
            "nombre_cliente"
            not in result.columns
        ):
            return result

        if (
            "observaciones"
            not in result.columns
        ):
            result[
                "observaciones"
            ] = ""

        if "estado" not in result.columns:
            result["estado"] = "OK"

        result[
            "cliente_validacion"
        ] = ""

        for index, row in result.iterrows():
            original = str(
                row.get(
                    "nombre_cliente"
                )
                or ""
            ).strip()

            normalized = self._normalize(
                original
            )

            if not normalized:
                result.loc[
                    index,
                    "cliente_validacion",
                ] = "VACIO"

                continue

            if normalized in self.PER_ALIASES:
                result.loc[
                    index,
                    "nombre_cliente",
                ] = self.PER_CLIENT

                result.loc[
                    index,
                    "cliente_validacion",
                ] = (
                    "CORREGIDO_DOLLARCITY"
                    if normalized
                    != self.PER_CLIENT
                    else "DOLLARCITY"
                )

                continue

            message = (
                "CLIENTE NO RECONOCIDO: "
                + original.upper()
            )

            result.loc[
                index,
                "observaciones",
            ] = self._append_message(
                result.loc[
                    index,
                    "observaciones",
                ],
                message,
            )

            result.loc[
                index,
                "estado",
            ] = "ERROR"

            result.loc[
                index,
                "cliente_validacion",
            ] = "NO_RECONOCIDO"

        return result
