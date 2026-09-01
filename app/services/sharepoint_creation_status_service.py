import pandas as pd

from app.clients.sharepoint_client import SharePointClient
from app.config.settings import settings


class SharePointCreationStatusService:

    VALID_STATES = {1, 2}

    def __init__(self):
        self.client = SharePointClient()

    def apply(
        self,
        results: pd.DataFrame,
        dry_run: bool = True,
    ) -> dict:

        required = {"_item_id", "creado"}

        missing = required - set(results.columns)

        if missing:
            raise ValueError(
                f"Faltan columnas: {sorted(missing)}"
            )

        # Leer estado actual de SharePoint una sola vez
        items = self.client.get_list_items(
            settings.SHAREPOINT_LIST_NAME
        )

        current_states = {}

        for item in items:
            item_id = str(item.get("id"))
            fields = item.get("fields", {})

            value = fields.get("CREADO")

            if value is None or str(value).strip() == "":
                current = 0
            else:
                try:
                    current = int(float(value))
                except (TypeError, ValueError):
                    current = None

            current_states[item_id] = current

        updated = 0
        skipped = 0
        failed = []
        preview = []

        for _, row in results.iterrows():

            item_id = str(
                row.get("_item_id") or ""
            ).strip()

            try:
                desired = int(row.get("creado"))
            except (TypeError, ValueError):
                desired = None

            if not item_id:
                failed.append({
                    "item_id": item_id,
                    "error": "Item ID vacio",
                })
                continue

            if desired not in self.VALID_STATES:
                failed.append({
                    "item_id": item_id,
                    "error": f"CREADO invalido: {desired}",
                })
                continue

            if item_id not in current_states:
                failed.append({
                    "item_id": item_id,
                    "error": "Item no encontrado en SharePoint",
                })
                continue

            current = current_states[item_id]

            preview.append({
                "_item_id": item_id,
                "actual": current,
                "nuevo": desired,
            })

            # Ya tiene exactamente el resultado deseado
            if current == desired:
                skipped += 1
                continue

            # No sobrescribir resultados previamente cerrados
            if current in {1, 2}:
                failed.append({
                    "item_id": item_id,
                    "error": (
                        f"Conflicto: SharePoint tiene CREADO={current} "
                        f"y se intento colocar {desired}"
                    ),
                })
                continue

            if dry_run:
                continue

            try:
                self.client.update_list_item_fields(
                    list_name=settings.SHAREPOINT_LIST_NAME,
                    item_id=item_id,
                    fields={
                        "CREADO": desired
                    }
                )

                updated += 1

            except Exception as e:
                failed.append({
                    "item_id": item_id,
                    "error": str(e),
                })

        return {
            "dry_run": dry_run,
            "total": len(results),
            "updated": updated,
            "skipped": skipped,
            "failed": failed,
            "preview": preview,
        }
