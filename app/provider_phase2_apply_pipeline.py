from __future__ import annotations

import argparse
from pathlib import Path

from app.services.provider_phase2_service import (
    ProviderPhase2Service,
)
from app.services.provider_excel_remote_apply_service import (
    ProviderExcelRemoteApplyService,
)


def run_provider_phase2_apply(
    run_folder: str,
    portal_result_excel: str,
    shared_url: str,
) -> dict:
    folder = Path(
        run_folder
    )

    phase2 = (
        ProviderPhase2Service()
    )

    preview = phase2.preview(
        run_folder=str(folder),
        portal_error_excel=
            portal_result_excel,
    )

    summary = preview[
        "summary"
    ]

    if summary[
        "relaciones_sin_resultado"
    ] != 0:
        raise RuntimeError(
            "Hay relaciones sin resultado de cuenta."
        )

    evidence_path = (
        phase2.export_evidence(
            run_folder=str(folder),
            preview=preview,
        )
    )

    remote = (
        ProviderExcelRemoteApplyService()
        .apply(
            shared_url=shared_url,
            relation_results=preview[
                "relation_results"
            ],
            output_dir=str(folder),
        )
    )

    return {
        "ok": bool(
            remote["ok"]
        ),
        "cuentas_enviadas": summary[
            "cuentas_enviadas"
        ],
        "cuentas_disponibles": summary[
            "cuentas_disponibles"
        ],
        "cuentas_no_creadas": summary[
            "cuentas_no_creadas"
        ],
        "relaciones_total": summary[
            "relaciones_total"
        ],
        "relaciones_creado_1": summary[
            "relaciones_creado_1"
        ],
        "relaciones_creado_2": summary[
            "relaciones_creado_2"
        ],
        "verificado_creado_1": remote[
            "created_1"
        ],
        "verificado_creado_2": remote[
            "created_2"
        ],
        "filas_verificadas": remote[
            "verified_rows"
        ],
        "evidence_path": evidence_path,
        "backup_path": remote[
            "backup_path"
        ],
        "candidate_path": remote[
            "candidate_path"
        ],
        "verified_path": remote[
            "verified_path"
        ],
        "report_path": remote[
            "report_path"
        ],
        "sha256_uploaded": remote[
            "sha256_uploaded"
        ],
        "sha256_downloaded": remote[
            "sha256_downloaded"
        ],
    }


def _print_result(
    result: dict,
) -> None:
    print(
        "=" * 100
    )
    print(
        "FASE 2 PER - APLICACION SHAREPOINT"
    )
    print(
        "=" * 100
    )

    fields = [
        (
            "Cuentas enviadas",
            "cuentas_enviadas",
        ),
        (
            "Cuentas disponibles",
            "cuentas_disponibles",
        ),
        (
            "Cuentas no creadas",
            "cuentas_no_creadas",
        ),
        (
            "Relaciones totales",
            "relaciones_total",
        ),
        (
            "Objetivo creado=1",
            "relaciones_creado_1",
        ),
        (
            "Objetivo creado=2",
            "relaciones_creado_2",
        ),
        (
            "Verificado creado=1",
            "verificado_creado_1",
        ),
        (
            "Verificado creado=2",
            "verificado_creado_2",
        ),
        (
            "Filas verificadas",
            "filas_verificadas",
        ),
    ]

    for label, key in fields:
        print(
            f"{label:<30}: "
            f"{result[key]}"
        )

    print()
    print(
        "Backup antes de escribir:"
    )
    print(
        result["backup_path"]
    )

    print()
    print(
        "Copia objetivo subida:"
    )
    print(
        result["candidate_path"]
    )

    print()
    print(
        "Copia releida y verificada:"
    )
    print(
        result["verified_path"]
    )

    print()
    print(
        "Reporte de aplicacion:"
    )
    print(
        result["report_path"]
    )

    print()
    print(
        "SHA256 subido   : "
        + result["sha256_uploaded"]
    )
    print(
        "SHA256 releido  : "
        + result["sha256_downloaded"]
    )

    print()
    print(
        "RESULTADO: "
        + (
            "OK"
            if result["ok"]
            else "ERROR"
        )
    )

    print(
        "=" * 100
    )


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Aplicar creado=1/2 al Excel PER "
            "alojado en SharePoint y verificarlo."
        )
    )

    parser.add_argument(
        "--run-folder",
        required=True,
    )

    parser.add_argument(
        "--portal-result",
        required=True,
    )

    parser.add_argument(
        "--url",
        required=True,
    )

    return parser


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()

    result = run_provider_phase2_apply(
        run_folder=args.run_folder,
        portal_result_excel=
            args.portal_result,
        shared_url=args.url,
    )

    _print_result(
        result
    )
