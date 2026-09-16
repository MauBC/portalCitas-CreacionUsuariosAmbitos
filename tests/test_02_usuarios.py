from _bootstrap import ROOT

from pathlib import Path
import os
import warnings
import zipfile

import pandas as pd

from app.main_pipeline import run_pipeline


warnings.filterwarnings(
    "ignore",
    message=(
        "Data Validation extension "
        "is not supported"
    ),
)


print("=" * 110)
print(
    "TEST 02 - PIPELINE INTEGRADO DE USUARIOS"
)
print("=" * 110)


errors = []


def ok(message):
    print(f"[OK] {message}")


def fail(message):
    print(f"[ERROR] {message}")
    errors.append(message)


# ============================================================
# 1. EJECUCION
# ============================================================

print()
print("-" * 110)
print("1. EJECUCION FASE 1")
print("-" * 110)

result = run_pipeline()

if not result.get("ok"):
    fail(
        "Pipeline retorno ok=False"
    )

total = int(
    result.get("total", 0)
)

validos = int(
    result.get("validos", 0)
)

errores = int(
    result.get("errores", 0)
)

revision = int(
    result.get(
        "clientes_revision",
        0,
    )
)

print()
print(f"Total                : {total}")
print(f"Validos              : {validos}")
print(f"Errores              : {errores}")
print(f"Revision cliente     : {revision}")

if validos + errores == total:
    ok(
        "Validos + errores = total"
    )
else:
    fail(
        "Validos + errores != total"
    )

if revision == 0:
    ok(
        "FASE 1 no bloquea usuarios "
        "por cliente"
    )
else:
    fail(
        "FASE 1 todavia contiene "
        "revision de cliente"
    )


# ============================================================
# 2. SHAREPOINT
# ============================================================

print()
print("-" * 110)
print("2. SEGURIDAD SHAREPOINT")
print("-" * 110)

if int(
    result.get(
        "sharepoint_updated",
        0,
    )
) == 0:
    ok(
        "FASE 1 no modifico SharePoint"
    )
else:
    fail(
        "FASE 1 modifico SharePoint"
    )


# ============================================================
# 3. ARCHIVOS
# ============================================================

print()
print("-" * 110)
print("3. ARCHIVOS GENERADOS")
print("-" * 110)

paths = {
    "VALIDOS":
        result.get("path_validos"),
    "ERRORES":
        result.get("path_errores"),
    "PLANTILLA":
        result.get("path_template"),
    "MANIFIESTO":
        result.get("path_manifest"),
}

for name, file_path in paths.items():

    if (
        file_path
        and os.path.exists(file_path)
    ):
        ok(
            f"{name}: {file_path}"
        )
    else:
        fail(
            f"{name}: no encontrado"
        )


# ============================================================
# 4. REPORTES
# ============================================================

print()
print("-" * 110)
print("4. REPORTES")
print("-" * 110)

valid_path = paths["VALIDOS"]
error_path = paths["ERRORES"]

valid_data = pd.read_excel(
    valid_path,
    sheet_name="DATOS_TECNICOS",
    dtype=str,
)

error_data = pd.read_excel(
    error_path,
    sheet_name="DATOS_TECNICOS",
    dtype=str,
)

if len(valid_data) == validos:
    ok(
        "Reporte VALIDOS correcto"
    )
else:
    fail(
        "Cantidad VALIDOS incorrecta"
    )

if len(error_data) == errores:
    ok(
        "Reporte ERRORES correcto"
    )
else:
    fail(
        "Cantidad ERRORES incorrecta"
    )

if (
    "observaciones"
    in error_data.columns
):

    client_errors = (
        error_data["observaciones"]
        .fillna("")
        .astype(str)
        .str.contains(
            "CLIENTE REQUIERE REVISION",
            case=False,
            regex=False,
        )
        .sum()
    )

    if client_errors == 0:
        ok(
            "Cliente no genera errores "
            "en FASE 1"
        )
    else:
        fail(
            f"{client_errors} usuario(s) "
            "siguen bloqueados por cliente"
        )

if (
    "nombre_cliente"
    in valid_data.columns
):
    ok(
        "Cliente original se conserva "
        "para Ambitos"
    )
else:
    fail(
        "Se perdio nombre_cliente "
        "del reporte tecnico"
    )


# ============================================================
# 5. PLANTILLA OFICIAL
# ============================================================

print()
print("-" * 110)
print("5. PLANTILLA OFICIAL DEL PORTAL")
print("-" * 110)

template_path = paths[
    "PLANTILLA"
]

official_path = (
    Path(ROOT)
    / "app"
    / "templates"
    / "subida_usuarios.xlsx"
)

xls = pd.ExcelFile(
    template_path
)

expected_sheets = [
    "USUARIOS",
    "CLIENTES",
    "SERVICIOS",
    "MAESTROS",
]

if xls.sheet_names == expected_sheets:
    ok(
        "Hojas exactamente iguales "
        "a plantilla oficial"
    )
else:
    fail(
        "Hojas incorrectas: "
        + str(xls.sheet_names)
    )


users = pd.read_excel(
    template_path,
    sheet_name="USUARIOS",
    dtype=str,
    keep_default_na=False,
)

expected_columns = [
    "NOMBRE",
    "APELLIDO",
    "CORREO",
    "PAIS",
    "PERFIL DE USUARIO",
    "TIPO DE USUARIO",
    "TIPO DE DOCUMENTO IDENTIDAD",
    "DOCUMENTO",
    "SOCIEDAD",
    "CLIENTE",
    "SERVICIO",
]

if (
    list(users.columns)
    == expected_columns
):
    ok(
        "Columnas USUARIOS correctas"
    )
else:
    fail(
        "Columnas USUARIOS incorrectas"
    )


if len(users) == validos:
    ok(
        "Plantilla contiene exactamente "
        "los usuarios validos"
    )
else:
    fail(
        f"USUARIOS={len(users)} "
        f"VALIDOS={validos}"
    )


client_values = (
    users["CLIENTE"]
    .fillna("")
    .astype(str)
    .str.strip()
)

if (
    client_values == ""
).all():
    ok(
        "CLIENTE vacio para todos "
        "los usuarios"
    )
else:
    fail(
        "Existen usuarios con CLIENTE"
    )


service_values = (
    users["SERVICIO"]
    .fillna("")
    .astype(str)
    .str.strip()
)

if (
    service_values.ne("").all()
    and service_values.isin(
        {"1", "2"}
    ).all()
):
    ok(
        "SERVICIO asignado correctamente "
        "a todos los usuarios"
    )
else:
    fail(
        "Existen valores SERVICIO "
        "vacios o desconocidos"
    )


clients = pd.read_excel(
    template_path,
    sheet_name="CLIENTES",
    dtype=str,
)

if (
    list(clients.columns)
    == ["RUC", "NOMBRE", "GRUPO"]
    and clients.empty
):
    ok(
        "CLIENTES conserva solo encabezados"
    )
else:
    fail(
        "Hoja CLIENTES fue modificada"
    )


services = pd.read_excel(
    template_path,
    sheet_name="SERVICIOS",
    dtype=str,
    keep_default_na=False,
)

country_codes = (
    valid_data["pais"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.upper()
)

country_codes = {
    value
    for value in country_codes
    if value
}

expected_service = {
    "SLV": "PORTAL ACCESO CAM",
    "PER": "PORTAL ACCESO",
}

if len(country_codes) == 1:

    country_code = next(
        iter(country_codes)
    )

    service_name = expected_service.get(
        country_code
    )

else:

    service_name = None


expected_services = pd.DataFrame(
    [
        {
            "SERVICIO": service_name,
            "PARAMETRO": "PACCESO_PROVEEDOR",
            "GRUPO": "1",
        },
        {
            "SERVICIO": service_name,
            "PARAMETRO": "PACCESO_CLIENTE",
            "GRUPO": "2",
        },
    ]
)

services_compare = (
    services[
        [
            "SERVICIO",
            "PARAMETRO",
            "GRUPO",
        ]
    ]
    .fillna("")
    .astype(str)
    .reset_index(drop=True)
)

if services_compare.equals(
    expected_services
):
    ok(
        "Hoja SERVICIOS correcta "
        f"para {country_code}"
    )
else:
    fail(
        "Contenido de SERVICIOS incorrecto"
    )


# ============================================================
# 6. COMPARACION BINARIA
# ============================================================

print()
print("-" * 110)
print("6. INTEGRIDAD DE LA PLANTILLA")
print("-" * 110)

with zipfile.ZipFile(
    official_path,
    "r",
) as official:

    with zipfile.ZipFile(
        template_path,
        "r",
    ) as generated:

        official_files = set(
            official.namelist()
        )

        generated_files = set(
            generated.namelist()
        )

        if (
            official_files
            == generated_files
        ):
            ok(
                "Estructura interna XLSX "
                "conservada"
            )
        else:
            fail(
                "Cambios en estructura "
                "interna XLSX"
            )

        changed = []

        for member in official_files:

            if member in {
                "xl/worksheets/sheet1.xml",
                "xl/worksheets/sheet3.xml",
            }:
                continue

            if (
                official.read(member)
                != generated.read(member)
            ):
                changed.append(
                    member
                )

        if not changed:
            ok(
                "CLIENTES, MAESTROS "
                "y configuracion original intactos"
            )
        else:
            fail(
                "Se modificaron archivos "
                "internos: "
                + ", ".join(changed)
            )

        usuarios_xml = generated.read(
            "xl/worksheets/sheet1.xml"
        ).decode(
            "utf-8"
        )

        if (
            '<x14:dataValidations count="5"'
            in usuarios_xml
        ):
            ok(
                "Validaciones originales "
                "de USUARIOS preservadas"
            )
        else:
            fail(
                "Se perdieron validaciones "
                "de USUARIOS"
            )


# ============================================================
# 7. MANIFIESTO
# ============================================================

print()
print("-" * 110)
print("7. MANIFIESTO FASE 2")
print("-" * 110)

manifest = pd.read_excel(
    paths["MANIFIESTO"],
    dtype=str,
)

if len(manifest) == validos:
    ok(
        "Manifiesto contiene exactamente "
        "los usuarios enviados"
    )
else:
    fail(
        "Manifiesto no coincide "
        "con usuarios enviados"
    )


# ============================================================
# RESULTADO
# ============================================================

print()
print("=" * 110)

if errors:

    print(
        f"RESULTADO: ERROR "
        f"({len(errors)} problema(s))"
    )

    for error in errors:
        print(
            f" - {error}"
        )

    raise SystemExit(1)


print("RESULTADO: OK")
print(
    "Plantilla de usuarios compatible "
    "con formato oficial."
)
print("=" * 110)
