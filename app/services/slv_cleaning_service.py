import re
import pandas as pd


class SlvCleaningService:

    REQUIRED_COLUMNS = [
        "_item_id",
        "pais",
        "creado",
        "nombre",
        "apellido",
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

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = None

        df["pais"] = df["pais"].apply(
            lambda x: self._clean_text(x).upper()
        )

        df["nombre"] = df["nombre"].apply(
            lambda x: self._clean_text(x).upper()
        )

        df["apellido"] = df["apellido"].apply(
            lambda x: self._clean_text(x).upper()
        )

        df["email"] = df["email"].apply(
            self._clean_email
        )

        df["telefono"] = df["telefono"].apply(
            self._clean_phone
        )

        df["numero_documento"] = df["numero_documento"].apply(
            self._only_digits
        )

        df["nit_proveedor"] = df["nit_proveedor"].apply(
            self._only_digits
        )

        df["nombre_proveedor"] = df["nombre_proveedor"].apply(
            lambda x: self._clean_text(x).upper()
        )

        # nombre_cliente se conserva con formato legible
        df["nombre_cliente"] = df["nombre_cliente"].apply(
            self._clean_text
        )

        df["perfil"] = "PROVEEDOR"
        df["tipo_documento"] = "DUI"

        df["dui_valido"] = df["numero_documento"].apply(
            self._valid_dui
        )

        df["nit_valido"] = df["nit_proveedor"].apply(
            self._valid_nit
        )

        df["telefono_valido"] = df["telefono"].apply(
            self._valid_phone
        )

        df["correo_valido"] = df["email"].apply(
            self._valid_email
        )

        df["observaciones"] = df.apply(
            self._build_observaciones,
            axis=1
        )

        df["estado"] = df["observaciones"].apply(
            lambda x: "OK"
            if x is None or pd.isna(x) or str(x).strip() == ""
            else "ERROR"
        )

        return df

    def _clean_text(self, value) -> str:
        if value is None or pd.isna(value):
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value)
        ).strip()

    def _only_digits(self, value) -> str:
        return re.sub(
            r"\D",
            "",
            self._clean_text(value)
        )

    def _clean_email(self, value) -> str:
        return (
            self._clean_text(value)
            .replace(" ", "")
            .lower()
        )

    def _clean_phone(self, value) -> str:
        digits = self._only_digits(value)

        if digits.startswith("503") and len(digits) == 11:
            digits = digits[3:]

        return digits

    def _valid_dui(self, value) -> bool:
        return bool(
            re.fullmatch(r"\d{9}", value or "")
        )

    def _valid_nit(self, value) -> bool:
        return bool(
            re.fullmatch(r"\d{9}|\d{14}", value or "")
        )

    def _valid_phone(self, value) -> bool:
        return bool(
            re.fullmatch(r"\d{8}", value or "")
        )

    def _valid_email(self, value) -> bool:
        return bool(
            re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                value or ""
            )
        )

    def _build_observaciones(self, row) -> str | None:
        errores = []

        if row.get("pais") != "SLV":
            errores.append("Pais invalido")

        if not row.get("nombre"):
            errores.append("Nombre vacio")

        if not row.get("apellido"):
            errores.append("Apellido vacio")

        if not row.get("dui_valido"):
            errores.append("DUI invalido")

        if not row.get("nit_valido"):
            errores.append("NIT invalido")

        if not row.get("telefono_valido"):
            errores.append("Telefono invalido")

        if not row.get("correo_valido"):
            errores.append("Correo invalido")

        if not row.get("nombre_proveedor"):
            errores.append("Empresa proveedor vacia")

        if not row.get("nombre_cliente"):
            errores.append("Cliente vacio")

        return " | ".join(errores) if errores else None

