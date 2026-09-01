from _bootstrap import ROOT

import os

import pandas as pd

from app.phase3_pipeline import (
    run_phase3_preview
)

from app.services.client_assignment_service import (
    ClientAssignmentService
)

from app.config.portal_template_config import (
    COUNTRY_TEMPLATE_CONFIG
)

from app.services.db_validation_service import (
    DbValidationService
)


print("=" * 110)
print("TEST 03 - PIPELINE INTEGRADO DE AMBITOS")
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
# 1. RESOLUCION MULTICLIENTE
# =============================================================================

print()
print("-" * 110)
print("1. RESOLUCION DE CLIENTES")
print("-" * 110)

resolver = ClientAssignmentService()

country_config = (
    COUNTRY_TEMPLATE_CONFIG["SLV"]
)

cases = [
    ("DoctorSV", "DOCTOR SV"),
    ("DR SV", "DOCTOR SV"),
    ("Telemedicina.", "DOCTOR SV"),

    ("CALLEJA", "CALLEJA S.A"),
    ("CALLEJAS", "CALLEJA S.A"),
    ("Calleja S.A.", "CALLEJA S.A"),
]

for entered, expected in cases:

    result = (
        resolver.resolve_with_details(
            row={
                "pais": "SLV",
                "nombre_cliente": entered,
            },
            country_config=country_config,
        )
    )

    if (
        result["status"] == "OK"
        and result[
            "resolved_client"
        ] == expected
    ):

        ok(
            f"{entered!r} -> {expected}"
        )

    else:

        fail(
            f"{entered!r}: esperado "
            f"{expected}, obtenido "
            f"{result}"
        )


# Caso que DEBE requerir revision.

strange = resolver.resolve_with_details(
    row={
        "pais": "SLV",
        "nombre_cliente":
            "cliente completamente desconocido xyz",
    },
    country_config=country_config,
)

if strange["status"] == "REVISAR":

    ok(
        "Cliente desconocido queda "
        "para revision manual"
    )

else:

    fail(
        "Cliente desconocido fue asignado "
        "automaticamente"
    )


# =============================================================================
# 2. CLIENTES REALES BD
# =============================================================================

print()
print("-" * 110)
print("2. CLIENTES EN POSTGRESQL")
print("-" * 110)

try:

    db = DbValidationService()

    clients = db.get_persons_by_names(
        [
            "DOCTOR SV",
            "CALLEJA S.A",
        ]
    )

    names = {
        str(
            row.get("name") or ""
        ).strip().upper()
        for row in clients
    }

    if "CALLEJA S.A" in names:

        ok(
            "CALLEJA S.A existe en BD SLV"
        )

    else:

        fail(
            "CALLEJA S.A no fue encontrado "
            "como ClientId"
        )

    if "DOCTOR SV" not in names:

        warn(
            "DOCTOR SV aun no existe en BD. "
            "El test lo simulara solo en memoria."
        )

    else:

        ok(
            "DOCTOR SV ya existe realmente en BD"
        )

except Exception as exc:

    fail(
        "Consulta BD fallo: "
        + str(exc)
    )


# =============================================================================
# 3. EJECUTAR FASE 3
# =============================================================================

print()
print("-" * 110)
print("3. GENERACION DE AMBITOS")
print("-" * 110)

result = run_phase3_preview()


print()
print(
    f"Pais                 : "
    f"{result.get('country')}"
)

print(
    f"Usuarios             : "
    f"{result.get('usuarios')}"
)

print(
    f"Matched              : "
    f"{result.get('matched')}"
)

print(
    f"No match             : "
    f"{result.get('no_match')}"
)

print(
    f"Entidades            : "
    f"{result.get('entidades')}"
)

print(
    f"RelacionNueva        : "
    f"{result.get('relacion_nueva')}"
)

print(
    f"Ambitos              : "
    f"{result.get('ambitos')}"
)


usuarios = int(
    result.get(
        "usuarios",
        0,
    )
)

matched = int(
    result.get(
        "matched",
        0,
    )
)

no_match = int(
    result.get(
        "no_match",
        0,
    )
)


if matched + no_match == usuarios:

    ok(
        "Matched + NO_MATCH = usuarios"
    )

else:

    fail(
        "Resultado FASE 3 inconsistente"
    )


if no_match == 0:

    ok(
        "Todos los usuarios validos "
        "obtuvieron cliente"
    )

else:

    fail(
        f"Existen {no_match} usuario(s) "
        "sin cliente para ambitos"
    )


# =============================================================================
# 4. ARCHIVOS
# =============================================================================

print()
print("-" * 110)
print("4. ARCHIVOS DE AMBITOS")
print("-" * 110)

template_path = result.get(
    "template_path"
)

diagnostic_path = result.get(
    "diagnostics_path"
)


for name, path in [
    ("PLANTILLA", template_path),
    ("DIAGNOSTICO", diagnostic_path),
]:

    if path and os.path.exists(path):

        ok(
            f"{name}: {path}"
        )

    else:

        fail(
            f"{name} no fue generado"
        )


# =============================================================================
# 5. ESTRUCTURA DEL EXCEL
# =============================================================================

print()
print("-" * 110)
print("5. ESTRUCTURA PLANTILLA AMBITOS")
print("-" * 110)

if (
    template_path
    and os.path.exists(
        template_path
    )
):

    excel = pd.ExcelFile(
        template_path
    )

    required_sheets = {
        "Entidades",
        "Ambitos",
        "RelacionNueva",
        "RelacionEliminar",
        "TipoNegocioNuevo",
        "TipoNegocioEliminar",
        "SedeNueva",
        "SedeEliminar",
    }

    missing = (
        required_sheets
        - set(excel.sheet_names)
    )

    if missing:

        fail(
            "Faltan hojas: "
            + ", ".join(
                sorted(missing)
            )
        )

    else:

        ok(
            "Todas las hojas obligatorias existen"
        )

    entidades = pd.read_excel(
        template_path,
        sheet_name="Entidades",
    )

    ambitos = pd.read_excel(
        template_path,
        sheet_name="Ambitos",
    )

    relaciones = pd.read_excel(
        template_path,
        sheet_name="RelacionNueva",
    )

    if len(entidades) == int(
        result.get("entidades", 0)
    ):

        ok(
            "Cantidad Entidades correcta"
        )

    else:

        fail(
            "Cantidad Entidades incorrecta"
        )

    if len(ambitos) == int(
        result.get("ambitos", 0)
    ):

        ok(
            "Cantidad Ambitos correcta"
        )

    else:

        fail(
            "Cantidad Ambitos incorrecta"
        )

    if len(relaciones) == int(
        result.get(
            "relacion_nueva",
            0,
        )
    ):

        ok(
            "Cantidad RelacionNueva correcta"
        )

    else:

        fail(
            "Cantidad RelacionNueva incorrecta"
        )


# =============================================================================
# 6. VALIDAR CONFIGURACION REAL SLV
# =============================================================================

print()
print("-" * 110)
print("6. CONFIGURACION REAL DE NEGOCIOS / SEDES")
print("-" * 110)

tipo_negocio = pd.read_excel(
    template_path,
    sheet_name="TipoNegocioNuevo",
)

sedes = pd.read_excel(
    template_path,
    sheet_name="SedeNueva",
)

business_values = {
    str(value).strip().upper()
    for value in tipo_negocio["Tipo de negocio"].dropna()
}

sede_values = {
    str(value).strip().upper()
    for value in sedes["Sede"].dropna()
}

expected_business = {
    "SECOS",
    "FRÍOS",
}

expected_sedes = {
    "SANTA ELENA",
    "RANSA APOPA",
}

if business_values == expected_business:
    ok("Tipos de negocio correctos: SECOS / FRÍOS")
else:
    fail(
        "Tipos de negocio incorrectos: "
        + str(business_values)
    )

if sede_values == expected_sedes:
    ok("Sedes correctas: SANTA ELENA / RANSA APOPA")
else:
    fail(
        "Sedes incorrectas: "
        + str(sede_values)
    )

for forbidden in [
    "RSA",
    "RAA",
    "RANSA LURIN",
]:

    if forbidden in sede_values:
        fail(
            f"Sede antigua detectada: {forbidden}"
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
print(
    "Pipeline de ambitos funcionando correctamente."
)
print("=" * 110)

