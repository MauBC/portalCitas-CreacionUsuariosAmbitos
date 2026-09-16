import pandas as pd

from app.services.db_validation_service import (
    DbValidationService,
)


class EmailValidationService:
    EXISTING_EMAIL_MESSAGE = (
        "CORREO YA EXISTE EN BD"
    )

    def __init__(
        self,
        db_validator:
            DbValidationService | None = None,
        country_code:
            str | None = None,
    ):
        self.country_code = str(
            country_code or ""
        ).strip().upper()

        self.db_validator = (
            db_validator
            or DbValidationService(
                country_code=
                    self.country_code
            )
        )

    @property
    def database_name(self) -> str:
        return str(
            getattr(
                self.db_validator,
                "database_name",
                "",
            )
            or ""
        )

    @staticmethod
    def normalize_email(
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

        return (
            str(value)
            .strip()
            .lower()
        )

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
            for part in (
                current_text
                .split("|")
            )
            if part.strip()
        ]

        if message not in parts:
            parts.append(
                message
            )

        return " | ".join(
            parts
        )

    def validate_existing_emails(
        self,
        df: pd.DataFrame,
    ) -> tuple[
        pd.DataFrame,
        int,
    ]:
        result = df.copy()

        if result.empty:
            return result, 0

        if (
            "email" not in result.columns
            or "estado"
            not in result.columns
        ):
            return result, 0

        if (
            "observaciones"
            not in result.columns
        ):
            result[
                "observaciones"
            ] = ""

        valid_mask = (
            result["estado"]
            .eq("OK")
        )

        if not valid_mask.any():
            return result, 0

        normalized_emails = (
            result["email"]
            .map(
                self.normalize_email
            )
        )

        emails = (
            normalized_emails[
                valid_mask
            ]
            .loc[
                lambda series:
                    series.ne("")
            ]
            .drop_duplicates()
            .tolist()
        )

        if not emails:
            return result, 0

        existing = (
            self.db_validator
            .get_existing_emails(
                emails
            )
        )

        if not existing:
            return result, 0

        duplicate_mask = (
            valid_mask
            & normalized_emails
            .isin(
                existing
            )
        )

        result.loc[
            duplicate_mask,
            "observaciones",
        ] = result.loc[
            duplicate_mask,
            "observaciones",
        ].apply(
            lambda value:
                self._append_message(
                    value,
                    self.EXISTING_EMAIL_MESSAGE,
                )
        )

        result.loc[
            duplicate_mask,
            "estado",
        ] = "ERROR"

        return (
            result,
            int(
                duplicate_mask.sum()
            ),
        )
