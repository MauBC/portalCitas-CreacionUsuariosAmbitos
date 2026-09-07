from _bootstrap import ROOT

import os

import pandas as pd

from app.phase3_pipeline import (
    run_phase3_final
)


print("=" * 110)
print("TEST 04 - GENERACION FINAL DE AMBITOS")
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


result = run_phase3_final()

print()
print("-" * 110)
print("1. RESULTADO FINAL")
print("-" * 110)

for label, key in [
    ("Registros fuente", "registros_fuente"),
    ("CREADO=1", "creado_1"),
    ("Automaticos", "automaticos"),
    ("Revision total", "revision_total"),
    ("Manuales asignados", "manuales_asignados"),
    ("Manuales incorporados", "manuales_incorporados"),
    ("Pendientes cliente", "pendientes_cliente"),
    ("Pendientes tecnicos", "pendientes_tecnicos"),
    ("Registros finales", "registros_finales"),
    ("Ambitos", "ambitos"),
]:
    print(
        f"{label:<22}: "
        f"{result.get(key)}"
    )

creado_1 = int(
    result.get(
        "creado_1",
        0,
    )
)

finales = int(
    result.get(
        "registros_finales",
        0,
    )
)

pendientes = int(
    result.get(
        "pendientes_total",
        0,
    )
)

if finales + pendientes == creado_1:
    ok(
        "Finales + pendientes = CREADO=1"
    )
else:
    fail(
        "Conteo final inconsistente"
    )

if int(
    result.get(
        "manuales_incorporados",
        0,
    )
) <= int(
    result.get(
        "manuales_asignados",
        0,
    )
):
    ok(
        "Asignaciones manuales controladas"
    )
else:
    fail(
        "Manuales incorporados supera asignados"
    )

if pendientes:
    warn(
        f"{pendientes} registro(s) "
        "quedaron fuera de la carga final"
    )
else:
    ok(
        "No existen pendientes"
    )


print()
print("-" * 110)
print("2. ARCHIVOS")
print("-" * 110)

template_path = result.get(
    "template_path"
)

diagnostics_path = result.get(
    "diagnostics_path"
)

for name, path in [
    ("PLANTILLA FINAL", template_path),
    ("DIAGNOSTICO FINAL", diagnostics_path),
]:
    if path and os.path.exists(path):
        ok(
            f"{name}: {path}"
        )
    else:
        fail(
            f"{name} no fue generado"
        )


print()
print("-" * 110)
print("3. PLANTILLA FINAL")
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

    expected = [
        "Entidades",
        "Ambitos",
        "RelacionNueva",
        "TipoNegocioNuevo",
        "TipoNegocioEliminar",
        "RelacionEliminar",
        "SedeNueva",
        "SedeEliminar",
    ]

    if excel.sheet_names == expected:
        ok(
            "Hojas y orden oficiales correctos"
        )
    else:
        fail(
            "Orden de hojas incorrecto"
        )

    ambitos = pd.read_excel(
        template_path,
        sheet_name="Ambitos",
        dtype=str,
    )

    relaciones = pd.read_excel(
        template_path,
        sheet_name="RelacionNueva",
        dtype=str,
    )

    entidades = pd.read_excel(
        template_path,
        sheet_name="Entidades",
        dtype=str,
    )

    if len(ambitos) == int(
        result.get(
            "ambitos",
            0,
        )
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

    if len(entidades) == int(
        result.get(
            "entidades",
            0,
        )
    ):
        ok(
            "Cantidad Entidades correcta"
        )
    else:
        fail(
            "Cantidad Entidades incorrecta"
        )


    # =============================================================================
    # TIPO DOCUMENTO POR PAIS
    # =============================================================================

    expected_entity_type = {
        "SLV": "NIT",
        "PER": "RUC",
    }.get(
        str(
            result.get("country")
            or ""
        ).strip().upper()
    )

    if not expected_entity_type:
        fail(
            "Pais sin Tipo de documento "
            "configurado para Entidades"
        )

    elif entidades.empty:
        fail(
            "No existen Entidades para "
            "validar Tipo de documento"
        )

    else:
        actual_types = {
            str(value or "")
            .strip()
            .upper()
            for value in (
                entidades["Tipo"]
                .fillna("")
            )
            if str(value or "").strip()
        }

        if actual_types == {
            expected_entity_type
        }:
            ok(
                "Entidades usa Tipo="
                f"{expected_entity_type}"
            )
        else:
            fail(
                "Tipo de documento incorrecto: "
                f"{sorted(actual_types)}"
            )

        if "Tipo Usuario" not in entidades.columns:
            fail(
                "Entidades no contiene "
                "la columna Tipo Usuario"
            )
        else:
            provider_rucs_tipo = set(
                relaciones["RUC"]
                .fillna("")
                .astype(str)
                .str.replace(
                    r"\D",
                    "",
                    regex=True,
                )
                .loc[
                    lambda series:
                        series.ne("")
                ]
                .tolist()
            )

            entity_rucs_tipo = (
                entidades["RUC"]
                .fillna("")
                .astype(str)
                .str.replace(
                    r"\D",
                    "",
                    regex=True,
                )
            )

            provider_mask_tipo = (
                entity_rucs_tipo
                .isin(
                    provider_rucs_tipo
                )
            )

            provider_rows_tipo = (
                entidades[
                    provider_mask_tipo
                ]
            )

            client_rows_tipo = (
                entidades[
                    ~provider_mask_tipo
                ]
            )

            provider_types = (
                provider_rows_tipo[
                    "Tipo Usuario"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            client_types = (
                client_rows_tipo[
                    "Tipo Usuario"
                ]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )

            if provider_rows_tipo.empty:
                fail(
                    "No existen entidades proveedoras "
                    "para validar Tipo Usuario"
                )
            elif provider_types.eq(
                "PROVEEDOR"
            ).all():
                ok(
                    "Entidades proveedoras usan "
                    "Tipo Usuario=PROVEEDOR"
                )
            else:
                invalid_values = sorted(
                    set(
                        provider_types[
                            provider_types.ne(
                                "PROVEEDOR"
                            )
                        ]
                    )
                )

                fail(
                    "Tipo Usuario incorrecto "
                    "en proveedores: "
                    + str(
                        invalid_values
                    )
                )

            if client_rows_tipo.empty:
                fail(
                    "No existen entidades cliente "
                    "para validar Tipo Usuario"
                )
            elif client_types.eq("CLIENTE").all():
                ok(
                    "Entidades cliente conservan "
                    "Tipo Usuario=CLIENTE"
                )
            else:
                fail(
                    "Las entidades cliente deben "
                    "tener Tipo Usuario=CLIENTE"
                )

    if not ambitos.empty:
        keys = (
            ambitos["Email"]
            .fillna("")
            .str.strip()
            .str.lower()
            + "|"
            + ambitos["Empresa"]
            .fillna("")
            .str.replace(
                r"\D",
                "",
                regex=True,
            )
        )

        if keys.duplicated().any():
            fail(
                "Ambitos duplica Email + Empresa"
            )
        else:
            ok(
                "Ambitos no duplica Email + Empresa"
            )

        invalid_sedes = []

        for value in (
            ambitos["Sedes Nuevas"]
            .fillna("")
        ):
            groups = {
                item.strip()
                for item in str(
                    value
                ).split(",")
                if item.strip()
            }

            if (
                not groups
                or not groups.issubset(
                    {"1", "2"}
                )
            ):
                invalid_sedes.append(
                    value
                )

        if invalid_sedes:
            fail(
                "Hay Sedes Nuevas invalidas"
            )
        else:
            ok(
                "Sedes Nuevas usa 1, 2 o 1,2"
            )


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
        print(
            f" - {error}"
        )

    raise SystemExit(1)

print("RESULTADO: OK")
print(
    "Plantilla final generada "
    "solo con relaciones seguras."
)
print("=" * 110)
