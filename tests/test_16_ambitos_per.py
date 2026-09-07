from pathlib import Path
import sys
import tempfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


from app.phase3_pipeline import (
    _build_result,
    _load_source,
)
from app.services.ambitos_config_service import (
    AmbitosConfigService,
)


errors = []


def ok(message):
    print(
        f"[OK] {message}"
    )


def fail(message):
    print(
        f"[ERROR] {message}"
    )
    errors.append(
        message
    )


print("=" * 100)
print("TEST 16 - AMBITOS PER / DOLLARCITY")
print("=" * 100)


config = AmbitosConfigService()

for alias in [
    "DOLLARCITY",
    "DOLARCITY",
    "DOLLACITY",
    "DOLLAY CITY",
    "DOLLAR CITY",
]:
    resolved = config.resolve_alias(
        "PER",
        alias,
    )

    if resolved == "DOLLARCITY":
        ok(
            f"Alias {alias} -> DOLLARCITY"
        )
    else:
        fail(
            f"Alias {alias} no resolvio a DOLLARCITY"
        )

client_config = config.get_client_config(
    "PER",
    "DOLLARCITY",
)

if not client_config:
    fail(
        "No existe configuracion PER para DOLLARCITY"
    )
else:
    values = client_config["config"]

    expected = {
        "relation_group": 1,
        "tipo_negocio_group": 4,
        "sede_group": 1,
        "sede": "RSA",
        "sede_tipo_negocio":
            "Centros de Distribución",
    }

    for key, value in expected.items():
        if values.get(key) == value:
            ok(
                f"{key}={value}"
            )
        else:
            fail(
                f"{key}: esperado {value!r}, "
                f"obtenido {values.get(key)!r}"
            )


with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)

    report_path = (
        tmp
        / "reporte_excel_VALIDOS_test.xlsx"
    )

    valid_rows = pd.DataFrame([
        {
            "_item_id": "EXCEL-000001",
            "pais": "PER",
            "perfil": "PROVEEDOR",
            "email": "uno@example.com",
            "nombre_proveedor":
                "PROVEEDOR UNO SAC",
            "ruc_proveedor":
                "20111111111",
            "nit_proveedor": "",
            "nombre_cliente":
                "DOLLARCITY",
        },
        {
            "_item_id": "EXCEL-000002",
            "pais": "PER",
            "perfil": "PROVEEDOR",
            "email": "dos@example.com",
            "nombre_proveedor":
                "PROVEEDOR DOS SAC",
            "ruc_proveedor":
                "20222222222",
            "nit_proveedor": "",
            "nombre_cliente":
                "DOLARCITY",
        },
        {
            "_item_id": "EXCEL-000003",
            "pais": "PER",
            "perfil": "PROVEEDOR",
            "email": "tres@example.com",
            "nombre_proveedor":
                "PROVEEDOR TRES SAC",
            "ruc_proveedor":
                "20333333333",
            "nit_proveedor": "",
            "nombre_cliente":
                "DOLLARCITY",
        },
    ])

    with pd.ExcelWriter(
        report_path,
        engine="openpyxl",
    ) as writer:
        valid_rows.to_excel(
            writer,
            sheet_name="DATOS_TECNICOS",
            index=False,
        )

    provider_status = pd.DataFrame([
        {
            "_item_id": "EXCEL-000001",
            "creado": "1",
        },
        {
            "_item_id": "EXCEL-000002",
            "creado": "2",
        },
        {
            "_item_id": "EXCEL-000003",
            "creado": "1",
        },
    ])

    source = _load_source(
        valid_report_path=str(
            report_path
        ),
        country_code="PER",
        provider_status_df=provider_status,
    )

    if source["source_count"] == 3:
        ok(
            "Reporte PER conserva 3 relaciones validas de prueba"
        )
    else:
        fail(
            "Conteo fuente PER incorrecto"
        )

    if len(source["df"]) == 2:
        ok(
            "FASE 3 PER procesa solo creado=1"
        )
    else:
        fail(
            "Filtro creado=1 PER incorrecto"
        )

    if (
        source["status_source_count"] == 3
        and source["status_created_1"] == 2
        and source["status_not_created_1"] == 1
    ):
        ok(
            "Conteos de estado PER correctos"
        )
    else:
        fail(
            "Conteos de estado PER incorrectos"
        )

    clients = [
        {
            "client_id":
                "d113779a-e4a5-4a72-9e25-fc50b1d9d392",
            "name": "DOLLARCITY",
            "document_number":
                "20606109343",
        }
    ]

    result = _build_result(
        df=source["df"],
        clients=clients,
        country="PER",
    )

    if len(
        result.get(
            "matched_relations",
            [],
        )
    ) == 2:
        ok(
            "Las 2 relaciones creado=1 matchean DOLLARCITY"
        )
    else:
        fail(
            "No todas las relaciones PER matchearon DOLLARCITY"
        )

    if not result.get(
        "no_match",
        [],
    ):
        ok(
            "PER no genera revision manual para aliases conocidos"
        )
    else:
        fail(
            "PER genero revision manual inesperada"
        )

    entidades = result.get(
        "entidades",
        [],
    )

    client_entities = [
        row
        for row in entidades
        if str(
            row.get("RUC")
            or ""
        ).strip() == "20606109343"
    ]

    if (
        len(client_entities) == 1
        and str(
            client_entities[0].get(
                "Relacion Nueva"
            )
            or ""
        ) == "1"
        and str(
            client_entities[0].get(
                "Tipo"
            )
            or ""
        ).upper() == "RUC"
    ):
        ok(
            "Entidad DOLLARCITY usa RUC y Relacion Nueva=1"
        )
    else:
        fail(
            "Entidad DOLLARCITY incorrecta"
        )

    provider_entities = [
        row
        for row in entidades
        if str(
            row.get("RUC")
            or ""
        ).strip() in {
            "20111111111",
            "20333333333",
        }
    ]

    if (
        len(provider_entities) == 2
        and all(
            str(
                row.get(
                    "Tipo de negocio Nuevo"
                )
                or ""
            ) == "4"
            for row in provider_entities
        )
    ):
        ok(
            "Proveedores DOLLARCITY usan Retail grupo 4"
        )
    else:
        fail(
            "TipoNegocioNuevo de proveedores PER incorrecto"
        )

    ambitos = result.get(
        "ambitos",
        [],
    )

    if (
        len(ambitos) == 2
        and all(
            str(
                row.get(
                    "Sedes Nuevas"
                )
                or ""
            ) == "1"
            for row in ambitos
        )
    ):
        ok(
            "Ambitos DOLLARCITY usan Sede Nueva grupo 1"
        )
    else:
        fail(
            "Sede Nueva de Ambitos PER incorrecta"
        )

    sedes = result.get(
        "sede_nueva",
        [],
    )

    if sedes == [
        {
            "Grupo": 1,
            "Sede": "RSA",
            "Tipo de negocio":
                "Centros de Distribución",
        }
    ]:
        ok(
            "SedeNueva PER = 1 / RSA / Centros de Distribucion"
        )
    else:
        fail(
            f"SedeNueva PER incorrecta: {sedes}"
        )

    negocios = result.get(
        "tipo_negocio_nuevo",
        [],
    )

    retail = [
        row
        for row in negocios
        if int(
            row.get("Grupo")
            or 0
        ) == 4
    ]

    if (
        len(retail) == 1
        and str(
            retail[0].get("Rubro")
            or ""
        ).strip().upper() == "RETAIL"
    ):
        ok(
            "TipoNegocioNuevo grupo 4 = Retail"
        )
    else:
        fail(
            "Catalogo Retail grupo 4 incorrecto"
        )


print()
print("=" * 100)

if errors:
    print(
        f"RESULTADO: ERROR ({len(errors)} problema(s))"
    )

    for error in errors:
        print(
            " - " + error
        )

    raise SystemExit(1)

print("RESULTADO: OK")
print(
    "FASE 3 PER filtra creado=1 y aplica reglas DOLLARCITY."
)
print("=" * 100)
