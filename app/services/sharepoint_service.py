import time
import pandas as pd
from app.clients.sharepoint_client import SharePointClient
from app.config.settings import settings


class SharePointService:
    META_COLUMNS = {
        "@odata.etag",
        "id",
        "ID",
        "ContentType",
        "Modified",
        "Created",
        "AuthorLookupId",
        "EditorLookupId",
        "_UIVersionString",
        "Attachments",
        "Edit",
        "ItemChildCount",
        "FolderChildCount",
        "_ComplianceFlags",
        "_ComplianceTag",
        "_ComplianceTagWrittenTime",
        "_ComplianceTagUserId",
        "AppAuthorLookupId",
        "AppEditorLookupId",
        "LinkTitle",
        "LinkTitleNoMenu",
        "DocIcon",
        "_ColorTag",
        "ComplianceAssetId",
        "_IsRecord",
        "Author",
        "Editor",
        "AppAuthor",
        "AppEditor",
        "Title",
    }

    def __init__(self):
        self.client = SharePointClient()

    def get_column_mapping(self) -> dict:
        columns = self.client.get_list_columns(settings.SHAREPOINT_LIST_NAME)
        mapping = {}

        for col in columns:
            internal_name = col.get("name")
            display_name = col.get("displayName")

            if not internal_name or not display_name:
                continue

            if internal_name in self.META_COLUMNS:
                continue

            mapping[internal_name] = display_name

        return mapping

    def load_form_responses_as_dataframe(self) -> pd.DataFrame:
        items = self.client.get_list_items(settings.SHAREPOINT_LIST_NAME)

        rows = []
        for item in items:
            fields = item.get("fields", {})
            row = dict(fields)
            row["_item_id"] = item.get("id")
            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        columns_to_keep = [col for col in df.columns if col not in self.META_COLUMNS]
        df = df[columns_to_keep].copy()

        mapping = self.get_column_mapping()
        df = df.rename(columns=mapping)

        for col in ["estado_validacion", "motivo_error"]:
            if col not in df.columns:
                df[col] = None

        if settings.FILTER_ONLY_PENDING_SHAREPOINT:

            # Flujo nuevo multipais:
            # CREADO vacio o 0 = pendiente.
            if "CREADO" in df.columns:
                creado = (
                    df["CREADO"]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                )

                df = df[
                    (creado == "")
                    | creado.isin(["0", "0.0"])
                ].copy()

            # Compatibilidad con SharePoint antiguo de Peru
            else:
                df = df[
                    df["estado_validacion"].isna()
                    | (
                        df["estado_validacion"]
                        .astype(str)
                        .str.strip()
                        == ""
                    )
                ].copy()

        return df

    def update_validation_result(
        self,
        item_id: str,
        estado_validacion: str,
        motivo_error: str | None = None,
        cliente_normalizado: str | None = None,
        observacion_validacion: str | None = None,
    ):
        """
        Actualiza solamente el resultado de validacion de FASE 1.

        IMPORTANTE:
        Este metodo NO modifica CREADO.

        CREADO se reserva para FASE 2:
            0 = pendiente
            1 = creado
            2 = no creado
        """

        observacion = (
            observacion_validacion
            if observacion_validacion is not None
            else motivo_error
        )

        payload = {
            "ESTADO_VALIDACION":
                self._clean_text(
                    estado_validacion
                ),

            "OBSERVACION_VALIDACION":
                self._clean_text(
                    observacion
                ),

            "CLIENTE_NORMALIZADO":
                self._clean_text(
                    cliente_normalizado
                ),
        }

        return self.client.update_list_item_fields(
            list_name=settings.SHAREPOINT_LIST_NAME,
            item_id=str(item_id),
            fields=payload,
        )

    @staticmethod
    def _clean_text(value) -> str:
        """
        Convierte NaN/None/etc. en cadena vacia.
        """

        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        return str(value).strip()

    @staticmethod
    def _as_bool(value) -> bool:
        """
        Convierte valores de Excel/DataFrame a booleano.
        """

        if value is True:
            return True

        if value is False or value is None:
            return False

        try:
            if pd.isna(value):
                return False
        except (TypeError, ValueError):
            pass

        text = str(value).strip().lower()

        return text in {
            "true",
            "1",
            "si",
            "s?",
            "yes",
        }

    def _build_validation_payload(
        self,
        row,
    ) -> dict:
        """
        Traduce el resultado interno de FASE 1 al estado
        visible que se guardara en SharePoint.

        LISTO_PARA_CARGA:
            usuario valido y cliente reconocido.

        ERROR_DATOS:
            DUI, telefono, email, NIT, duplicado, etc.

        REVISION_CLIENTE:
            cliente desconocido o ambiguo.
        """

        estado = (
            self._clean_text(
                row.get("estado")
            )
            .upper()
        )

        requiere_revision = self._as_bool(
            row.get(
                "requiere_revision_cliente"
            )
        )

        cliente = self._clean_text(
            row.get(
                "cliente_normalizado"
            )
        )

        # Compatibilidad con reportes donde el cliente
        # canonico queda directamente en nombre_cliente.
        if (
            not cliente
            and not requiere_revision
        ):
            cliente = self._clean_text(
                row.get(
                    "nombre_cliente"
                )
            )

        observaciones = self._clean_text(
            row.get(
                "observaciones"
            )
        )

        if requiere_revision:
            estado_sharepoint = (
                "REVISION_CLIENTE"
            )

            # En un cliente ambiguo NO queremos guardar
            # accidentalmente el texto ingresado como si
            # fuera un cliente valido.
            cliente = ""

        elif estado == "OK":
            estado_sharepoint = (
                "LISTO_PARA_CARGA"
            )

        else:
            estado_sharepoint = (
                "ERROR_DATOS"
            )

        return {
            "ESTADO_VALIDACION":
                estado_sharepoint,

            "OBSERVACION_VALIDACION":
                observaciones,

            "CLIENTE_NORMALIZADO":
                cliente,
        }

    def _chunk_list(self, items: list, size: int):
        for i in range(0, len(items), size):
            yield items[i:i + size]

    def push_validation_results_batch(self, df: pd.DataFrame, batch_size: int = 20, max_retries: int = 5):
        if df.empty:
            return {"updated": 0, "failed": []}

        if "_item_id" not in df.columns:
            raise ValueError("El DataFrame no contiene _item_id.")

        prepared = []
        for idx, row in df.iterrows():
            payload = self._build_validation_payload(row)
            prepared.append({
                "request_id": str(idx),
                "item_id": str(row["_item_id"]),
                "payload": payload,
            })

        failed = []
        updated = 0

        for group in self._chunk_list(prepared, batch_size):
            batch_requests = []
            for item in group:
                req = self.client.build_update_request(
                    list_name=settings.SHAREPOINT_LIST_NAME,
                    item_id=item["item_id"],
                    fields=item["payload"],
                    request_id=item["request_id"],
                )
                batch_requests.append(req)

            batch_response = self.client.batch_update_list_item_fields(batch_requests)
            responses = batch_response.get("responses", [])

            retry_queue = []

            for resp in responses:
                request_id = resp.get("id")
                status = resp.get("status", 0)

                original = next((x for x in group if x["request_id"] == request_id), None)
                if original is None:
                    continue

                if 200 <= status < 300:
                    updated += 1
                    continue

                if status == 429 or status in {500, 502, 503, 504}:
                    headers = resp.get("headers", {})
                    retry_after = headers.get("Retry-After") or headers.get("retry-after")
                    retry_queue.append({
                        "item": original,
                        "retry_after": int(retry_after) if retry_after and str(retry_after).isdigit() else None,
                    })
                    continue

                failed.append({
                    "item_id": original["item_id"],
                    "status": status,
                    "body": resp.get("body"),
                })

            for retry_data in retry_queue:
                item = retry_data["item"]
                success = False

                for attempt in range(max_retries):
                    wait_seconds = retry_data["retry_after"]
                    if wait_seconds is None:
                        wait_seconds = min(2 ** attempt, 30)

                    time.sleep(wait_seconds)

                    try:
                        self.update_validation_result(
                            item_id=item["item_id"],
                            estado_validacion=item["payload"]["estado_validacion"],
                            motivo_error=item["payload"]["motivo_error"],
                        )
                        updated += 1
                        success = True
                        break
                    except Exception as e:
                        last_error = str(e)

                if not success:
                    failed.append({
                        "item_id": item["item_id"],
                        "status": 429,
                        "body": last_error if "last_error" in locals() else "Retry agotado",
                    })

            time.sleep(0.5)

        return {
            "updated": updated,
            "failed": failed,
        }
