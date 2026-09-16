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
print("TEST 05 - IMPORTADOR EXCEL PROVEEDORES")
print("=" * 100)


with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(temp_dir)

    per_path = (
        temp
        / "proveedores_per.xlsx"
    )

    per_data = pd.DataFrame([
        {
            "nombre": "Francísco",
            "apellido": "Lúliquiz",
            "nombreCliente": "Dollar City",
            "rucProveedor": "20-610543317",
            "nombreProveedor":
                "Business MFP Solution Perú SAC",
            "correo":
                "SOLUCIONES.BSC@GMAIL.COM",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "7486167",
            "creado":
                0,
        },
        {
            "nombre": "Francísco",
            "apellido": "Lúliquiz",
            "nombreCliente": "DOLLACITY",
            "rucProveedor": "20-610543317",
            "nombreProveedor":
                "Business MFP Solution Perú SAC",
            "correo":
                "SOLUCIONES.BSC@GMAIL.COM",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "7486167",
            "creado":
                0,
        },
        {
            "nombre": "Carlos",
            "apellido": "Puican",
            "nombreCliente": "Dollar City",
            "rucProveedor": "20522228ABC",
            "nombreProveedor":
                "I.SEG PERU SAC",
            "correo":
                "carlos@example.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "74217877",
            "creado":
                0,
        },
    ])

    with pd.ExcelWriter(
        per_path,
        engine="openpyxl",
    ) as writer:
        per_data.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False,
        )

    per_result = run_provider_excel(
        country_code="PER",
        source_type="local",
        file_path=str(
            per_path
        ),
        validate_existing_emails=False,
        output_root=temp,
    )

    if (
        per_result[
            "valid_relations"
        ] == 2
    ):
        ok(
            "PER conserva relaciones pendientes validas"
        )
    else:
        fail(
            "PER relaciones validas incorrectas"
        )

    if (
        per_result[
            "unique_users"
        ] == 1
    ):
        ok(
            "PER deduplica usuarios por correo"
        )
    else:
        fail(
            "PER no deduplico usuarios"
        )

    if (
        per_result[
            "errors"
        ] == 1
    ):
        ok(
            "PER convierte error de validacion a creado=2"
        )
    else:
        fail(
            "PER error de validacion incorrecto"
        )

    ok(
        "PER acepta Excel sin apellidomaterno"
    )

    slv_path = (
        temp
        / "proveedores_slv.xlsx"
    )

    slv_data = pd.DataFrame([
        {
            "nombre": "María",
            "apellido": "Núńez",
            "nombreCliente": "Doctor SV",
            "rucProveedor":
                "0614-170299-102-6",
            "nombreProveedor":
                "Compańía Farmacéutica SA de CV",
            "correo":
                "MARIA@EXAMPLE.COM",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "1234567",
            "creado":
                0,
        },
        {
            "nombre": "Luis",
            "apellido": "Lopez",
            "nombreCliente": "Doctor SV",
            "rucProveedor":
                "0614170299102",
            "nombreProveedor":
                "Proveedor XYZ",
            "correo":
                "luis@example.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "123456789",
            "creado":
                0,
        },
    ])

    with pd.ExcelWriter(
        slv_path,
        engine="openpyxl",
    ) as writer:
        slv_data.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False,
        )

    slv_result = run_provider_excel(
        country_code="SLV",
        source_type="local",
        file_path=str(
            slv_path
        ),
        validate_existing_emails=False,
        output_root=temp,
    )

    if (
        slv_result[
            "valid_relations"
        ] == 1
    ):
        ok(
            "SLV acepta NIT valido pendiente"
        )
    else:
        fail(
            "SLV validacion NIT incorrecta"
        )

    if (
        slv_result[
            "errors"
        ] == 1
    ):
        ok(
            "SLV error de validacion queda en creado=2"
        )
    else:
        fail(
            "SLV error de validacion incorrecto"
        )

    ok(
        "SLV acepta Excel sin apellidomaterno"
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
    "Importador PER/SLV procesa "
    "solo registros pendientes."
)
print("=" * 100)
