import pandas as pd

from app.services.per_cleaning_service import (
    PerCleaningService,
)
from app.services.slv_cleaning_service import (
    SlvCleaningService,
)


class CountryCleaningService:

    def __init__(self):
        self.cleaners = {
            "PER": PerCleaningService(),
            "SLV": SlvCleaningService(),
        }

    def clean(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        result = df.copy()

        if "pais" not in result.columns:
            result["pais"] = "PER"

        result["pais"] = (
            result["pais"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        cleaned_groups = []

        for country_code, group in result.groupby(
            "pais",
            dropna=False,
            sort=False,
        ):
            cleaner = self.cleaners.get(
                country_code
            )

            if cleaner is None:
                invalid = group.copy()
                invalid["estado"] = "ERROR"
                invalid["observaciones"] = (
                    f"PAIS NO SOPORTADO: "
                    f"{country_code}"
                )
                invalid["advertencias"] = ""
                cleaned_groups.append(
                    invalid
                )
                continue

            cleaned_groups.append(
                cleaner.clean(group)
            )

        if not cleaned_groups:
            return result

        return (
            pd.concat(
                cleaned_groups
            )
            .sort_index()
        )
