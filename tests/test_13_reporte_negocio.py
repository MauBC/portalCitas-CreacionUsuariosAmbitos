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


from app.services.provider_excel_source_service import (
    ProviderExcelSourceService,
)

from app.services.excel_service import (
    ExcelService,
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
print(
    "TEST 13 - FILAS VACIAS "
    "Y REPORTE DE NEGOCIO"
)
print("=" * 100)


with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(temp_dir)

    source_path = (
        temp
        / "proveedores.xlsx"
    )

    source = pd.DataFrame([
        {
            "nombre": "",
            "apellido": "",
            "apellidomaterno": "",
            "nombreCliente": "",
            "rucProveedor": "",
            "nombreProveedor": "",
            "correo": "",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad": "",
            "creado": "0",
        },
        {
            "nombre": "ANA",
            "apellido": "PEREZ",
            "apellidomaterno": "",
            "nombreCliente":
                "DOLLARCITY",
            "rucProveedor":
                "20123456789",
            "nombreProveedor":
                "PROVEEDOR SAC",
            "correo":
                "ana@test.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "12345678",
            "creado": "0",
        },
    ])

    with pd.ExcelWriter(
        source_path,
        engine="openpyxl",
    ) as writer:
        source.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False,
        )

    loaded = (
        ProviderExcelSourceService()
        .load_local(
            str(source_path)
        )
    )

    if (
        len(loaded) == 1
        and loaded.iloc[0][
            "nombre"
        ] == "ANA"
    ):
        ok(
            "Fila con solo creado/tipoUsuario "
            "se elimina como vacia"
        )
    else:
        fail(
            "Fila de control vacia "
            "sigue entrando al pipeline"
        )

    output_dir = (
        temp
        / "salida"
    )

    excel = ExcelService(
        output_dir=
            str(output_dir)
    )

    error_df = pd.DataFrame([
        {
            "_item_id":
                "EXCEL-000003",
            "pais":
                "PER",
            "nombre":
                "",
            "apellido":
                "HURTADO",
            "apellido_pat":
                "HURTADO",
            "apellido_mat":
                "",
            "email":
                "ghurtado@delycorp.pe",
            "nombre_proveedor":
                "DELYCORP SAC",
            "nombre_cliente":
                "DOLLARCITY",
            "numero_documento":
                "45065527",
            "ruc_proveedor":
                "20601019443",
            "perfil":
                "PROVEEDOR",
            "estado":
                "ERROR",
            "observaciones":
                "NOMBRE OBLIGATORIO",
            "advertencias":
                "",
            "seleccion_usuario":
                "",
        },
        {
            "_item_id":
                "EXCEL-000010",
            "pais":
                "PER",
            "nombre":
                "JUAN",
            "apellido":
                "PEREZ",
            "apellido_pat":
                "PEREZ",
            "apellido_mat":
                "",
            "email":
                "duplicado@test.com",
            "nombre_proveedor":
                "PROVEEDOR SAC",
            "nombre_cliente":
                "DOLLARCITY",
            "numero_documento":
                "",
            "ruc_proveedor":
                "20123456789",
            "perfil":
                "PROVEEDOR",
            "estado":
                "ERROR",
            "observaciones":
                "DNI OBLIGATORIO",
            "advertencias":
                "",
            "seleccion_usuario":
                "NO_USADO_CUENTA_POR_ERROR",
        },
        {
            "_item_id":
                "EXCEL-000011",
            "pais":
                "PER",
            "nombre":
                "JUAN",
            "apellido":
                "PEREZ",
            "apellido_pat":
                "PEREZ",
            "apellido_mat":
                "",
            "email":
                "duplicado@test.com",
            "nombre_proveedor":
                "PROVEEDOR SAC",
            "nombre_cliente":
                "DOLLARCITY",
            "numero_documento":
                "12345678",
            "ruc_proveedor":
                "20123456789",
            "perfil":
                "PROVEEDOR",
            "estado":
                "OK",
            "observaciones":
                "",
            "advertencias":
                "",
            "seleccion_usuario":
                "PRIMER_REGISTRO_VALIDO",
        },
    ])

    paths = (
        excel.export_validos_errores(
            error_df,
            base_name="prueba",
        )
    )

    error_path = Path(
        paths["errores"]
    )

    with pd.ExcelFile(
        error_path
    ) as book:
        expected = {
            "PENDIENTES_CUENTA",
            "ERRORES_RESUMEN",
            "DATOS_TECNICOS",
        }

        if expected.issubset(
            set(
                book.sheet_names
            )
        ):
            ok(
                "Reporte contiene hoja de negocio "
                "y hojas tecnicas"
            )
        else:
            fail(
                "Faltan hojas "
                "del nuevo reporte"
            )

    pending = pd.read_excel(
        error_path,
        sheet_name=
            "PENDIENTES_CUENTA",
        dtype=str,
        keep_default_na=False,
    )

    if (
        len(pending) == 1
        and pending.iloc[0][
            "CORREO"
        ] == "ghurtado@delycorp.pe"
    ):
        ok(
            "Hoja negocio excluye "
            "error cubierto por otra fila valida"
        )
    else:
        fail(
            "Hoja negocio contiene "
            "cuentas cubiertas por otra fila"
        )

    if (
        "Completar los siguientes datos"
        in pending.iloc[0][
            "ACCION REQUERIDA"
        ]
    ):
        ok(
            "Reporte explica "
            "la accion requerida"
        )
    else:
        fail(
            "Reporte no explica "
            "que debe corregirse"
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
    "Filas vacias reales y "
    "reporte de negocio funcionando."
)
print("=" * 100)
