from _bootstrap import ROOT

import importlib
import inspect
import os

import pandas as pd


print("=" * 110)
print("TEST 02 - PIPELINE INTEGRADO DE USUARIOS")
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
# 1. LOCALIZAR RUNNER DE MAIN_PIPELINE
# =============================================================================

print()
print("-" * 110)
print("1. EJECUCION FASE 1")
print("-" * 110)

main_pipeline = importlib.import_module(
    "app.main_pipeline"
)

candidate_names = [
    "run_pipeline",
    "run_main_pipeline",
    "execute_pipeline",
    "execute",
    "main",
]

runner = None
runner_name = None

for name in candidate_names:

    function = getattr(
        main_pipeline,
        name,
        None,
    )

    if not callable(function):
        continue

    try:

        signature = inspect.signature(
            function
        )

        required = [
            parameter
            for parameter
            in signature.parameters.values()
            if (
                parameter.default
                is inspect.Parameter.empty
                and parameter.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            )
        ]

        if not required:
            runner = function
            runner_name = name
            break

    except Exception:
        continue


if runner is None:

    available = [
        name
        for name, value
        in vars(main_pipeline).items()
        if callable(value)
        and not name.startswith("_")
    ]

    raise RuntimeError(
        "No se encontro automaticamente "
        "la funcion principal de main_pipeline.py.\n"
        f"Funciones encontradas: {available}"
    )


ok(
    f"Runner detectado: {runner_name}()"
)


# =============================================================================
# 2. EJECUTAR
# =============================================================================

result = runner()

if not isinstance(result, dict):

    fail(
        "El pipeline no retorno un dict"
    )

    raise SystemExit(1)


if not result.get("ok"):

    fail(
        "El pipeline reporto ok=False"
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
        "Validos + errores NO coincide "
        "con el total"
    )


# =============================================================================
# 3. ASEGURAR QUE FASE 1 NO MODIFICA SHAREPOINT
# =============================================================================

print()
print("-" * 110)
print("2. SEGURIDAD SHAREPOINT")
print("-" * 110)

sharepoint_updates = int(
    result.get(
        "sharepoint_updated",
        0,
    )
)

if sharepoint_updates == 0:
    ok(
        "FASE 1 no modifico SharePoint"
    )
else:
    fail(
        f"FASE 1 modifico {sharepoint_updates} "
        "registro(s) SharePoint"
    )


# =============================================================================
# 4. ARCHIVOS GENERADOS
# =============================================================================

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


for name, path in paths.items():

    if not path:

        if (
            name in (
                "PLANTILLA",
                "MANIFIESTO",
            )
            and validos == 0
        ):
            warn(
                f"{name}: no generado "
                "porque no existen validos"
            )
            continue

        fail(
            f"{name}: ruta vacia"
        )
        continue

    if os.path.exists(path):

        ok(
            f"{name}: {path}"
        )

    else:

        fail(
            f"{name}: archivo no existe "
            f"({path})"
        )


# =============================================================================
# 5. VALIDAR REPORTE VALIDOS / ERRORES
# =============================================================================

print()
print("-" * 110)
print("4. CONTENIDO DE REPORTES")
print("-" * 110)

valid_path = paths["VALIDOS"]
error_path = paths["ERRORES"]


if valid_path and os.path.exists(
    valid_path
):

    xls = pd.ExcelFile(
        valid_path
    )

    required_sheets = {
        "VALIDOS_RESUMEN",
        "DATOS_TECNICOS",
    }

    missing = (
        required_sheets
        - set(xls.sheet_names)
    )

    if missing:
        fail(
            "Reporte VALIDOS sin hojas: "
            + ", ".join(
                sorted(missing)
            )
        )
    else:
        ok(
            "Reporte VALIDOS tiene "
            "las hojas obligatorias"
        )

    tech_valid = pd.read_excel(
        valid_path,
        sheet_name="DATOS_TECNICOS",
    )

    if len(tech_valid) == validos:
        ok(
            "Filas VALIDOS coinciden "
            "con contador"
        )
    else:
        fail(
            "Cantidad del reporte VALIDOS "
            "no coincide con el resultado"
        )


if error_path and os.path.exists(
    error_path
):

    xls = pd.ExcelFile(
        error_path
    )

    required_sheets = {
        "ERRORES_RESUMEN",
        "DATOS_TECNICOS",
    }

    missing = (
        required_sheets
        - set(xls.sheet_names)
    )

    if missing:
        fail(
            "Reporte ERRORES sin hojas: "
            + ", ".join(
                sorted(missing)
            )
        )
    else:
        ok(
            "Reporte ERRORES tiene "
            "las hojas obligatorias"
        )

    tech_errors = pd.read_excel(
        error_path,
        sheet_name="DATOS_TECNICOS",
    )

    if len(tech_errors) == errores:
        ok(
            "Filas ERRORES coinciden "
            "con contador"
        )
    else:
        fail(
            "Cantidad del reporte ERRORES "
            "no coincide"
        )

    if (
        "requiere_revision_cliente"
        in tech_errors.columns
    ):

        review_count = int(
            tech_errors[
                "requiere_revision_cliente"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        print(
            f"Casos revision manual : "
            f"{review_count}"
        )

        if review_count:
            ok(
                "Casos ambiguos de cliente "
                "quedan identificados"
            )


# =============================================================================
# 6. VALIDAR PLANTILLA PORTAL
# =============================================================================

print()
print("-" * 110)
print("5. PLANTILLA DE USUARIOS")
print("-" * 110)

template_path = paths[
    "PLANTILLA"
]

if (
    template_path
    and os.path.exists(template_path)
):

    xls = pd.ExcelFile(
        template_path
    )

    expected_sheets = [
        "USUARIOS",
        "SERVICIOS",
        "CONTROL",
    ]

    if xls.sheet_names == expected_sheets:

        ok(
            "Plantilla tiene exactamente "
            "USUARIOS + SERVICIOS + CONTROL"
        )

    else:

        fail(
            "Hojas incorrectas en plantilla: "
            + str(xls.sheet_names)
        )

    users = pd.read_excel(
        template_path,
        sheet_name="USUARIOS",
    )

    services = pd.read_excel(
        template_path,
        sheet_name="SERVICIOS",
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

    if list(users.columns) == expected_columns:

        ok(
            "Columnas USUARIOS correctas"
        )

    else:

        fail(
            "Columnas USUARIOS diferentes "
            "a la plantilla requerida"
        )

    if len(users) == validos:

        ok(
            "Cantidad de usuarios plantilla "
            "coincide con validos"
        )

    else:

        fail(
            "Cantidad de usuarios de la "
            "plantilla no coincide"
        )

    if len(services) == 2:

        ok(
            "Hoja SERVICIOS contiene "
            "las 2 filas requeridas"
        )

    else:

        fail(
            "Hoja SERVICIOS no contiene "
            "exactamente 2 filas"
        )


# =============================================================================
# 6. VALIDAR HOJA CONTROL
# =============================================================================

print()
print("-" * 110)
print("6. HOJA CONTROL")
print("-" * 110)

if (
    template_path
    and os.path.exists(template_path)
):

    control = pd.read_excel(
        template_path,
        sheet_name="CONTROL",
        dtype=str,
    )

    expected_control_columns = [
        "ITEM_ID",
        "EMAIL",
        "PROVEEDOR",
        "NIT_PROVEEDOR",
        "CLIENTE_ORIGINAL",
        "CLIENTE_NORMALIZADO",
        "ESTADO",
        "OBSERVACION",
    ]

    if list(control.columns) == expected_control_columns:
        ok(
            "Columnas CONTROL correctas"
        )
    else:
        fail(
            "Columnas CONTROL incorrectas: "
            + str(list(control.columns))
        )

    if len(control) == total:
        ok(
            f"CONTROL contiene los {total} registros"
        )
    else:
        fail(
            f"CONTROL contiene {len(control)} registros "
            f"y se esperaban {total}"
        )

    counts = (
        control["ESTADO"]
        .fillna("")
        .astype(str)
        .str.strip()
        .value_counts()
        .to_dict()
    )

    listos = int(
        counts.get(
            "LISTO_PARA_CARGA",
            0,
        )
    )

    error_datos = int(
        counts.get(
            "ERROR_DATOS",
            0,
        )
    )

    revision_cliente = int(
        counts.get(
            "REVISION_CLIENTE",
            0,
        )
    )

    print()
    print(
        f"LISTO_PARA_CARGA    : {listos}"
    )
    print(
        f"ERROR_DATOS         : {error_datos}"
    )
    print(
        f"REVISION_CLIENTE    : {revision_cliente}"
    )

    if listos == validos:
        ok(
            "LISTO_PARA_CARGA coincide con validos"
        )
    else:
        fail(
            f"LISTO_PARA_CARGA={listos}, "
            f"pero validos={validos}"
        )

    if revision_cliente == revision:
        ok(
            "REVISION_CLIENTE coincide "
            "con casos de revision"
        )
    else:
        fail(
            f"REVISION_CLIENTE={revision_cliente}, "
            f"pero revision={revision}"
        )

    expected_error_datos = (
        errores - revision
    )

    if error_datos == expected_error_datos:
        ok(
            "ERROR_DATOS coincide con errores "
            "no asociados a revision cliente"
        )
    else:
        fail(
            f"ERROR_DATOS={error_datos}, "
            f"pero se esperaban "
            f"{expected_error_datos}"
        )

    estados_validos = {
        "LISTO_PARA_CARGA",
        "ERROR_DATOS",
        "REVISION_CLIENTE",
    }

    estados_encontrados = set(
        control["ESTADO"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    desconocidos = (
        estados_encontrados
        - estados_validos
    )

    if not desconocidos:
        ok(
            "CONTROL no contiene estados desconocidos"
        )
    else:
        fail(
            "Estados desconocidos en CONTROL: "
            + ", ".join(
                sorted(desconocidos)
            )
        )


# =============================================================================
# 7. MANIFIESTO
# =============================================================================

print()
print("-" * 110)
print("7. MANIFIESTO FASE 2")
print("-" * 110)

manifest_path = paths[
    "MANIFIESTO"
]

if (
    manifest_path
    and os.path.exists(
        manifest_path
    )
):

    manifest = pd.read_excel(
        manifest_path
    )

    if len(manifest) == validos:

        ok(
            "Manifiesto contiene exactamente "
            "los usuarios enviados"
        )

    else:

        fail(
            "Filas del manifiesto no coinciden "
            "con validos"
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
    "Pipeline de usuarios funcionando correctamente."
)
print("=" * 110)
