import pandas as pd


class PortalUserResultService:

    def process(
        self,
        sent_users: pd.DataFrame,
        error_excel_path: str,
    ) -> pd.DataFrame:

        if sent_users.empty:
            return pd.DataFrame()

        required = {"_item_id", "email"}

        missing = required - set(sent_users.columns)

        if missing:
            raise ValueError(
                f"Faltan columnas en usuarios enviados: {sorted(missing)}"
            )

        errors = pd.read_excel(
            error_excel_path,
            dtype=str
        )

        # Normalizar encabezados del Excel del portal
        column_map = {
            str(col).strip().lower(): col
            for col in errors.columns
        }

        email_col = column_map.get("email")
        message_col = column_map.get("mensaje de error")

        if email_col is None:
            raise ValueError(
                "El Excel de respuesta no contiene la columna Email."
            )

        if message_col is None:
            raise ValueError(
                "El Excel de respuesta no contiene la columna Mensaje de Error."
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

            error_by_email[email] = message

        results = []

        for _, row in sent_users.iterrows():

            email = self._normalize_email(
                row.get("email")
            )

            if not email:
                continue

            if email in error_by_email:
                creado = 2
                mensaje = error_by_email[email]

            else:
                creado = 1
                mensaje = ""

            results.append({
                "_item_id": str(row.get("_item_id")),
                "email": email,
                "creado": creado,
                "mensaje_error": mensaje,
            })

        return pd.DataFrame(results)

    def _normalize_email(self, value) -> str:
        if value is None or pd.isna(value):
            return ""

        return (
            str(value)
            .strip()
            .lower()
            .replace(" ", "")
        )
