"""Actionable hints; diagnostics remain in the existing redacted error report."""
import re


def error_guidance(error: str, trace: str = "", *, mode: str = "") -> str:
    text = f"{error}\n{trace}".lower()
    if "password authentication failed" in text:
        return "Revisa el usuario y la contraseña de PostgreSQL en la configuración."
    if "no pg_hba.conf entry" in text:
        return "Solicita al administrador revisar el acceso de tu equipo y la configuración SSL de PostgreSQL."
    if "error autenticando con microsoft" in text or "aadsts" in text:
        return "Revisa la configuración de Microsoft y la vigencia de las credenciales con el administrador."
    if re.search(r"(?:http(?:error)?\s*:?\s*|status\s*=\s*)401\b|401 client error", text):
        return "Microsoft rechazó la autenticación. Revisa las credenciales configuradas y su vigencia."
    if re.search(r"(?:http(?:error)?\s*:?\s*|status\s*=\s*)403\b|403 client error", text):
        return "Solicita al administrador revisar los permisos de la aplicación sobre el sitio, lista o archivo de SharePoint."
    if "sslerror" in text or "certificate_verify_failed" in text:
        return "Revisa la fecha del equipo, el certificado y el proxy corporativo con soporte. No desactives la verificación SSL."
    if "permissionerror" in text or "[winerror 32]" in text:
        return "Cierra el archivo en Excel y comprueba que tengas permiso para escribir en la carpeta de destino."
    if "filenotfounderror" in text:
        return "Comprueba que el archivo exista y vuelve a seleccionarlo antes de generar un nuevo preview."
    connection_problem = any(token in text for token in (
        "timed out", "timeout", "connection refused", "could not translate host name",
        "name resolution", "connectionerror", "failed to establish a new connection",
    ))
    if connection_problem:
        database = any(token in text for token in ("psycopg2", "postgresql", "connection to server"))
        if database:
            return "Comprueba que la VPN esté conectada y que PostgreSQL sea accesible. Después vuelve a intentar la operación."
        if mode == "apply":
            return (
                "Se perdió la conexión o se agotó el tiempo de espera. El resultado de la escritura puede ser incierto. "
                "Comprueba el estado publicado en SharePoint y genera un nuevo preview antes de volver a aplicar."
            )
        return "Comprueba la conexión de red y el acceso a Microsoft/SharePoint. Después vuelve a intentar la operación."
    return ""
