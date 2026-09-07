from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


from app.provider_excel_pipeline import (
    _build_unique_users,
    _mark_email_identity_conflicts,
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
    "TEST 10 - PRIORIDAD DE CORREO REPETIDO"
)
print("=" * 100)


source = pd.DataFrame([
    {
        "nombre": "PRIMERO",
        "apellido": "VALIDO",
        "numero_documento": "11111111",
        "email": "mismo@correo.com",
        "estado": "OK",
        "advertencias": "",
        "nombre_cliente": "DOLLARCITY",
        "ruc_proveedor": "20111111111",
    },
    {
        "nombre": "SEGUNDO",
        "apellido": "DISTINTO",
        "numero_documento": "22222222",
        "email": "mismo@correo.com",
        "estado": "OK",
        "advertencias": "",
        "nombre_cliente": "DOLLARCITY",
        "ruc_proveedor": "20222222222",
    },
])

marked = _mark_email_identity_conflicts(
    source
)

if marked["estado"].eq("OK").all():
    ok(
        "Identidades distintas no bloquean "
        "filas validas"
    )
else:
    fail(
        "Se bloqueo un correo repetido valido"
    )

if (
    bool(
        marked.iloc[0][
            "usuario_principal"
        ]
    )
    and marked.iloc[0][
        "seleccion_usuario"
    ]
    == "PRIMER_REGISTRO_VALIDO"
):
    ok(
        "Primer registro valido queda "
        "como usuario principal"
    )
else:
    fail(
        "No se eligio el primer registro valido"
    )

if (
    marked.iloc[1][
        "seleccion_usuario"
    ]
    == "RELACION_ADICIONAL"
):
    ok(
        "Segundo registro valido se conserva "
        "como relacion adicional"
    )
else:
    fail(
        "Relacion adicional no fue conservada"
    )

unique = _build_unique_users(
    marked
)

if (
    len(unique) == 1
    and unique.iloc[0][
        "nombre"
    ] == "PRIMERO"
    and unique.iloc[0][
        "numero_documento"
    ] == "11111111"
):
    ok(
        "Plantilla usa datos completos "
        "del primer registro valido"
    )
else:
    fail(
        "Plantilla no priorizo el registro antiguo"
    )


source_invalid_first = pd.DataFrame([
    {
        "nombre": "",
        "apellido": "",
        "numero_documento": "",
        "email": "otro@correo.com",
        "estado": "ERROR",
        "advertencias": "",
        "nombre_cliente": "",
        "ruc_proveedor": "",
    },
    {
        "nombre": "VALIDO",
        "apellido": "SEGUNDO",
        "numero_documento": "33333333",
        "email": "otro@correo.com",
        "estado": "OK",
        "advertencias": "",
        "nombre_cliente": "DOLLARCITY",
        "ruc_proveedor": "20333333333",
    },
])

marked_invalid_first = (
    _mark_email_identity_conflicts(
        source_invalid_first
    )
)

unique_invalid_first = (
    _build_unique_users(
        marked_invalid_first
    )
)

if (
    len(unique_invalid_first) == 1
    and unique_invalid_first.iloc[0][
        "nombre"
    ] == "VALIDO"
):
    ok(
        "Si el registro antiguo tiene error, "
        "usa el primer repetido que sea valido"
    )
else:
    fail(
        "Una fila invalida bloqueo una cuenta valida"
    )

if (
    marked_invalid_first.iloc[0][
        "estado"
    ] == "ERROR"
    and marked_invalid_first.iloc[0][
        "seleccion_usuario"
    ]
    == "NO_USADO_CUENTA_POR_ERROR"
):
    ok(
        "Fila invalida conserva su error "
        "sin bloquear la cuenta"
    )
else:
    fail(
        "Fila invalida no conserva su estado"
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
    "Correos repetidos priorizan "
    "el primer registro valido."
)
print("=" * 100)
