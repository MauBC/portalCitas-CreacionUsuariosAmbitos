from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def clean_text(value) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(value).strip()


def normalize_key(value) -> str:
    text = clean_text(value).upper()

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    return re.sub(
        r"[^A-Z0-9]+",
        "",
        text,
    )


def split_counter(values) -> Counter:
    counter = Counter()

    for value in values:
        text = clean_text(value)

        if not text:
            continue

        for part in text.split("|"):
            item = part.strip()

            if item:
                counter[item] += 1

    return counter


def counter_to_df(
    counter: Counter,
    column_name: str,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                column_name: item,
                "CANTIDAD": count,
            }
            for item, count
            in counter.most_common()
        ]
    )


def latest_provider_run() -> Path:
    output_root = ROOT / "salidas"

    runs = [
        path
        for path in output_root.glob(
            "excel_proveedores_*"
        )
        if path.is_dir()
    ]

    if not runs:
        raise FileNotFoundError(
            "No existen ejecuciones excel_proveedores_*."
        )

    return max(
        runs,
        key=lambda path:
            path.stat().st_mtime,
    )


def newest_file(
    folder: Path,
    pattern: str,
) -> Path:
    matches = list(
        folder.glob(pattern)
    )

    if not matches:
        raise FileNotFoundError(
            f"No se encontro {pattern} en {folder}"
        )

    return max(
        matches,
        key=lambda path:
            path.stat().st_mtime,
    )


def build_duplicate_email_report(
    df: pd.DataFrame,
) -> pd.DataFrame:
    if "email" not in df.columns:
        return pd.DataFrame()

    work = df.copy()

    work["_email_key"] = (
        work["email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    work = work[
        work["_email_key"].ne("")
    ].copy()

    rows = []

    for email, group in work.groupby(
        "_email_key",
        sort=False,
    ):
        if len(group) <= 1:
            continue

        rucs = sorted({
            clean_text(value)
            for value in group.get(
                "ruc_proveedor",
                pd.Series(dtype=str),
            )
            if clean_text(value)
        })

        clients = sorted({
            clean_text(value)
            for value in group.get(
                "nombre_cliente",
                pd.Series(dtype=str),
            )
            if clean_text(value)
        })

        names = sorted({
            " ".join(
                part
                for part in [
                    clean_text(
                        row.get("nombre")
                    ),
                    clean_text(
                        row.get("apellido_pat")
                        or row.get("apellido")
                    ),
                ]
                if part
            )
            for _, row in group.iterrows()
        })

        rows.append({
            "CORREO": email,
            "FILAS": len(group),
            "RUC_UNICOS": len(rucs),
            "CLIENTES_UNICOS": len(clients),
            "NOMBRES_UNICOS": len(names),
            "RUC": " | ".join(rucs),
            "CLIENTES": " | ".join(clients),
            "NOMBRES": " | ".join(names),
        })

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["FILAS", "CORREO"],
            ascending=[False, True],
            ignore_index=True,
        )
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--country",
        required=True,
        choices=["PER", "SLV"],
    )

    parser.add_argument(
        "--run-folder",
        default=None,
    )

    args = parser.parse_args()

    country = args.country.upper()

    run_folder = (
        Path(args.run_folder).resolve()
        if args.run_folder
        else latest_provider_run()
    )

    normalized_path = (
        run_folder
        / "excel_proveedores_normalizado.xlsx"
    )

    error_path = newest_file(
        run_folder,
        "reporte_excel_ERRORES_*.xlsx",
    )

    valid_path = newest_file(
        run_folder,
        "reporte_excel_VALIDOS_*.xlsx",
    )

    if not normalized_path.exists():
        raise FileNotFoundError(
            normalized_path
        )

    normalized = pd.read_excel(
        normalized_path,
        dtype=str,
        keep_default_na=False,
    )

    errors = pd.read_excel(
        error_path,
        sheet_name="ERRORES_RESUMEN",
        dtype=str,
        keep_default_na=False,
    )

    valid = pd.read_excel(
        valid_path,
        sheet_name="VALIDOS_RESUMEN",
        dtype=str,
        keep_default_na=False,
    )

    estado = (
        normalized["estado"]
        if "estado" in normalized.columns
        else pd.Series(
            "",
            index=normalized.index,
        )
    )

    estado_proceso = (
        normalized["estado_proceso"]
        if "estado_proceso" in normalized.columns
        else pd.Series(
            "",
            index=normalized.index,
        )
    )

    email = (
        normalized["email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        if "email" in normalized.columns
        else pd.Series(
            "",
            index=normalized.index,
        )
    )

    client = (
        normalized["nombre_cliente"]
        .fillna("")
        .astype(str)
        .str.strip()
        if "nombre_cliente" in normalized.columns
        else pd.Series(
            "",
            index=normalized.index,
        )
    )

    valid_mask = estado.eq("OK")

    unique_valid_users = int(
        email[
            valid_mask
        ]
        .loc[
            lambda series:
                series.ne("")
        ]
        .nunique()
    )

    missing_counter = split_counter(
        errors["FALTA LLENAR"]
        if "FALTA LLENAR"
        in errors.columns
        else []
    )

    error_counter = split_counter(
        errors["ERROR"]
        if "ERROR"
        in errors.columns
        else []
    )

    warning_counter = split_counter(
        normalized["advertencias"]
        if "advertencias"
        in normalized.columns
        else []
    )

    client_counts = (
        client.value_counts(
            dropna=False
        )
        .rename_axis("CLIENTE")
        .reset_index(name="CANTIDAD")
    )

    client_counts["CLIENTE_KEY"] = (
        client_counts["CLIENTE"]
        .map(normalize_key)
    )

    duplicate_emails = (
        build_duplicate_email_report(
            normalized
        )
    )

    if country == "PER":
        non_dollarcity_mask = (
            client.map(normalize_key)
            .ne("DOLLARCITY")
        )

        non_dollarcity = (
            normalized[
                non_dollarcity_mask
            ]
            .copy()
            .reset_index(drop=True)
        )
    else:
        non_dollarcity = pd.DataFrame()

    summary_rows = [
        {
            "METRICA": "Pais",
            "VALOR": country,
        },
        {
            "METRICA": "Carpeta ejecucion",
            "VALOR": str(run_folder),
        },
        {
            "METRICA": "Filas procesadas",
            "VALOR": len(normalized),
        },
        {
            "METRICA": "Relaciones validas",
            "VALOR": int(
                estado.eq("OK").sum()
            ),
        },
        {
            "METRICA": "Errores",
            "VALOR": int(
                estado.eq("ERROR").sum()
            ),
        },
        {
            "METRICA": "Omitidos",
            "VALOR": int(
                estado.eq("OMITIDO").sum()
            ),
        },
        {
            "METRICA": "Usuarios unicos validos",
            "VALOR": unique_valid_users,
        },
        {
            "METRICA": "PENDIENTE",
            "VALOR": int(
                estado_proceso
                .eq("PENDIENTE")
                .sum()
            ),
        },
        {
            "METRICA": "YA_CREADO",
            "VALOR": int(
                estado_proceso
                .eq("YA_CREADO")
                .sum()
            ),
        },
        {
            "METRICA": "ERROR_PREVIO",
            "VALOR": int(
                estado_proceso
                .eq("ERROR_PREVIO")
                .sum()
            ),
        },
        {
            "METRICA": "ERROR_VALIDACION",
            "VALOR": int(
                estado_proceso
                .eq("ERROR_VALIDACION")
                .sum()
            ),
        },
        {
            "METRICA": "Correos duplicados",
            "VALOR": len(
                duplicate_emails
            ),
        },
        {
            "METRICA": "Clientes distintos",
            "VALOR": int(
                client[
                    client.ne("")
                ].nunique()
            ),
        },
    ]

    if country == "PER":
        summary_rows.append({
            "METRICA":
                "Filas no DOLLARCITY",
            "VALOR":
                len(non_dollarcity),
        })

    summary = pd.DataFrame(
        summary_rows
    )

    timestamp = (
        datetime.now()
        .strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    output_path = (
        run_folder
        / (
            f"diagnostico_{country}_"
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

        counter_to_df(
            missing_counter,
            "CAMPO FALTANTE",
        ).to_excel(
            writer,
            sheet_name="CAMPOS_FALTANTES",
            index=False,
        )

        counter_to_df(
            error_counter,
            "CAUSA ERROR",
        ).to_excel(
            writer,
            sheet_name="CAUSAS_ERROR",
            index=False,
        )

        counter_to_df(
            warning_counter,
            "ADVERTENCIA",
        ).to_excel(
            writer,
            sheet_name="ADVERTENCIAS",
            index=False,
        )

        client_counts.to_excel(
            writer,
            sheet_name="CLIENTES",
            index=False,
        )

        duplicate_emails.to_excel(
            writer,
            sheet_name="DUPLICADOS_EMAIL",
            index=False,
        )

        errors.to_excel(
            writer,
            sheet_name="ERRORES_DETALLE",
            index=False,
        )

        valid.to_excel(
            writer,
            sheet_name="VALIDOS_DETALLE",
            index=False,
        )

        if country == "PER":
            non_dollarcity.to_excel(
                writer,
                sheet_name="NO_DOLLARCITY",
                index=False,
            )

    print("=" * 100)
    print(
        f"DIAGNOSTICO {country}"
    )
    print("=" * 100)

    print(
        f"Carpeta             : "
        f"{run_folder}"
    )

    print(
        f"Filas               : "
        f"{len(normalized)}"
    )

    print(
        f"Relaciones OK       : "
        f"{int(estado.eq('OK').sum())}"
    )

    print(
        f"Errores             : "
        f"{int(estado.eq('ERROR').sum())}"
    )

    print(
        f"Usuarios unicos OK  : "
        f"{unique_valid_users}"
    )

    print(
        f"Correos duplicados  : "
        f"{len(duplicate_emails)}"
    )

    if country == "PER":
        print(
            f"No DOLLARCITY       : "
            f"{len(non_dollarcity)}"
        )

    print()
    print(
        "Principales campos faltantes:"
    )

    for name, count in (
        missing_counter
        .most_common(10)
    ):
        print(
            f"  {name}: {count}"
        )

    print()
    print(
        "Principales causas de error:"
    )

    for name, count in (
        error_counter
        .most_common(10)
    ):
        print(
            f"  {name}: {count}"
        )

    print()
    print(
        "Principales advertencias:"
    )

    for name, count in (
        warning_counter
        .most_common(10)
    ):
        print(
            f"  {name}: {count}"
        )

    print()
    print("Diagnostico:")
    print(output_path)
    print("=" * 100)


if __name__ == "__main__":
    main()
