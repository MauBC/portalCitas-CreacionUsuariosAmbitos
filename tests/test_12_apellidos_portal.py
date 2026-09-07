from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.excel_service import ExcelService


errors = []


def ok(message):
    print(f"[OK] {message}")


def fail(message):
    print(f"[ERROR] {message}")
    errors.append(message)


print("=" * 100)
print("TEST 12 - APELLIDOS PLANTILLA PORTAL")
print("=" * 100)

service = ExcelService(
    output_dir=str(ROOT / "salidas")
)

per = pd.DataFrame([
    {
        "pais": "PER",
        "nombre": "FRANCISCO",
        "apellido": "LULIQUIZ",
        "apellido_pat": "LULIQUIZ",
        "apellido_mat": "ROSALES",
        "email": "francisco@test.com",
        "perfil": "PROVEEDOR",
        "numero_documento": "74861676",
    },
    {
        "pais": "PER",
        "nombre": "CARLOS",
        "apellido": "PUICAN",
        "apellido_pat": "PUICAN",
        "apellido_mat": "",
        "email": "carlos@test.com",
        "perfil": "PROVEEDOR",
        "numero_documento": "74217877",
    },
])

usuarios_per = service._build_usuarios_sheet(per)

if usuarios_per.iloc[0]["APELLIDO"] == "LULIQUIZ ROSALES":
    ok("PER concatena paterno + materno")
else:
    fail("PER no concateno paterno + materno")

if usuarios_per.iloc[1]["APELLIDO"] == "PUICAN":
    ok("PER acepta apellido materno vacio")
else:
    fail("PER genero apellido incorrecto cuando materno esta vacio")

slv = pd.DataFrame([
    {
        "pais": "SLV",
        "nombre": "ANA",
        "apellido": "PEREZ LOPEZ",
        "email": "ana@test.com",
        "perfil": "PROVEEDOR",
        "numero_documento": "012345678",
    },
])

usuarios_slv = service._build_usuarios_sheet(slv)

if usuarios_slv.iloc[0]["APELLIDO"] == "PEREZ LOPEZ":
    ok("SLV conserva apellido completo")
else:
    fail("La mejora de PER afecto SLV")

summary_row = pd.Series({
    "apellido": "LULIQUIZ",
    "apellido_pat": "LULIQUIZ",
    "apellido_mat": "ROSALES",
})

if service._summary_apellido(summary_row) == "LULIQUIZ ROSALES":
    ok("Reportes tambien muestran paterno + materno")
else:
    fail("Reporte no concatena apellidos")

print()
print("=" * 100)

if errors:
    print(f"RESULTADO: ERROR ({len(errors)} problema(s))")

    for error in errors:
        print(f" - {error}")

    raise SystemExit(1)

print("RESULTADO: OK")
print("Apellidos PER/SLV correctos.")
print("=" * 100)
