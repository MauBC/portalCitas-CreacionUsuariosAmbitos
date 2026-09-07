from __future__ import annotations

import argparse
from pathlib import Path

from app.services.provider_phase2_service import (
    ProviderPhase2Service,
)
from app.services.provider_excel_remote_status_service import (
    ProviderExcelRemoteStatusService,
)


def run_provider_phase2_preview(
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

    result = phase2.preview(
        run_folder=
            str(folder),
        portal_error_excel=
            portal_result_excel,
    )

    evidence_path = (
        phase2.export_evidence(
            run_folder=
                str(folder),
            preview=
                result,
        )
    )

    remote = (
        ProviderExcelRemoteStatusService()
        .export_preview(
            shared_url=
                shared_url,
            relation_results=
                result[
                    "relation_results"
                ],
            output_dir=
                str(folder),
        )
    )

    summary = result[
        "summary"
    ]

    remote_summary = remote[
        "summary"
    ]

    ok = (
        summary[
            "relaciones_sin_resultado"
        ] == 0
        and bool(
            remote[
                "ready"
            ]
        )
    )

    return {
        "ok":
            ok,
        "cuentas_enviadas":
            summary[
                "cuentas_enviadas"
            ],
        "cuentas_disponibles":
            summary[
                "cuentas_disponibles"
            ],
        "cuentas_no_creadas":
            summary[
                "cuentas_no_creadas"
            ],
        "relaciones_total":
            summary[
                "relaciones_total"
            ],
        "relaciones_validas_fase1":
            summary[
                "relaciones_validas_fase1"
            ],
        "relaciones_creado_1":
            summary[
                "relaciones_creado_1"
            ],
        "relaciones_creado_2":
            summary[
                "relaciones_creado_2"
            ],
        "relaciones_sin_resultado":
            summary[
                "relaciones_sin_resultado"
            ],
        "actualizaciones_remotas_preview":
            remote_summary[
                "actualizaciones"
            ],
        "sin_cambio_remoto":
            remote_summary[
                "sin_cambio"
            ],
        "conflictos_remotos":
            remote_summary[
                "conflictos"
            ],
        "errores_verificacion_remota":
            remote_summary[
                "errores_verificacion"
            ],
        "estados_remotos_invalidos":
            remote_summary[
                "estados_invalidos"
            ],
        "listo_para_escritura":
            remote_summary[
                "listo_para_escritura"
            ],
        "evidence_path":
            evidence_path,
        "preview_path":
            remote[
                "preview_path"
            ],
        "plan_path":
            remote[
                "plan_path"
            ],
    }


def _print_result(
    result: dict,
) -> None:
    print(
        "=" * 100
    )
    print(
        "FASE 2 PER - PREVIEW SHAREPOINT"
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
            "Relaciones validas F1",
            "relaciones_validas_fase1",
        ),
        (
            "Relaciones -> creado=1",
            "relaciones_creado_1",
        ),
        (
            "Relaciones -> creado=2",
            "relaciones_creado_2",
        ),
        (
            "Relaciones sin resultado",
            "relaciones_sin_resultado",
        ),
        (
            "Cambios remotos PREVIEW",
            "actualizaciones_remotas_preview",
        ),
        (
            "Sin cambio remoto",
            "sin_cambio_remoto",
        ),
        (
            "Conflictos remotos",
            "conflictos_remotos",
        ),
        (
            "Errores verificacion",
            "errores_verificacion_remota",
        ),
        (
            "Estados remotos invalidos",
            "estados_remotos_invalidos",
        ),
        (
            "Listo para escritura",
            "listo_para_escritura",
        ),
    ]

    for label, key in fields:
        print(
            f"{label:<30}: "
            f"{result[key]}"
        )

    print()
    print(
        "Evidencia Fase 2:"
    )
    print(
        result[
            "evidence_path"
        ]
    )

    print()
    print(
        "Excel remoto simulado:"
    )
    print(
        result[
            "preview_path"
        ]
    )

    print()
    print(
        "Plan de cambios:"
    )
    print(
        result[
            "plan_path"
        ]
    )

    print()
    print(
        "RESULTADO: "
        + (
            "OK"
            if result["ok"]
            else "REVISAR"
        )
    )

    print(
        "IMPORTANTE: "
        "este comando NO modifica SharePoint."
    )

    print(
        "=" * 100
    )


def _build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Procesar resultado real del Portal "
            "y simular creado=1/2 en el Excel "
            "PER alojado en SharePoint."
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

    output = (
        run_provider_phase2_preview(
            run_folder=
                args.run_folder,
            portal_result_excel=
                args.portal_result,
            shared_url=
                args.url,
        )
    )

    _print_result(
        output
    )
