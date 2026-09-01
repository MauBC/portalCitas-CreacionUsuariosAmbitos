from pathlib import Path
import argparse

import pandas as pd

from app.services.sharepoint_service import (
    SharePointService,
)
from app.config import settings


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent

OUTPUT_ROOT = (
    PROJECT_ROOT / "salidas"
)

REQUIRED_SHAREPOINT_COLUMNS = {
    "ESTADO_VALIDACION",
    "OBSERVACION_VALIDACION",
    "CLIENTE_NORMALIZADO",
}


def find_latest_run() -> Path:

    folders = sorted(
        OUTPUT_ROOT.glob(
            "ejecucion_*"
        ),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    for folder in folders:

        valid = list(
            folder.glob(
                "reporte_VALIDOS_*.xlsx"
            )
        )

        errors = list(
            folder.glob(
                "reporte_ERRORES_*.xlsx"
            )
        )

        if valid and errors:
            return folder

    raise FileNotFoundError(
        "No se encontro una ejecucion "
        "completa de FASE 1."
    )


def find_single(
    folder: Path,
    pattern: str,
) -> Path:

    files = sorted(
        folder.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    if not files:
        raise FileNotFoundError(
            f"No se encontro: {pattern}"
        )

    return files[0]


def load_report(
    path: Path,
) -> pd.DataFrame:

    workbook = pd.ExcelFile(
        path
    )

    if (
        "DATOS_TECNICOS"
        not in workbook.sheet_names
    ):
        raise ValueError(
            f"{path.name} no contiene "
            "DATOS_TECNICOS"
        )

    return pd.read_excel(
        path,
        sheet_name="DATOS_TECNICOS",
        dtype=str,
    )


def validate_sharepoint_columns(
    service: SharePointService,
):

    client = service.client

    site_id = (
        client.get_site_id()
    )

    list_id = client.get_list_id(
        settings.SHAREPOINT_LIST_NAME
    )

    response = client.graph.get(
        f"/sites/{site_id}/lists/"
        f"{list_id}/columns"
    )

    columns = response.get(
        "value",
        []
    )

    internal_names = {
        str(
            col.get("name") or ""
        ).strip()
        for col in columns
    }

    print()
    print(
        "Columnas SharePoint:"
    )

    for required in sorted(
        REQUIRED_SHAREPOINT_COLUMNS
    ):

        if required in internal_names:
            print(
                f"  [OK] {required}"
            )

        else:
            print(
                f"  [ERROR] {required}"
            )

    missing = (
        REQUIRED_SHAREPOINT_COLUMNS
        - internal_names
    )

    if missing:
        raise RuntimeError(
            "Faltan columnas internas en "
            "SharePoint: "
            + ", ".join(
                sorted(missing)
            )
        )


def run(
    write: bool = False,
):

    print(
        "=" * 100
    )
    print(
        "FASE 1 - DESPLIEGUE SHAREPOINT"
    )
    print(
        "=" * 100
    )

    folder = find_latest_run()

    valid_path = find_single(
        folder,
        "reporte_VALIDOS_*.xlsx",
    )

    error_path = find_single(
        folder,
        "reporte_ERRORES_*.xlsx",
    )

    print()
    print(
        "Ejecucion:",
        folder
    )

    print(
        "VALIDOS:",
        valid_path.name
    )

    print(
        "ERRORES:",
        error_path.name
    )

    valid = load_report(
        valid_path
    )

    errors = load_report(
        error_path
    )

    df = pd.concat(
        [
            valid,
            errors,
        ],
        ignore_index=True,
    )

    if "_item_id" not in df.columns:
        raise ValueError(
            "No existe _item_id."
        )

    duplicated = (
        df["_item_id"]
        .duplicated()
        .sum()
    )

    if duplicated:
        raise ValueError(
            f"Hay {duplicated} "
            "_item_id duplicados."
        )

    service = SharePointService()

    validate_sharepoint_columns(
        service
    )

    preview_rows = []

    for _, row in df.iterrows():

        payload = (
            service
            ._build_validation_payload(
                row
            )
        )

        preview_rows.append({
            "_item_id":
                row["_item_id"],

            "email":
                row.get(
                    "email",
                    ""
                ),

            **payload,
        })

    preview = pd.DataFrame(
        preview_rows
    )

    print()
    print("-" * 100)
    print(
        "RESUMEN"
    )
    print("-" * 100)

    counts = (
        preview[
            "ESTADO_VALIDACION"
        ]
        .value_counts()
    )

    for status, total in (
        counts.items()
    ):
        print(
            f"{status:<25}: {total}"
        )

    print(
        f"{'TOTAL':<25}: "
        f"{len(preview)}"
    )

    print()
    print("-" * 100)
    print(
        "REGISTROS QUE REQUIEREN ATENCION"
    )
    print("-" * 100)

    attention = preview[
        preview[
            "ESTADO_VALIDACION"
        ]
        != "LISTO_PARA_CARGA"
    ]

    if attention.empty:
        print(
            "Ninguno."
        )

    else:
        print(
            attention[
                [
                    "_item_id",
                    "email",
                    "ESTADO_VALIDACION",
                    "CLIENTE_NORMALIZADO",
                    "OBSERVACION_VALIDACION",
                ]
            ]
            .to_string(
                index=False
            )
        )

    if not write:

        print()
        print(
            "=" * 100
        )
        print(
            "PREVIEW SOLAMENTE"
        )
        print(
            "SharePoint NO fue modificado."
        )
        print(
            "=" * 100
        )

        return

    print()
    print(
        "Escribiendo resultados "
        "en SharePoint..."
    )

    result = (
        service
        .push_validation_results_batch(
            df
        )
    )

    print()
    print(
        "Actualizados:",
        result.get(
            "updated",
            0
        )
    )

    failed = result.get(
        "failed",
        []
    )

    print(
        "Fallidos:",
        len(failed)
    )

    if failed:
        print()
        print(
            "DETALLE DE FALLIDOS:"
        )

        for item in failed:
            print(
                item
            )

        raise RuntimeError(
            "Hubo actualizaciones "
            "fallidas en SharePoint."
        )

    print()
    print(
        "=" * 100
    )
    print(
        "SHAREPOINT ACTUALIZADO "
        "CORRECTAMENTE"
    )
    print(
        "CREADO NO FUE MODIFICADO"
    )
    print(
        "=" * 100
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Escribir realmente "
            "en SharePoint."
        ),
    )

    args = parser.parse_args()

    run(
        write=args.write
    )
