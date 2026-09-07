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
from app.services.provider_excel_source_service import (
    ProviderExcelSourceService,
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


def build_excel(
    path: Path,
    rows: list[dict],
):
    columns = [
        "nombre",
        "apellido",
        "apellidomaterno",
        "nombreCliente",
        "rucProveedor",
        "nombreProveedor",
        "correo",
        "tipoUsuario",
        "docIdentidad",
        "creado",
    ]

    frame = pd.DataFrame(
        rows,
        columns=columns,
    )

    with pd.ExcelWriter(
        path,
        engine="openpyxl",
    ) as writer:
        frame.to_excel(
            writer,
            sheet_name=
                "Proveedores",
            index=False,
        )


print("=" * 100)
print(
    "TEST 08 - REPORTE DE ERRORES "
    "Y FILAS VACIAS"
)
print("=" * 100)


with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(
        temp_dir
    )

    per_path = (
        temp
        / "reporte_per.xlsx"
    )

    build_excel(
        per_path,
        [
            {
                "nombre":
                    "ANA",
                "apellido":
                    "RAMOS",
                "apellidomaterno":
                    "",
                "nombreCliente":
                    "DOLLARCITY",
                "rucProveedor":
                    "20610543317",
                "nombreProveedor":
                    "PROVEEDOR A",
                "correo":
                    "ana@example.com",
                "tipoUsuario":
                    "PROVEEDOR",
                "docIdentidad":
                    "12345678",
                "creado":
                    0,
            },
            {
                "nombre":
                    "",
                "apellido":
                    "PEREZ",
                "apellidomaterno":
                    "",
                "nombreCliente":
                    "DOLLARCITY",
                "rucProveedor":
                    "",
                "nombreProveedor":
                    "PROVEEDOR B",
                "correo":
                    "falta@example.com",
                "tipoUsuario":
                    "PROVEEDOR",
                "docIdentidad":
                    "",
                "creado":
                    0,
            },
            {
                "nombre":
                    "",
                "apellido":
                    "",
                "apellidomaterno":
                    "",
                "nombreCliente":
                    "",
                "rucProveedor":
                    "",
                "nombreProveedor":
                    "",
                "correo":
                    "",
                "tipoUsuario":
                    "",
                "docIdentidad":
                    "",
                "creado":
                    "",
            },
            {
                "nombre":
                    "LUIS",
                "apellido":
                    "LOPEZ",
                "apellidomaterno":
                    "",
                "nombreCliente":
                    "DOLLARCITY",
                "rucProveedor":
                    "ABC",
                "nombreProveedor":
                    "PROVEEDOR C",
                "correo":
                    "luis@example.com",
                "tipoUsuario":
                    "PROVEEDOR",
                "docIdentidad":
                    "123",
                "creado":
                    0,
            },
        ],
    )

    raw_per = (
        ProviderExcelSourceService()
        .load_local(
            str(per_path)
        )
    )

    if len(raw_per) == 3:
        ok(
            "PER elimina fila completamente vacia "
            "antes del pipeline"
        )
    else:
        fail(
            "PER no elimino correctamente "
            "la fila vacia"
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

    per_errors = pd.read_excel(
        per_result["error_path"],
        sheet_name="ERRORES_RESUMEN",
        dtype=str,
        keep_default_na=False,
    )

    expected_per_headers = {
        "DNI ORIGINAL",
        "DNI LIMPIO",
        "RUC ORIGINAL",
        "RUC LIMPIO",
        "FALTA LLENAR",
        "ERROR",
    }

    if expected_per_headers.issubset(
        set(
            per_errors.columns
        )
    ):
        ok(
            "PER usa encabezados DNI/RUC "
            "y FALTA LLENAR"
        )
    else:
        fail(
            "PER no genero encabezados esperados"
        )

    missing_row = per_errors[
        per_errors[
            "CORREO"
        ].eq(
            "falta@example.com"
        )
    ]

    if len(missing_row) == 1:
        missing_text = (
            missing_row.iloc[0][
                "FALTA LLENAR"
            ]
        )

        if all(
            field in missing_text
            for field in [
                "NOMBRE",
                "DNI",
                "RUC",
            ]
        ):
            ok(
                "PER informa NOMBRE, DNI y RUC "
                "como faltantes"
            )
        else:
            fail(
                "PER FALTA LLENAR incompleto: "
                + missing_text
            )
    else:
        fail(
            "No se encontro fila PER "
            "de campos faltantes"
        )

    invalid_row = per_errors[
        per_errors[
            "CORREO"
        ].eq(
            "luis@example.com"
        )
    ]

    if len(invalid_row) == 1:
        missing_text = (
            invalid_row.iloc[0][
                "FALTA LLENAR"
            ]
        )

        error_text = (
            invalid_row.iloc[0][
                "ERROR"
            ]
        )

        if (
            "RUC" not in missing_text
            and "RUC PROVEEDOR INVALIDO"
            in error_text
        ):
            ok(
                "PER distingue RUC faltante "
                "de RUC invalido"
            )
        else:
            fail(
                "PER confunde valor invalido "
                "con campo faltante"
            )

    slv_path = (
        temp
        / "reporte_slv.xlsx"
    )

    build_excel(
        slv_path,
        [
            {
                "nombre":
                    "",
                "apellido":
                    "RAMOS",
                "apellidomaterno":
                    "",
                "nombreCliente":
                    "DOCTOR SV",
                "rucProveedor":
                    "",
                "nombreProveedor":
                    "PROVEEDOR SLV",
                "correo":
                    "slv@example.com",
                "tipoUsuario":
                    "PROVEEDOR",
                "docIdentidad":
                    "",
                "creado":
                    0,
            },
        ],
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

    slv_errors = pd.read_excel(
        slv_result["error_path"],
        sheet_name="ERRORES_RESUMEN",
        dtype=str,
        keep_default_na=False,
    )

    expected_slv_headers = {
        "DUI ORIGINAL",
        "DUI LIMPIO",
        "NIT ORIGINAL",
        "NIT LIMPIO",
        "FALTA LLENAR",
        "ERROR",
    }

    if expected_slv_headers.issubset(
        set(
            slv_errors.columns
        )
    ):
        ok(
            "SLV usa encabezados DUI/NIT "
            "y FALTA LLENAR"
        )
    else:
        fail(
            "SLV no genero encabezados esperados"
        )

    slv_missing = (
        slv_errors.iloc[0][
            "FALTA LLENAR"
        ]
        if not slv_errors.empty
        else ""
    )

    if all(
        field in slv_missing
        for field in [
            "NOMBRE",
            "DUI",
            "NIT",
        ]
    ):
        ok(
            "SLV informa NOMBRE, DUI y NIT "
            "como faltantes"
        )
    else:
        fail(
            "SLV FALTA LLENAR incorrecto: "
            + slv_missing
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
    "Reportes por pais y limpieza "
    "de filas vacias funcionando."
)
print("=" * 100)

