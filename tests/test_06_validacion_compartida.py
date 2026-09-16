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
from app.services.db_validation_service import (
    DbValidationService,
)
from app.services.email_validation_service import (
    EmailValidationService,
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


class FakeEmailDb:
    def __init__(
        self,
        existing,
    ):
        self.existing = {
            str(value).strip().lower()
            for value in existing
        }

        self.calls = []

    def get_existing_emails(
        self,
        emails,
    ):
        normalized = [
            str(value).strip().lower()
            for value in emails
        ]

        self.calls.append(
            normalized
        )

        return (
            self.existing
            .intersection(
                normalized
            )
        )


class FakePostgresClient:
    def __init__(self):
        self.last_query = ""
        self.last_params = None

    def fetch_all(
        self,
        query,
        params=None,
    ):
        self.last_query = query
        self.last_params = params

        return [
            {
                "ClientId": 10,
                "Name": "DOCTOR SV",
                "DocumentNumber":
                    "1234567891234",
            }
        ]


print("=" * 100)
print("TEST 06 - VALIDACION COMPARTIDA")
print("=" * 100)


# ---------------------------------------------------------------------------
# 1. Servicio reutilizable de validacion de correo
# ---------------------------------------------------------------------------

fake_email_db = FakeEmailDb(
    {
        "existing@example.com",
    }
)

email_validator = (
    EmailValidationService(
        db_validator=fake_email_db
    )
)

frame = pd.DataFrame([
    {
        "email":
            " EXISTING@EXAMPLE.COM ",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "email":
            "new@example.com",
        "estado":
            "OK",
        "observaciones":
            "",
    },
    {
        "email":
            "existing@example.com",
        "estado":
            "ERROR",
        "observaciones":
            "ERROR PREVIO",
    },
])

validated, count = (
    email_validator
    .validate_existing_emails(
        frame
    )
)

if count == 1:
    ok(
        "Solo usuarios previamente validos "
        "se bloquean por BD"
    )
else:
    fail(
        f"Conteo BD incorrecto: {count}"
    )

if (
    validated.iloc[0]["estado"]
    == "ERROR"
):
    ok(
        "Correo existente cambia a ERROR"
    )
else:
    fail(
        "Correo existente no fue bloqueado"
    )

if (
    "CORREO YA EXISTE EN BD"
    in validated.iloc[0][
        "observaciones"
    ]
):
    ok(
        "Observacion de correo existente correcta"
    )
else:
    fail(
        "Falta observacion de correo existente"
    )

if (
    validated.iloc[1]["estado"]
    == "OK"
):
    ok(
        "Correo nuevo permanece OK"
    )
else:
    fail(
        "Correo nuevo fue bloqueado"
    )

if (
    validated.iloc[2][
        "observaciones"
    ]
    == "ERROR PREVIO"
):
    ok(
        "Errores previos no son sobrescritos"
    )
else:
    fail(
        "Se modifico un error previo"
    )


# ---------------------------------------------------------------------------
# 2. Consulta parametrizada a PostgreSQL
# ---------------------------------------------------------------------------

fake_postgres = (
    FakePostgresClient()
)

db_service = (
    DbValidationService(
        db=fake_postgres
    )
)

persons = (
    db_service
    .get_persons_by_names([
        " doctor sv ",
        "DOCTOR SV",
    ])
)

if (
    "ANY(%s)"
    in fake_postgres.last_query
    and fake_postgres.last_params
    == (
        ["DOCTOR SV"],
    )
):
    ok(
        "Busqueda de personas usa parametros SQL"
    )
else:
    fail(
        "Busqueda de personas no usa "
        "parametros correctamente"
    )

if (
    len(persons) == 1
    and persons[0]["name"]
    == "DOCTOR SV"
):
    ok(
        "Resultado parametrizado conserva contrato"
    )
else:
    fail(
        "Resultado get_persons_by_names incorrecto"
    )


# ---------------------------------------------------------------------------
# 3. Integracion importador Excel + validacion de correo
# ---------------------------------------------------------------------------

with tempfile.TemporaryDirectory() as temp_dir:
    temp = Path(
        temp_dir
    )

    excel_path = (
        temp
        / "proveedores_bd.xlsx"
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
                "Proveedor SAC",
            "correo":
                "existing@example.com",
            "tipoUsuario":
                "PROVEEDOR",
            "docIdentidad":
                "12345678",
            "creado":
                0,
        }
    ])

    with pd.ExcelWriter(
        excel_path,
        engine="openpyxl",
    ) as writer:
        data.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False,
        )

    pipeline_fake_db = (
        FakeEmailDb(
            {
                "existing@example.com",
            }
        )
    )

    pipeline_validator = (
        EmailValidationService(
            db_validator=
                pipeline_fake_db
        )
    )

    result = run_provider_excel(
        country_code="PER",
        source_type="local",
        file_path=str(
            excel_path
        ),
        validate_existing_emails=True,
        email_validation_service=
            pipeline_validator,
        output_root=temp,
    )

    if (
        result[
            "existing_emails_db"
        ] == 1
    ):
        ok(
            "Importador Excel integra validacion BD"
        )
    else:
        fail(
            "Importador Excel no conto "
            "correo existente"
        )

    if (
        result[
            "valid_relations"
        ] == 0
        and result[
            "errors"
        ] == 1
        and result[
            "unique_users"
        ] == 0
    ):
        ok(
            "Correo existente no llega "
            "a plantilla de usuarios"
        )
    else:
        fail(
            "Correo existente llego "
            "al flujo valido"
        )

    normalized = pd.read_excel(
        result[
            "normalized_path"
        ],
        dtype=str,
    )

    creado = str(
        normalized.iloc[0][
            "creado"
        ]
    ).strip()

    if creado in {
        "2",
        "2.0",
    }:
        ok(
            "Error por correo existente "
            "queda con creado=2"
        )
    else:
        fail(
            "Error por correo existente "
            "no actualizo creado=2"
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
    "Validacion compartida y estado "
    "creado funcionando."
)
print("=" * 100)
