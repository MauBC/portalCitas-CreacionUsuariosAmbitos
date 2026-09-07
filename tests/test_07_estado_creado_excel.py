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


from app.provider_excel_pipeline import (
    run_provider_excel,
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
print("TEST 07 - ESTADO CREADO EXCEL")
print("=" * 100)


with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(
        temp_dir
    )

    path = (
        temp
        / "estado_creado.xlsx"
    )

    data = pd.DataFrame([
        {
            "nombre":
                "Ana",
            "apellido":
                "Ramos",
            "nombreCliente":
                "DOLLARCITY",
            "rucProveedor":
                "20610543317",
            "nombreProveedor":
                "PROVEEDOR A",
            "correo":
                "pendiente@example.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "12345678",
            "creado":
                0,
        },
        {
            "nombre":
                "Luis",
            "apellido":
                "Perez",
            "nombreCliente":
                "DOLLARCITY",
            "rucProveedor":
                "20610543318",
            "nombreProveedor":
                "PROVEEDOR B",
            "correo":
                "creado@example.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "87654321",
            "creado":
                1,
        },
        {
            "nombre":
                "Maria",
            "apellido":
                "Lopez",
            "nombreCliente":
                "DOLLARCITY",
            "rucProveedor":
                "20610543319",
            "nombreProveedor":
                "PROVEEDOR C",
            "correo":
                "error@example.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "11112222",
            "creado":
                2,
        },
    ])

    with pd.ExcelWriter(
        path,
        engine="openpyxl",
    ) as writer:
        data.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False,
        )

    result = run_provider_excel(
        country_code="PER",
        source_type="local",
        file_path=str(
            path
        ),
        validate_existing_emails=False,
        output_root=temp,
    )

    if result["total"] == 3:
        ok(
            "Se conservaron las tres filas fuente"
        )
    else:
        fail(
            "Conteo total incorrecto"
        )

    if (
        result[
            "valid_relations"
        ] == 1
    ):
        ok(
            "Solo creado=0 entra al proceso"
        )
    else:
        fail(
            "Se procesaron filas no pendientes"
        )

    if (
        result[
            "already_created"
        ] == 1
    ):
        ok(
            "creado=1 se omite como ya creado"
        )
    else:
        fail(
            "creado=1 no fue omitido correctamente"
        )

    if (
        result[
            "previous_errors"
        ] == 1
    ):
        ok(
            "creado=2 se omite como error previo"
        )
    else:
        fail(
            "creado=2 no fue omitido correctamente"
        )

    if (
        result[
            "unique_users"
        ] == 1
    ):
        ok(
            "La plantilla contiene solo pendientes"
        )
    else:
        fail(
            "La plantilla contiene filas omitidas"
        )

    normalized = pd.read_excel(
        result[
            "normalized_path"
        ],
        dtype=str,
    )

    required_normalized_columns = {
        "email",
        "creado",
        "estado",
        "estado_proceso",
    }

    missing = (
        required_normalized_columns
        - set(
            normalized.columns
        )
    )

    if not missing:
        ok(
            "Esquema normalizado contiene "
            "email, creado, estado y estado_proceso"
        )
    else:
        fail(
            "Faltan columnas normalizadas: "
            + ", ".join(
                sorted(
                    missing
                )
            )
        )

    statuses = {
        str(
            row["email"]
        ).strip().lower():
            str(
                row["creado"]
            ).strip()
        for _, row in (
            normalized.iterrows()
        )
    }

    process_statuses = {
        str(
            row["email"]
        ).strip().lower():
            str(
                row["estado_proceso"]
            ).strip()
        for _, row in (
            normalized.iterrows()
        )
    }

    if statuses.get(
        "pendiente@example.com"
    ) in {
        "0",
        "0.0",
    }:
        ok(
            "Pendiente conserva creado=0"
        )
    else:
        fail(
            "Pendiente cambio de estado sin crearse"
        )

    if statuses.get(
        "creado@example.com"
    ) in {
        "1",
        "1.0",
    }:
        ok(
            "Usuario creado conserva creado=1"
        )
    else:
        fail(
            "creado=1 fue alterado"
        )

    if statuses.get(
        "error@example.com"
    ) in {
        "2",
        "2.0",
    }:
        ok(
            "Error previo conserva creado=2"
        )
    else:
        fail(
            "creado=2 fue alterado"
        )

    if (
        process_statuses.get(
            "pendiente@example.com"
        )
        == "PENDIENTE"
    ):
        ok(
            "Pendiente conserva estado_proceso=PENDIENTE"
        )
    else:
        fail(
            "estado_proceso incorrecto para creado=0"
        )

    if (
        process_statuses.get(
            "creado@example.com"
        )
        == "YA_CREADO"
    ):
        ok(
            "creado=1 queda como YA_CREADO"
        )
    else:
        fail(
            "estado_proceso incorrecto para creado=1"
        )

    if (
        process_statuses.get(
            "error@example.com"
        )
        == "ERROR_PREVIO"
    ):
        ok(
            "creado=2 queda como ERROR_PREVIO"
        )
    else:
        fail(
            "estado_proceso incorrecto para creado=2"
        )


print()
print("=" * 100)

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
    "Estados 0/1/2 y esquema normalizado "
    "funcionando correctamente."
)
print("=" * 100)
