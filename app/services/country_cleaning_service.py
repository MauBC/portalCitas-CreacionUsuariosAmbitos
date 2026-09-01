import pandas as pd

from app.services.per_cleaning_service import PerCleaningService
from app.services.slv_cleaning_service import SlvCleaningService


class CountryCleaningService:

    def __init__(self):
        self.per_cleaner = PerCleaningService()
        self.slv_cleaner = SlvCleaningService()

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        df = df.copy()

        # Compatibilidad con el flujo antiguo de Peru.
        # Si no existe pais, asumimos PER.
        if "pais" not in df.columns:
            df["pais"] = "PER"

        df["pais"] = (
            df["pais"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        results = []

        for pais, group in df.groupby("pais", dropna=False):

            if pais == "PER":
                cleaned = self.per_cleaner.clean(group)

            elif pais == "SLV":
                cleaned = self.slv_cleaner.clean(group)

            else:
                cleaned = group.copy()
                cleaned["estado"] = "ERROR"
                cleaned["observaciones"] = f"Pais no soportado: {pais}"

            results.append(cleaned)

        if not results:
            return df

        result = pd.concat(results).sort_index()

        return result

