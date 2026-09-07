from __future__ import annotations

import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT),
    )


def text(value) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def key(value) -> str:
    value = text(value).upper()

    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    return re.sub(
        r"[^A-Z0-9]+",
        "",
        value,
    )


def latest_run() -> Path:
    folders = [
        item
        for item in (
            ROOT / "salidas"
        ).glob(
            "excel_proveedores_*"
        )
        if item.is_dir()
    ]

    if not folders:
        raise FileNotFoundError(
            "No existen ejecuciones."
        )

    return max(
        folders,
        key=lambda item:
            item.stat().st_mtime,
    )


run_folder = latest_run()

normalized_path = (
    run_folder
    / "excel_proveedores_normalizado.xlsx"
)

df = pd.read_excel(
    normalized_path,
    dtype=str,
    keep_default_na=False,
)

client = (
    df["nombre_cliente"]
    .fillna("")
    .astype(str)
    .str.strip()
)

client_key = client.map(
    key
)

blank_client = df[
    client.eq("")
].copy()

other_client = df[
    client.ne("")
    & client_key.ne(
        "DOLLARCITY"
    )
].copy()

other_values = (
    other_client[
        "nombre_cliente"
    ]
    .value_counts()
    .rename_axis(
        "CLIENTE"
    )
    .reset_index(
        name="CANTIDAD"
    )
)

email = (
    df["email"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

duplicate_mask = (
    email.ne("")
    & email.duplicated(
        keep=False
    )
)

duplicate_rows = df[
    duplicate_mask
].copy()

columns = [
    column
    for column in [
        "_orden_origen",
        "email",
        "nombre",
        "apellido",
        "apellido_pat",
        "apellido_mat",
        "numero_documento",
        "nombre_cliente",
        "nombre_proveedor",
        "ruc_proveedor",
        "estado",
        "observaciones",
        "advertencias",
        "correo_repetido",
        "usuario_principal",
        "seleccion_usuario",
        "creado",
        "estado_proceso",
    ]
    if column in duplicate_rows.columns
]

duplicate_detail = (
    duplicate_rows[
        columns
    ].copy()
)

summary = pd.DataFrame([
    {
        "METRICA":
            "Filas totales",
        "VALOR":
            len(df),
    },
    {
        "METRICA":
            "DOLLARCITY exacto/normalizado",
        "VALOR":
            int(
                client_key
                .eq(
                    "DOLLARCITY"
                )
                .sum()
            ),
    },
    {
        "METRICA":
            "Cliente vacio",
        "VALOR":
            len(
                blank_client
            ),
    },
    {
        "METRICA":
            "Cliente no vacio distinto DOLLARCITY",
        "VALOR":
            len(
                other_client
            ),
    },
    {
        "METRICA":
            "Filas con correo repetido",
        "VALOR":
            len(
                duplicate_rows
            ),
    },
])

timestamp = (
    datetime.now()
    .strftime(
        "%Y%m%d_%H%M%S"
    )
)

output_path = (
    run_folder
    / (
        "analisis_clientes_repetidos_PER_"
        f"{timestamp}.xlsx"
    )
)

with pd.ExcelWriter(
    output_path,
    engine="openpyxl",
) as writer:
    summary.to_excel(
        writer,
        sheet_name="RESUMEN",
        index=False,
    )

    other_values.to_excel(
        writer,
        sheet_name="OTROS_CLIENTES_RESUMEN",
        index=False,
    )

    other_client.to_excel(
        writer,
        sheet_name="OTROS_CLIENTES_DETALLE",
        index=False,
    )

    blank_client.to_excel(
        writer,
        sheet_name="CLIENTE_VACIO",
        index=False,
    )

    duplicate_detail.to_excel(
        writer,
        sheet_name="CORREOS_REPETIDOS",
        index=False,
    )

print("=" * 100)
print(
    "ANALISIS CLIENTES Y CORREOS REPETIDOS"
)
print("=" * 100)
print(
    f"Filas totales                   : "
    f"{len(df)}"
)
print(
    f"DOLLARCITY normalizado          : "
    f"{int(client_key.eq('DOLLARCITY').sum())}"
)
print(
    f"Cliente vacio                   : "
    f"{len(blank_client)}"
)
print(
    f"Otro cliente no vacio           : "
    f"{len(other_client)}"
)
print(
    f"Filas de correos repetidos      : "
    f"{len(duplicate_rows)}"
)

print()
print(
    "Valores no vacios distintos "
    "de DOLLARCITY:"
)

if other_values.empty:
    print(
        "  Ninguno"
    )
else:
    for _, row in (
        other_values.iterrows()
    ):
        print(
            f"  {row['CLIENTE']}: "
            f"{row['CANTIDAD']}"
        )

print()
print(
    "Archivo:"
)
print(
    output_path
)
print("=" * 100)
