import unicodedata

import pandas as pd


class PortalUserResultService:

    ACCOUNT_AVAILABLE_MESSAGES = (
        "CORREO DUPLICADO",
        "USUARIO YA EXISTE",
    )

    def process(
        self,
        sent_users: pd.DataFrame,
        error_excel_path: str,
    ) -> pd.DataFrame:

        if sent_users.empty:
            return pd.DataFrame()

        required = {
            "_item_id",
            "email",
        }

        missing = required - set(
            sent_users.columns
        )

        if missing:
            raise ValueError(
                "Faltan columnas en usuarios enviados: "
                f"{sorted(missing)}"
            )

        errors = pd.read_excel(
            error_excel_path,
            dtype=str,
        )

        column_map = {
            str(col).strip().lower(): col
            for col in errors.columns
        }

        email_col = column_map.get(
            "email"
        )

        message_col = column_map.get(
            "mensaje de error"
        )

        if email_col is None:
            raise ValueError(
                "El Excel de respuesta no contiene "
                "la columna Email."
            )

        if message_col is None:
            raise ValueError(
                "El Excel de respuesta no contiene "
                "la columna Mensaje de Error."
            )

        error_by_email = {}

        for _, row in errors.iterrows():

            email = self._normalize_email(
                row.get(email_col)
            )

            if not email:
                continue

            message = str(
                row.get(message_col) or ""
            ).strip()

            error_by_email.setdefault(
                email,
                [],
            ).append(
                message
            )

        results = []

        for _, row in sent_users.iterrows():

            email = self._normalize_email(
                row.get("email")
            )

            if not email:
                continue

            messages = error_by_email.get(
                email,
                [],
            )

            unique_messages = list(
                dict.fromkeys(messages)
            )

            blocking_messages = [
                message
                for message in unique_messages
                if not self._account_is_available(
                    message
                )
            ]

            if blocking_messages:

                creado = 2
                estado_portal = "NO_CREADO"

            else:

                creado = 1
                estado_portal = "DISPONIBLE"

            result_row = row.to_dict()

            result_row.update({
                "_item_id":
                    str(row.get("_item_id")).strip(),
                "email":
                    email,
                "creado":
                    creado,
                "estado_portal":
                    estado_portal,
                "mensaje_error":
                    " | ".join(unique_messages),
            })

            results.append(
                result_row
            )

        return pd.DataFrame(
            results
        )

    def _account_is_available(
        self,
        message,
    ) -> bool:

        normalized = self._normalize_message(
            message
        )

        return any(
            pattern in normalized
            for pattern
            in self.ACCOUNT_AVAILABLE_MESSAGES
        )

    @staticmethod
    def _normalize_message(
        value,
    ) -> str:

        text = str(
            value or ""
        ).strip().upper()

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = "".join(
            char
            for char in text
            if not unicodedata.combining(char)
        )

        return " ".join(
            text.split()
        )

    @staticmethod
    def _normalize_email(
        value,
    ) -> str:

        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        return (
            str(value)
            .strip()
            .lower()
            .replace(" ", "")
        )
