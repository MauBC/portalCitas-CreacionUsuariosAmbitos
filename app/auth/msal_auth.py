import msal
from app.config.settings import settings

class MsalAuthService:
    def __init__(self):
        self.authority = f"https://login.microsoftonline.com/{settings.MS_TENANT_ID}"
        self.app = msal.ConfidentialClientApplication(
            client_id=settings.MS_CLIENT_ID,
            client_credential=settings.MS_CLIENT_SECRET,
            authority=self.authority,
        )

    def get_access_token(self) -> str:
        result = self.app.acquire_token_for_client(
            scopes=[settings.MS_GRAPH_SCOPE]
        )

        if "access_token" not in result:
            error = result.get("error", "unknown_error")
            description = result.get("error_description", "No se pudo obtener el token.")
            raise RuntimeError(f"Error autenticando con Microsoft: {error} - {description}")

        return result["access_token"]