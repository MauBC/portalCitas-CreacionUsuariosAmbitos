import pandas as pd


class ProviderCreationStatusService:
    PENDING = 0
    CREATED = 1
    ERROR = 2

    VALID_VALUES = {
        PENDING,
        CREATED,
        ERROR,
    }

    STATUS_PENDING = "PENDIENTE"
    STATUS_CREATED = "YA_CREADO"
    STATUS_PREVIOUS_ERROR = "ERROR_PREVIO"
    STATUS_INVALID = "ERROR_ESTADO_CREADO"
    STATUS_VALIDATION_ERROR = "ERROR_VALIDACION"

    INVALID_MESSAGE = (
        "CREADO INVALIDO: SOLO SE PERMITEN 0, 1 O 2"
    )

    def apply_source_status(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        result = df.copy()

        if result.empty:
            return result

        if "creado" not in result.columns:
            result["creado"] = None

        if "estado" not in result.columns:
            result["estado"] = "OK"

        if "observaciones" not in result.columns:
            result["observaciones"] = ""

        result["creado_origen"] = result["creado"]

        normalized = result["creado"].map(
            self.normalize
        )

        result["creado"] = normalized
        result["estado_proceso"] = ""

        pending_mask = normalized.eq(
            self.PENDING
        )
        created_mask = normalized.eq(
            self.CREATED
        )
        previous_error_mask = normalized.eq(
            self.ERROR
        )
        invalid_mask = normalized.isna()

        result.loc[
            pending_mask,
            "estado_proceso",
        ] = self.STATUS_PENDING

        result.loc[
            created_mask,
            "estado",
        ] = "OMITIDO"

        result.loc[
            created_mask,
            "estado_proceso",
        ] = self.STATUS_CREATED

        result.loc[
            previous_error_mask,
            "estado",
        ] = "OMITIDO"

        result.loc[
            previous_error_mask,
            "estado_proceso",
        ] = self.STATUS_PREVIOUS_ERROR

        result.loc[
            invalid_mask,
            "estado",
        ] = "ERROR"

        result.loc[
            invalid_mask,
            "estado_proceso",
        ] = self.STATUS_INVALID

        result.loc[
            invalid_mask,
            "observaciones",
        ] = result.loc[
            invalid_mask,
            "observaciones",
        ].apply(
            lambda value:
                self._append_message(
                    value,
                    self.INVALID_MESSAGE,
                )
        )

        return result

    def finalize(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        result = df.copy()

        if result.empty:
            return result

        pending_error_mask = (
            result["creado"].eq(
                self.PENDING
            )
            & result["estado"].eq(
                "ERROR"
            )
        )

        result.loc[
            pending_error_mask,
            "creado",
        ] = self.ERROR

        result.loc[
            pending_error_mask,
            "estado_proceso",
        ] = self.STATUS_VALIDATION_ERROR

        return result

    def summarize(
        self,
        df: pd.DataFrame,
    ) -> dict:
        if df.empty:
            return {
                "pending": 0,
                "already_created": 0,
                "previous_errors": 0,
                "invalid_status": 0,
                "validation_errors": 0,
            }

        status = (
            df["estado_proceso"]
            .fillna("")
            .astype(str)
        )

        return {
            "pending":
                int(
                    status.eq(
                        self.STATUS_PENDING
                    ).sum()
                ),
            "already_created":
                int(
                    status.eq(
                        self.STATUS_CREATED
                    ).sum()
                ),
            "previous_errors":
                int(
                    status.eq(
                        self.STATUS_PREVIOUS_ERROR
                    ).sum()
                ),
            "invalid_status":
                int(
                    status.eq(
                        self.STATUS_INVALID
                    ).sum()
                ),
            "validation_errors":
                int(
                    status.eq(
                        self.STATUS_VALIDATION_ERROR
                    ).sum()
                ),
        }

    @classmethod
    def normalize(
        cls,
        value,
    ):
        if value is None:
            return cls.PENDING

        try:
            if pd.isna(value):
                return cls.PENDING
        except (TypeError, ValueError):
            pass

        text = str(value).strip()

        if not text:
            return cls.PENDING

        try:
            numeric = float(text)
        except (TypeError, ValueError):
            return None

        if not numeric.is_integer():
            return None

        integer = int(numeric)

        if integer not in cls.VALID_VALUES:
            return None

        return integer


    @staticmethod
    def _append_message(
        current,
        message: str,
    ) -> str:
        current_text = str(
            current or ""
        ).strip()

        if not current_text:
            return message

        parts = [
            part.strip()
            for part in current_text.split("|")
            if part.strip()
        ]

        if message not in parts:
            parts.append(message)

        return " | ".join(parts)
