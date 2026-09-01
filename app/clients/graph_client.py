import time
import requests
from app.auth.msal_auth import MsalAuthService


class GraphClient:
    BASE_URL = "https://graph.microsoft.com/v1.0"

    RETRY_STATUS = {429, 500, 502, 503, 504}

    def __init__(self):
        self.auth_service = MsalAuthService()

    def _get_headers(self):
        token = self.auth_service.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, url: str, params: dict | None = None, json_body: dict | None = None, max_retries: int = 5):
        last_error = None

        for attempt in range(max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self._get_headers(),
                    params=params,
                    json=json_body,
                    timeout=60,
                )

                if response.status_code in self.RETRY_STATUS:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and str(retry_after).isdigit():
                        wait_seconds = int(retry_after)
                    else:
                        wait_seconds = min(2 ** attempt, 30)

                    if attempt < max_retries - 1:
                        time.sleep(wait_seconds)
                        continue

                response.raise_for_status()

                if not response.text:
                    return None

                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type.lower():
                    return response.json()

                return response.text

            except requests.RequestException as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(min(2 ** attempt, 30))
                    continue
                break

        detail = ""
        if last_error is not None and hasattr(last_error, "response") and last_error.response is not None:
            resp = last_error.response
            detail = f" | status={resp.status_code} | body={resp.text}"

        raise RuntimeError(f"Error en llamada Graph: {method} {url}{detail}")

    def get(self, endpoint: str, params: dict | None = None):
        url = f"{self.BASE_URL}{endpoint}"
        return self._request("GET", url, params=params)

    def get_all_pages(self, endpoint: str, params: dict | None = None) -> list[dict]:
        url = f"{self.BASE_URL}{endpoint}"
        all_items = []
        next_url = url
        next_params = params.copy() if params else None

        while next_url:
            data = self._request("GET", next_url, params=next_params)

            if not isinstance(data, dict):
                raise RuntimeError(f"Respuesta inesperada de Graph en paginacion: {next_url}")

            values = data.get("value", [])
            if values:
                all_items.extend(values)

            next_url = data.get("@odata.nextLink")
            next_params = None

        return all_items

    def patch(self, endpoint: str, json_body: dict):
        url = f"{self.BASE_URL}{endpoint}"
        return self._request("PATCH", url, json_body=json_body)

    def post(self, endpoint: str, json_body: dict):
        url = f"{self.BASE_URL}{endpoint}"
        return self._request("POST", url, json_body=json_body)

    def batch(self, requests_list: list[dict]):
        payload = {"requests": requests_list}
        return self.post("/$batch", payload)