from _bootstrap import ROOT

from pathlib import Path

from app.config.settings import settings
from app.clients.sharepoint_client import SharePointClient
from app.services.db_validation_service import DbValidationService
from app.services.ambitos_config_service import AmbitosConfigService


print("=" * 110)
print("TEST 01 - SISTEMA / CONFIGURACION / CONEXIONES")
print("=" * 110)

errors = []
warnings = []


def ok(message):
    print(f"[OK] {message}")


def fail(message):
    print(f"[ERROR] {message}")
    errors.append(message)


def warn(message):
    print(f"[WARN] {message}")
    warnings.append(message)


# =============================================================================
# 1. ARCHIVO .ENV
# =============================================================================

print()
print("-" * 110)
print("1. ARCHIVO .ENV")
print("-" * 110)

env_path = Path(ROOT) / ".env"

if env_path.exists():
    ok(f".env encontrado: {env_path}")

    raw = env_path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        fail(
            ".env contiene BOM UTF-8. "
            "Esto puede impedir que MS_TENANT_ID sea reconocido."
        )
    else:
        ok(".env esta guardado sin BOM")

else:
    fail(".env no existe")


# =============================================================================
# 2. VARIABLES OBLIGATORIAS
# =============================================================================

print()
print("-" * 110)
print("2. VARIABLES DE ENTORNO")
print("-" * 110)

required_settings = [
    # Microsoft
    "MS_TENANT_ID",
    "MS_CLIENT_ID",
    "MS_CLIENT_SECRET",
    "MS_GRAPH_SCOPE",

    # SharePoint
    "SHAREPOINT_HOSTNAME",
    "SHAREPOINT_SITE_PATH",
    "SHAREPOINT_LIST_NAME",

    # PostgreSQL
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
]

for variable in required_settings:

    value = getattr(
        settings,
        variable,
        None,
    )

    if value:
        ok(f"{variable}: CONFIGURADO")
    else:
        fail(f"{variable}: VACIO / NO CONFIGURADO")


# =============================================================================
# 3. SHAREPOINT / MICROSOFT GRAPH
# =============================================================================

print()
print("-" * 110)
print("3. MICROSOFT GRAPH / SHAREPOINT")
print("-" * 110)

try:

    sp_client = SharePointClient()

    site_id = sp_client.get_site_id()

    if site_id:
        ok("Autenticacion Microsoft correcta")
        ok("Site SharePoint encontrado")
    else:
        fail("No se obtuvo Site ID")

    lists = sp_client.get_lists()

    target = (
        settings
        .SHAREPOINT_LIST_NAME
        .strip()
        .lower()
    )

    selected_list = None

    for item in lists:

        name = str(
            item.get("name") or ""
        ).strip().lower()

        display = str(
            item.get("displayName") or ""
        ).strip().lower()

        if name == target or display == target:
            selected_list = item
            break

    if selected_list:

        ok(
            "Lista SharePoint encontrada: "
            + str(
                selected_list.get(
                    "displayName"
                )
            )
        )

        list_id = selected_list["id"]

        endpoint = (
            f"/sites/{site_id}/lists/"
            f"{list_id}/items"
        )

        items = (
            sp_client
            .graph
            .get_all_pages(
                endpoint,
                params={
                    "$expand": "fields"
                }
            )
        )

        ok(
            f"Lectura SharePoint correcta "
            f"({len(items)} registros)"
        )

    else:

        fail(
            "No se encontro la lista configurada: "
            + settings.SHAREPOINT_LIST_NAME
        )

except Exception as exc:

    fail(
        "Conexion SharePoint/Microsoft fallo: "
        + str(exc)
    )


# =============================================================================
# 4. POSTGRESQL
# =============================================================================

print()
print("-" * 110)
print("4. POSTGRESQL")
print("-" * 110)

try:

    db = DbValidationService()

    clients = db.get_distinct_clients()

    suppliers = db.get_distinct_suppliers()

    ok("Conexion PostgreSQL correcta")

    ok(
        f"Clientes encontrados por ClientSupplier: "
        f"{len(clients)}"
    )

    ok(
        f"Proveedores encontrados por ClientSupplier: "
        f"{len(suppliers)}"
    )

    print()

    print("Clientes BD:")

    for client in clients:
        print(
            f"  - {client.get('name')} "
            f"| {client.get('document_number')}"
        )

except Exception as exc:

    fail(
        "Conexion/consulta PostgreSQL fallo: "
        + str(exc)
    )


# =============================================================================
# 5. CONFIGURACION DE CLIENTES / AMBITOS
# =============================================================================

print()
print("-" * 110)
print("5. CONFIGURACION DE AMBITOS")
print("-" * 110)

try:

    config = AmbitosConfigService()

    slv_clients = config.get_clients(
        "SLV"
    )

    required_slv_clients = {
        "DOCTOR SV",
        "CALLEJA S.A",
    }

    configured = set(
        slv_clients.keys()
    )

    missing = (
        required_slv_clients
        - configured
    )

    if missing:

        fail(
            "Faltan clientes SLV: "
            + ", ".join(
                sorted(missing)
            )
        )

    else:

        ok(
            "Clientes SLV configurados correctamente"
        )

    print()

    for name, client_config in slv_clients.items():

        ready = client_config.get(
            "ready_for_upload",
            False,
        )

        negocios = client_config.get(
            "negocios",
            [],
        )

        print(
            f"  {name}: "
            f"{len(negocios)} negocio(s) "
            f"| ready_for_upload={ready}"
        )

except Exception as exc:

    fail(
        "ambitos_config.json fallo: "
        + str(exc)
    )


# =============================================================================
# RESULTADO
# =============================================================================

print()
print("=" * 110)

if warnings:

    print(
        f"WARNINGS: {len(warnings)}"
    )

if errors:

    print(
        f"RESULTADO: ERROR "
        f"({len(errors)} problema(s))"
    )

    for error in errors:
        print(f" - {error}")

    raise SystemExit(1)

print("RESULTADO: OK")
print("Sistema, configuracion y conexiones funcionando.")
print("=" * 110)
