from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def text(value) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def latest_run() -> Path:
    folders = [
        path
        for path in (ROOT / "salidas").glob(
            "excel_proveedores_*"
        )
        if path.is_dir()
    ]

    if not folders:
        raise FileNotFoundError(
            "No existen ejecuciones excel_proveedores_*."
        )

    return max(
        folders,
        key=lambda path:
            path.stat().st_mtime,
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

if "estado" not in df.columns:
    raise ValueError(
        "El normalizado no contiene columna estado."
    )

if "email" not in df.columns:
    raise ValueError(
        "El normalizado no contiene columna email."
    )


email_key = (
    df["email"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

valid_emails = set(
    email_key[
        df["estado"].eq("OK")
        & email_key.ne("")
    ]
    .tolist()
)

errors = df[
    df["estado"].eq("ERROR")
].copy()

errors["_email_key"] = (
    errors["email"]
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
)

errors[
    "CUENTA_CUBIERTA_POR_OTRA_FILA_VALIDA"
] = errors["_email_key"].apply(
    lambda value:
        bool(
            value
            and value in valid_emails
        )
)

business_columns = [
    column
    for column in [
        "nombre",
        "apellido",
        "apellido_pat",
        "apellido_mat",
        "email",
        "numero_documento",
        "nombre_cliente",
        "nombre_proveedor",
        "ruc_proveedor",
        "ruc_cliente",
        "tipo_usuario",
        "perfil",
        "telefono",
    ]
    if column in errors.columns
]


def populated_business_fields(
    row,
) -> int:
    return sum(
        1
        for column in business_columns
        if text(
            row.get(column)
        )
    )


errors[
    "CAMPOS_NEGOCIO_LLENOS"
] = errors.apply(
    populated_business_fields,
    axis=1,
)


def classify(row) -> str:
    observations = text(
        row.get("observaciones")
    ).upper()

    filled = int(
        row.get(
            "CAMPOS_NEGOCIO_LLENOS",
            0,
        )
    )

    covered = bool(
        row.get(
            "CUENTA_CUBIERTA_POR_OTRA_FILA_VALIDA",
            False,
        )
    )

    if (
        "CLIENTE NO RECONOCIDO"
        in observations
    ):
        return "CLIENTE_NO_RECONOCIDO"

    if covered:
        return "ERROR_CUBIERTO_POR_OTRA_FILA_VALIDA"

    if filled <= 1:
        return "FILA_CASI_VACIA"

    if "CORREO INVALIDO" in observations:
        return "CORREO_INVALIDO"

    if (
        "TIPO DE USUARIO INVALIDO"
        in observations
    ):
        return "TIPO_USUARIO_INVALIDO"

    return "DATOS_INCOMPLETOS"


errors[
    "CLASIFICACION_AUDITORIA"
] = errors.apply(
    classify,
    axis=1,
)

summary = (
    errors[
        "CLASIFICACION_AUDITORIA"
    ]
    .value_counts()
    .rename_axis(
        "CLASIFICACION"
    )
    .reset_index(
        name="CANTIDAD"
    )
)

covered_count = int(
    errors[
        "CUENTA_CUBIERTA_POR_OTRA_FILA_VALIDA"
    ].sum()
)

uncovered = errors[
    ~errors[
        "CUENTA_CUBIERTA_POR_OTRA_FILA_VALIDA"
    ]
].copy()

uncovered_with_email = uncovered[
    uncovered["_email_key"].ne("")
].copy()

uncovered_without_email = uncovered[
    uncovered["_email_key"].eq("")
].copy()

account_summary = pd.DataFrame([
    {
        "METRICA":
            "Filas ERROR",
        "VALOR":
            len(errors),
    },
    {
        "METRICA":
            "Errores cubiertos por otra fila valida del mismo correo",
        "VALOR":
            covered_count,
    },
    {
        "METRICA":
            "Errores no cubiertos",
        "VALOR":
            len(uncovered),
    },
    {
        "METRICA":
            "Errores no cubiertos con correo",
        "VALOR":
            len(uncovered_with_email),
    },
    {
        "METRICA":
            "Errores no cubiertos sin correo",
        "VALOR":
            len(uncovered_without_email),
    },
    {
        "METRICA":
            "Correos unicos validos para crear",
        "VALOR":
            len(valid_emails),
    },
])


preferred_columns = [
    column
    for column in [
        "_orden_origen",
        "email",
        "nombre",
        "apellido",
        "apellido_pat",
        "numero_documento",
        "nombre_cliente",
        "nombre_proveedor",
        "ruc_proveedor",
        "creado",
        "estado_proceso",
        "FALTA LLENAR",
        "observaciones",
        "advertencias",
        "seleccion_usuario",
        "CAMPOS_NEGOCIO_LLENOS",
        "CUENTA_CUBIERTA_POR_OTRA_FILA_VALIDA",
        "CLASIFICACION_AUDITORIA",
    ]
    if column in errors.columns
]

detail = errors[
    preferred_columns
].copy()

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

output_path = (
    run_folder
    / f"auditoria_errores_PER_{timestamp}.xlsx"
)

with pd.ExcelWriter(
    output_path,
    engine="openpyxl",
) as writer:
    account_summary.to_excel(
        writer,
        sheet_name="RESUMEN_CUENTAS",
        index=False,
    )

    summary.to_excel(
        writer,
        sheet_name="RESUMEN_ERRORES",
        index=False,
    )

    detail.to_excel(
        writer,
        sheet_name="ERRORES_DETALLE",
        index=False,
    )

    errors[
        errors[
            "CUENTA_CUBIERTA_POR_OTRA_FILA_VALIDA"
        ]
    ][
        preferred_columns
    ].to_excel(
        writer,
        sheet_name="CUBIERTOS",
        index=False,
    )

    uncovered[
        preferred_columns
    ].to_excel(
        writer,
        sheet_name="NO_CUBIERTOS",
        index=False,
    )

    uncovered_with_email[
        preferred_columns
    ].to_excel(
        writer,
        sheet_name="NO_CUBIERTOS_CON_EMAIL",
        index=False,
    )

    uncovered_without_email[
        preferred_columns
    ].to_excel(
        writer,
        sheet_name="NO_CUBIERTOS_SIN_EMAIL",
        index=False,
    )


print("=" * 100)
print(
    "AUDITORIA DE ERRORES PER"
)
print("=" * 100)
print(
    f"Carpeta                            : {run_folder}"
)
print(
    f"Filas ERROR                        : {len(errors)}"
)
print(
    f"Errores cubiertos por otra fila OK : {covered_count}"
)
print(
    f"Errores no cubiertos               : {len(uncovered)}"
)
print(
    f"No cubiertos con correo            : {len(uncovered_with_email)}"
)
print(
    f"No cubiertos sin correo            : {len(uncovered_without_email)}"
)
print(
    f"Correos unicos validos             : {len(valid_emails)}"
)

print()
print(
    "Clasificacion:"
)

for _, row in summary.iterrows():
    print(
        f"  {row['CLASIFICACION']}: "
        f"{row['CANTIDAD']}"
    )

print()
print("Archivo:")
print(output_path)
print("=" * 100)
