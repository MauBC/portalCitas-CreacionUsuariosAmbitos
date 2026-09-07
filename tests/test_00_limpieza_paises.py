from pathlib import Path
import sys

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


from app.config.portal_access_config import (
    PORTAL_ACCESS_SERVICE,
)
from app.services.country_cleaning_service import (
    CountryCleaningService,
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
print("TEST 00 - LIMPIEZA UNIFICADA PER / SLV")
print("=" * 100)

cleaner = CountryCleaningService()


per = pd.DataFrame([
    {
        "_item_id": "PER-1",
        "pais": "PER",
        "nombre": " José ",
        "apellido_pat": "Pérez-López",
        "apellido_mat": "García",
        "email": " TEST.PER@GMAIL.COM ",
        "numero_documento": "7486167",
        "perfil": "PROVEEDOR",
        "nombre_cliente": "Dóllar City",
        "nombre_proveedor":
            "Comercialización & Servicios S.A.C.",
        "ruc_proveedor": "20-610543317",
        "num_telefono": "",
    },
    {
        "_item_id": "PER-2",
        "pais": "PER",
        "nombre": "ANA",
        "apellido_pat": "RAMOS",
        "apellido_mat": "",
        "email": "ana@test.com",
        "numero_documento": "12345678",
        "perfil": "PROVEEDOR",
        "nombre_cliente": "CLIENTE XYZ",
        "nombre_proveedor": "PROVEEDOR XYZ",
        "ruc_proveedor": "20610543317A",
        "num_telefono": "",
    },
])

per_result = cleaner.clean(
    per
)

per_ok = per_result.iloc[0]
per_bad = per_result.iloc[1]

if per_ok["nombre"] == "JOSE":
    ok("PER elimina tildes en nombre")
else:
    fail("PER no limpio nombre correctamente")

if per_ok["apellido_pat"] == "PEREZ LOPEZ":
    ok("PER limpia apellido paterno")
else:
    fail("PER no limpio apellido paterno")

if per_ok["nombre_cliente"] == "DOLLAR CITY":
    ok("PER limpia nombre cliente")
else:
    fail("PER no limpio nombre cliente")

if (
    per_ok["ruc_proveedor"] == "20610543317"
    and per_ok["estado"] == "OK"
):
    ok("PER acepta RUC limpio de 11 digitos")
else:
    fail("PER rechazo RUC valido")

if (
    "DNI CON FORMATO INUSUAL"
    in str(per_ok["advertencias"])
    and per_ok["estado"] == "OK"
):
    ok("PER DNI invalido genera warning")
else:
    fail("PER DNI invalido esta bloqueando")

if per_bad["estado"] == "ERROR":
    ok("PER rechaza RUC con caracteres invalidos")
else:
    fail("PER acepto RUC con caracteres invalidos")


slv = pd.DataFrame([
    {
        "_item_id": "SLV-1",
        "pais": "SLV",
        "nombre": " María ",
        "apellido": "Núñez-Ramírez",
        "email": " TEST.SLV@MAIL.COM ",
        "telefono": "",
        "numero_documento": "1234567",
        "perfil": "PROVEEDOR",
        "nombre_cliente": "Doctor SV",
        "nombre_proveedor":
            "Compañía Farmacéutica, S.A. de C.V.",
        "nit_proveedor": "0614-170299-102-6",
    },
    {
        "_item_id": "SLV-2",
        "pais": "SLV",
        "nombre": "LUIS",
        "apellido": "LOPEZ",
        "email": "luis@test.com",
        "telefono": "",
        "numero_documento": "123456789",
        "perfil": "PROVEEDOR",
        "nombre_cliente": "DOCTOR SV",
        "nombre_proveedor": "PROVEEDOR XYZ",
        "nit_proveedor": "06141702991026A",
    },
])

slv_result = cleaner.clean(
    slv
)

slv_ok = slv_result.iloc[0]
slv_bad = slv_result.iloc[1]

if slv_ok["nombre"] == "MARIA":
    ok("SLV elimina tildes en nombre")
else:
    fail("SLV no limpio nombre correctamente")

if slv_ok["apellido"] == "NUNEZ RAMIREZ":
    ok("SLV limpia apellido")
else:
    fail("SLV no limpio apellido")

if slv_ok["nit_proveedor"] == "06141702991026":
    ok("SLV conserva cero inicial del NIT")
else:
    fail("SLV altero NIT")

if (
    slv_ok["estado"] == "OK"
    and "DUI CON FORMATO INUSUAL"
    in str(slv_ok["advertencias"])
):
    ok("SLV DUI invalido genera warning")
else:
    fail("SLV DUI invalido esta bloqueando")

if slv_bad["estado"] == "ERROR":
    ok("SLV rechaza NIT con caracteres invalidos")
else:
    fail("SLV acepto NIT con caracteres invalidos")


if PORTAL_ACCESS_SERVICE["SLV"] == "PORTAL ACCESO CAM":
    ok("SLV usa PORTAL ACCESO CAM")
else:
    fail("Servicio SLV incorrecto")

if PORTAL_ACCESS_SERVICE["PER"] == "PORTAL ACCESO":
    ok("PER usa PORTAL ACCESO")
else:
    fail("Servicio PER incorrecto")


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
    "Limpieza PER/SLV centralizada "
    "y reglas tributarias validadas."
)
print("=" * 100)

