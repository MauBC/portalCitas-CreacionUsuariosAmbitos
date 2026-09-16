from app.clients.graph_client import GraphClient
from app.config.settings import settings


class SharePointClient:
    def __init__(self):
        self.graph = GraphClient()
        self._site_id_cache = None
        self._list_id_cache = {}

    def get_site_id(self) -> str:
        if self._site_id_cache:
            return self._site_id_cache

        endpoint = (
            f"/sites/{settings.SHAREPOINT_HOSTNAME}:"
            f"{settings.SHAREPOINT_SITE_PATH}"
        )
        data = self.graph.get(endpoint)
        self._site_id_cache = data["id"]
        return self._site_id_cache

    def get_lists(self):
        site_id = self.get_site_id()
        endpoint = f"/sites/{site_id}/lists"
        return self.graph.get_all_pages(endpoint)

    def get_list_by_name(self, list_name: str):
        target = list_name.strip().lower()

        for item in self.get_lists():
            display_name = str(
                item.get("displayName") or ""
            ).strip().lower()
            internal_name = str(
                item.get("name") or ""
            ).strip().lower()

            if target in {
                display_name,
                internal_name,
            }:
                return item

        raise RuntimeError(
            f"No se encontro la lista '{list_name}'."
        )

    def get_list_id(self, list_name: str) -> str:
        key = list_name.strip().lower()

        if key in self._list_id_cache:
            return self._list_id_cache[key]

        target_list = self.get_list_by_name(list_name)
        list_id = target_list["id"]
        self._list_id_cache[key] = list_id
        return list_id

    def get_list_items(self, list_name: str):
        site_id = self.get_site_id()
        list_id = self.get_list_id(list_name)

        endpoint = (
            f"/sites/{site_id}/lists/"
            f"{list_id}/items"
        )
        params = {"$expand": "fields"}
        return self.graph.get_all_pages(
            endpoint,
            params=params,
        )

    def get_list_columns(self, list_name: str):
        site_id = self.get_site_id()
        list_id = self.get_list_id(list_name)

        endpoint = (
            f"/sites/{site_id}/lists/"
            f"{list_id}/columns"
        )
        return self.graph.get_all_pages(endpoint)

    def update_list_item_fields(
        self,
        list_name: str,
        item_id: str,
        fields: dict,
    ):
        site_id = self.get_site_id()
        list_id = self.get_list_id(list_name)

        endpoint = (
            f"/sites/{site_id}/lists/{list_id}/items/"
            f"{item_id}/fields"
        )
        return self.graph.patch(
            endpoint,
            fields,
        )
