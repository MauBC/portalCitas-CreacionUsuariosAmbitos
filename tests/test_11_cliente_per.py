from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


from app.services.provider_client_validation_service import (
    ProviderClientValidationService,
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
    "TEST 11 - HOMOLOGACION CLIENTE PER"
)
print("=" * 100)


df = pd.DataFrame([
    {
        "nombre_cliente":
            "DOLLARCITY",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "nombre_cliente":
            "DOLARCITY",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "nombre_cliente":
            "DOLLACITY",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "nombre_cliente":
            "DOLLAY CITY",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "nombre_cliente":
            "GUSTOZZI",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "nombre_cliente":
            "",
        "estado":
            "ERROR",
        "observaciones":
            "NOMBRE CLIENTE OBLIGATORIO",
    },
])

result = (
    ProviderClientValidationService()
    .apply(
        df,
        country_code="PER",
    )
)


for index in [0, 1, 2, 3]:
    if (
        result.iloc[index][
            "nombre_cliente"
        ]
        == "DOLLARCITY"
        and result.iloc[index][
            "estado"
        ]
        == "OK"
    ):
        ok(
            f"Fila {index + 1} "
            "queda como DOLLARCITY"
        )
    else:
        fail(
            f"Fila {index + 1} "
            "no fue homologada"
        )


if (
    result.iloc[4]["estado"]
    == "ERROR"
    and "CLIENTE NO RECONOCIDO: GUSTOZZI"
    in result.iloc[4][
        "observaciones"
    ]
):
    ok(
        "GUSTOZZI queda como error"
    )
else:
    fail(
        "GUSTOZZI no fue bloqueado"
    )


if (
    result.iloc[5]["estado"]
    == "ERROR"
    and result.iloc[5][
        "observaciones"
    ]
    == "NOMBRE CLIENTE OBLIGATORIO"
):
    ok(
        "Cliente vacio conserva "
        "su error original"
    )
else:
    fail(
        "Cliente vacio fue alterado"
    )


slv = (
    ProviderClientValidationService()
    .apply(
        df.iloc[[4]].copy(),
        country_code="SLV",
    )
)

if (
    slv.iloc[0][
        "nombre_cliente"
    ]
    == "GUSTOZZI"
    and slv.iloc[0][
        "estado"
    ]
    == "OK"
):
    ok(
        "Regla PER no altera SLV"
    )
else:
    fail(
        "Regla PER afecto SLV"
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
    "Homologacion DOLLARCITY "
    "y rechazo de desconocidos correctos."
)
print("=" * 100)
