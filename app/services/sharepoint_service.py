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
        columns = self.client.get_list_columns(
            settings.SHAREPOINT_LIST_NAME
        )
        mapping = {}

        for column in columns:
            internal_name = column.get("name")
            display_name = column.get("displayName")

            if not internal_name or not display_name:
                continue

            if internal_name in self.META_COLUMNS:
                continue

            mapping[internal_name] = display_name

        return mapping

    def load_form_responses_as_dataframe(self) -> pd.DataFrame:
        items = self.client.get_list_items(
            settings.SHAREPOINT_LIST_NAME
        )

        rows = []

        for item in items:
            fields = item.get("fields", {})
            row = dict(fields)
            row["_item_id"] = item.get("id")
            rows.append(row)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        columns_to_keep = [
            column
            for column in df.columns
            if column not in self.META_COLUMNS
        ]
        df = df[columns_to_keep].copy()

        mapping = self.get_column_mapping()
        df = df.rename(columns=mapping)

        for column in [
            "estado_validacion",
            "motivo_error",
        ]:
            if column not in df.columns:
                df[column] = None

        if settings.FILTER_ONLY_PENDING_SHAREPOINT:
            if "CREADO" not in df.columns:
                raise ValueError(
                    "La lista SharePoint no contiene la columna CREADO."
                )

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

        return df
