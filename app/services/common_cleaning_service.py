import re
import unicodedata

import pandas as pd


class CommonCleaningService:

    ALLOWED_NUMERIC_SEPARATORS = re.compile(
        r"^[0-9\s./-]*$"
    )

    @staticmethod
    def to_text(value) -> str:
        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        return str(value).strip()

    @classmethod
    def clean_text(
        cls,
        value,
        uppercase: bool = True,
    ) -> str:
        text = cls.to_text(value)

        if not text:
            return ""

        text = unicodedata.normalize(
            "NFKD",
            text,
        )

        text = "".join(
            char
            for char in text
            if not unicodedata.combining(char)
        )

        text = text.replace("-", " ")
        text = text.replace("/", " ")
        text = text.replace("&", " ")

        text = re.sub(
            r"[^A-Za-z0-9 ]",
            "",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if uppercase:
            text = text.upper()

        return text

    @classmethod
    def clean_email(cls, value) -> str:
        text = cls.to_text(value)

        if not text:
            return ""

        return (
            text
            .replace(" ", "")
            .lower()
        )

    @classmethod
    def clean_digits(cls, value) -> str:
        text = cls.to_text(value)

        if not text:
            return ""

        if re.fullmatch(
            r"\d+\.0",
            text,
        ):
            text = text[:-2]

        return "".join(
            char
            for char in text
            if char.isdigit()
        )

    @classmethod
    def numeric_input_has_valid_chars(
        cls,
        value,
    ) -> bool:
        text = cls.to_text(value)

        if not text:
            return False

        return bool(
            cls.ALLOWED_NUMERIC_SEPARATORS.fullmatch(
                text
            )
        )

    @staticmethod
    def valid_email(value) -> bool:
        return bool(
            re.fullmatch(
                r"[^@\s]+@[^@\s]+\.[^@\s]+",
                value or "",
            )
        )

    @staticmethod
    def valid_exact_digits(
        value,
        length: int,
    ) -> bool:
        return bool(
            re.fullmatch(
                rf"\d{{{length}}}",
                value or "",
            )
        )

    @staticmethod
    def join_messages(
        messages: list[str],
    ) -> str:
        return " | ".join(
            dict.fromkeys(messages)
        )
