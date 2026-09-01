import re
import pandas as pd


class PerCleaningService:

    PERFILES_VALIDOS = {"RANSA", "CLIENTE", "PROVEEDOR"}

    REQUIRED_COLUMNS = [
        "tipo_documento",
        "numero_documento",
        "nombre",
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

    COLUMNS_SKIP_GENERAL_NORMALIZATION = {
        "nombre_cliente",
    }

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # asegurar columnas esperadas
        for col in self.REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = None

        # limpieza general, evitando columnas que se usaran para match semantico
        df = self._normalize_text(df)

        df["email"] = df["email"].apply(self._safe_apply(self._clean_email))

        for col in ["nombre", "apellido_pat", "apellido_mat"]:
            df[col] = df[col].apply(self._safe_apply(self._clean_name))

        df["numero_documento"] = df["numero_documento"].apply(
            self._safe_apply(self._normalize_integer_id)
        )

        df["ruc_cliente"] = df["ruc_cliente"].apply(
            self._safe_apply(self._normalize_integer_id)
        )

        df["ruc_proveedor"] = df["ruc_proveedor"].apply(
            self._safe_apply(self._normalize_integer_id)
        )

        df["num_telefono"] = df["num_telefono"].apply(
            self._safe_apply(self._normalize_phone)
        )

        df["tipo_telefono"] = df["num_telefono"].apply(
            self._safe_apply(self._clasificar_telefono, default="INVALIDO")
        )

        df["perfil"] = df["perfil"].apply(
            self._safe_apply(self._normalize_perfil)
        )

        df["dni_valido"] = df["numero_documento"].apply(
            self._safe_apply(self._validar_dni, default=False)
        )

        df["correo_valido"] = df["email"].apply(
            self._safe_apply(self._validar_correo, default=False)
        )

        df["ruc_cliente_valido"] = df["ruc_cliente"].apply(
            self._safe_apply(self._validar_ruc, default=False)
        )

        df["ruc_proveedor_valido"] = df["ruc_proveedor"].apply(
            self._safe_apply(self._validar_ruc, default=False)
        )

        df["observaciones"] = df.apply(self._build_observaciones, axis=1)

        df["estado"] = df["observaciones"].apply(
            lambda x: "OK" if self._is_empty(x) else "ERROR"
        )

        return df

    def _safe_apply(self, func, default=None):
        def wrapper(value):
            try:
                return func(value)
            except Exception:
                return default
        return wrapper

    def _is_empty(self, value) -> bool:
        if pd.isna(value):
            return True
        return str(value).strip() == ""

    def _safe_str(self, value) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    def _normalize_text(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if col in self.COLUMNS_SKIP_GENERAL_NORMALIZATION:
                continue
            df[col] = df[col].apply(self._safe_apply(self._clean_value))
        return df

    def _clean_value(self, value):
        text = self._safe_str(value)
        if not text:
            return None

        text = re.sub(r"\s+", " ", text)
        return text.upper() if text else None

    def _clean_email(self, correo):
        text = self._safe_str(correo)
        if not text:
            return None

        text = text.replace(" ", "")
        return text.lower() if text else None

    def _clean_name(self, value):
        text = self._safe_str(value)
        if not text:
            return None

        text = re.sub(r"[^A-Za-zÃÃ‰ÃÃ“ÃšÃ‘Ã¡Ã©Ã­Ã³ÃºÃ± ]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        return text.upper() if text else None

    def _normalize_integer_id(self, value):
        text = self._safe_str(value)
        if not text:
            return None

        if re.fullmatch(r"\d+\.0", text):
            text = text[:-2]

        digits = re.sub(r"\D", "", text)
        return digits if digits else None

    def _normalize_phone(self, telefono):
        text = self._safe_str(telefono)
        if not text:
            return None

        digits = re.sub(r"\D", "", text)
        return digits if digits else None

    def _clasificar_telefono(self, telefono):
        text = self._safe_str(telefono)
        if not text:
            return "VACIO"

        digits = re.sub(r"\D", "", text)
        if not digits:
            return "VACIO"

        if digits.startswith("51"):
            digits = digits[2:]

        if re.fullmatch(r"9\d{8}", digits):
            return "CELULAR_PE"

        if re.fullmatch(r"\d{7,8}", digits):
            return "FIJO_PE"

        if len(digits) > 9:
            return "EXTRANJERO"

        return "INVALIDO"

    def _normalize_perfil(self, perfil):
        text = self._safe_str(perfil)
        return text.upper() if text else None

    def _validar_dni(self, dni):
        dni = self._normalize_integer_id(dni)
        if not dni:
            return False
        return bool(re.fullmatch(r"\d{8}", dni))

    def _validar_ruc(self, ruc):
        ruc = self._normalize_integer_id(ruc)
        if not ruc:
            return False
        return bool(re.fullmatch(r"\d{11}", ruc))

    def _validar_correo(self, correo):
        text = self._safe_str(correo)
        if not text:
            return False

        return bool(re.fullmatch(r"[^@]+@[^@]+\.[^@]+", text))

    def _build_observaciones(self, row):
        errores = []

        if self._is_empty(row.get("numero_documento")):
            errores.append("DNI vacio")
        elif not bool(row.get("dni_valido")):
            errores.append("DNI invalido")

        if self._is_empty(row.get("nombre")):
            errores.append("Nombre vacio")

        if self._is_empty(row.get("apellido_pat")):
            errores.append("Apellido paterno vacio")

        # apellido materno no rompe el flujo, pero se marca como observacion
        #if self._is_empty(row.get("apellido_mat")):
        #    errores.append("Apellido materno vacio")

        if self._is_empty(row.get("email")):
            errores.append("Correo vacio")
        elif not bool(row.get("correo_valido")):
            errores.append("Correo invalido")

        if row.get("tipo_telefono") == "INVALIDO":
            errores.append("Telefono invalido")

        perfil = row.get("perfil")

        if perfil not in self.PERFILES_VALIDOS:
            errores.append("Perfil invalido")

        elif perfil == "CLIENTE":
            if self._is_empty(row.get("nombre_cliente")):
                errores.append("Falta nombre cliente")

            if self._is_empty(row.get("ruc_cliente")):
                errores.append("Falta RUC cliente")
            elif not bool(row.get("ruc_cliente_valido")):
                errores.append("RUC cliente invalido")

        elif perfil == "PROVEEDOR":
            if self._is_empty(row.get("nombre_proveedor")):
                errores.append("Falta nombre proveedor")

            if self._is_empty(row.get("ruc_proveedor")):
                errores.append("Falta RUC proveedor")
            elif not bool(row.get("ruc_proveedor_valido")):
                errores.append("RUC proveedor invalido")

            if self._is_empty(row.get("nombre_cliente")):
                errores.append("Falta nombre cliente")

        elif perfil == "RANSA":
            if self._is_empty(row.get("negocio")):
                errores.append("Falta negocio")

            if self._is_empty(row.get("tipo_cargo")):
                errores.append("Falta tipo cargo")

        return " | ".join(errores) if errores else None
