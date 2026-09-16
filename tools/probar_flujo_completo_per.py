from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from app.config.env_loader import load_env

load_env()


from app.phase3_pipeline import (
    run_phase3_final,
    run_phase3_preview,
)
from app.provider_excel_pipeline import (
    run_provider_excel,
)
from app.services.provider_creation_status_service import (
    ProviderCreationStatusService,
)
from app.services.provider_excel_source_service import (
    ProviderExcelSourceService,
)
from app.services.provider_phase2_service import (
    ProviderPhase2Service,
)


def section(title: str) -> None:
    print()
    print("=" * 110)
    print(title)
    print("=" * 110)


def build_status_counts(df: pd.DataFrame) -> dict:
    if "creado" not in df.columns:
        return {
            "creado_0": 0,
            "creado_1": 0,
            "creado_2": 0,
            "creado_invalido": 0,
        }

    status_service = (
        ProviderCreationStatusService()
    )

    normalized = (
        df["creado"]
        .map(
            status_service.normalize
        )
    )

    return {
        "creado_0":
            int(
                normalized.eq(0).sum()
            ),
        "creado_1":
            int(
                normalized.eq(1).sum()
            ),
        "creado_2":
            int(
                normalized.eq(2).sum()
            ),
        "creado_invalido":
            int(
                normalized.isna().sum()
            ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prueba integral PER: "
            "SharePoint -> Fase 1 -> "
            "Fase 2 simulada OK -> "
            "Fase 3 Ambitos."
        )
    )

    parser.add_argument(
        "--url",
        required=True,
        help=(
            "URL compartida del Excel "
            "de proveedores en SharePoint."
        ),
    )

    args = parser.parse_args()

    shared_url = str(
        args.url or ""
    ).strip()

    if not shared_url:
        raise ValueError(
            "La URL de SharePoint esta vacia."
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    test_root = (
        ROOT
        / "salidas"
        / (
            "prueba_flujo_completo_PER_"
            f"{timestamp}"
        )
    )

    test_root.mkdir(
        parents=True,
        exist_ok=False,
    )


    # =========================================================
    # 0. LEER EXCEL REAL
    # =========================================================

    section(
        "0. LECTURA DEL EXCEL REAL DE SHAREPOINT"
    )

    source_service = (
        ProviderExcelSourceService()
    )

    source_real = (
        source_service
        .load_sharepoint(
            shared_url
        )
    )

    if source_real.empty:
        raise RuntimeError(
            "El Excel remoto no contiene filas."
        )

    original_status = (
        build_status_counts(
            source_real
        )
    )

    print(
        f"Filas leidas                 : "
        f"{len(source_real)}"
    )

    print(
        f"creado=0 original            : "
        f"{original_status['creado_0']}"
    )

    print(
        f"creado=1 original            : "
        f"{original_status['creado_1']}"
    )

    print(
        f"creado=2 original            : "
        f"{original_status['creado_2']}"
    )

    print(
        f"creado invalido original     : "
        f"{original_status['creado_invalido']}"
    )


    # =========================================================
    # 1. SIMULAR ESTADO INICIAL creado=0
    # =========================================================

    section(
        "1. SIMULACION: TODAS LAS FILAS COMO creado=0"
    )

    source_simulated = (
        source_real.copy()
    )

    source_simulated[
        "creado"
    ] = 0

    simulated_source_path = (
        test_root
        / "excel_fuente_SIMULADO_creado_0.xlsx"
    )

    with pd.ExcelWriter(
        simulated_source_path,
        engine="openpyxl",
    ) as writer:
        source_simulated.to_excel(
            writer,
            sheet_name="Proveedores",
            index=False,
        )

    print(
        "[OK] Se genero una copia local "
        "de evidencia."
    )

    print(
        "[OK] El Excel remoto NO fue modificado."
    )

    print(
        f"Copia simulada:\n"
        f"{simulated_source_path}"
    )


    # =========================================================
    # 2. FASE 1 PER
    # =========================================================

    section(
        "2. FASE 1 PER - LIMPIEZA Y PLANTILLA DE USUARIOS"
    )

    # El pipeline cree que esta leyendo SharePoint,
    # pero durante esta llamada recibe la copia en memoria
    # con creado=0.
    #
    # Esto evita cualquier cambio en el archivo remoto.

    with patch.object(
        ProviderExcelSourceService,
        "load_sharepoint",
        return_value=
            source_simulated.copy(),
    ):
        phase1 = run_provider_excel(
            country_code="PER",
            source_type="sharepoint",
            shared_url=shared_url,
            validate_existing_emails=False,
            output_root=test_root,
        )

    run_folder = Path(
        phase1["run_folder"]
    )

    print(
        f"Filas procesadas              : "
        f"{phase1['total']}"
    )

    print(
        f"Relaciones validas            : "
        f"{phase1['valid_relations']}"
    )

    print(
        f"Errores                       : "
        f"{phase1['errors']}"
    )

    print(
        f"Usuarios unicos               : "
        f"{phase1['unique_users']}"
    )

    print(
        f"Correos BD validados          : "
        f"{phase1['existing_emails_db']}"
        " (DESACTIVADO PARA ESTE TEST)"
    )

    print()
    print(
        "Plantilla usuarios:"
    )

    print(
        phase1[
            "template_path"
        ]
        or "NO GENERADA"
    )

    if (
        phase1[
            "valid_relations"
        ] <= 0
    ):
        raise RuntimeError(
            "FASE 1 no produjo relaciones validas."
        )

    if not phase1[
        "template_path"
    ]:
        raise RuntimeError(
            "FASE 1 no genero plantilla de usuarios."
        )


    # =========================================================
    # 3. FASE 2 SIMULADA
    # =========================================================

    section(
        "3. FASE 2 SIMULADA - TODAS LAS CUENTAS OK"
    )

    # Un Excel de resultado sin errores significa:
    # todas las cuentas enviadas fueron creadas
    # o estan disponibles correctamente.

    portal_simulated_path = (
        run_folder
        / "resultado_portal_SIMULADO_TODO_OK.xlsx"
    )

    pd.DataFrame(
        columns=[
            "Email",
            "Mensaje de Error",
        ]
    ).to_excel(
        portal_simulated_path,
        index=False,
    )

    phase2_service = (
        ProviderPhase2Service()
    )

    phase2 = (
        phase2_service
        .preview(
            run_folder=
                str(run_folder),
            portal_error_excel=
                str(
                    portal_simulated_path
                ),
        )
    )

    phase2_evidence_path = (
        phase2_service
        .export_evidence(
            run_folder=
                str(run_folder),
            preview=phase2,
        )
    )

    phase2_summary = (
        phase2[
            "summary"
        ]
    )

    print(
        f"Cuentas enviadas              : "
        f"{phase2_summary['cuentas_enviadas']}"
    )

    print(
        f"Cuentas disponibles           : "
        f"{phase2_summary['cuentas_disponibles']}"
    )

    print(
        f"Cuentas no creadas            : "
        f"{phase2_summary['cuentas_no_creadas']}"
    )

    print(
        f"Relaciones total              : "
        f"{phase2_summary['relaciones_total']}"
    )

    print(
        f"Relaciones -> creado=1        : "
        f"{phase2_summary['relaciones_creado_1']}"
    )

    print(
        f"Relaciones -> creado=2        : "
        f"{phase2_summary['relaciones_creado_2']}"
    )

    print(
        f"Relaciones sin resultado      : "
        f"{phase2_summary['relaciones_sin_resultado']}"
    )

    if (
        phase2_summary[
            "relaciones_sin_resultado"
        ] != 0
    ):
        raise RuntimeError(
            "FASE 2 dejo relaciones sin resultado."
        )


    # =========================================================
    # 4. ESTADO SIMULADO PARA FASE 3
    # =========================================================

    section(
        "4. PREPARAR ESTADO SIMULADO PARA AMBITOS"
    )

    relation_results = (
        phase2[
            "relation_results"
        ].copy()
    )

    required_status_columns = {
        "_item_id",
        "creado_objetivo",
    }

    missing_status = (
        required_status_columns
        - set(
            relation_results.columns
        )
    )

    if missing_status:
        raise RuntimeError(
            "Faltan columnas en resultado Fase 2: "
            + ", ".join(
                sorted(
                    missing_status
                )
            )
        )

    provider_status_df = (
        relation_results[
            [
                "_item_id",
                "creado_objetivo",
            ]
        ]
        .rename(
            columns={
                "creado_objetivo":
                    "creado",
            }
        )
        .copy()
    )

    simulated_status_path = (
        run_folder
        / "estado_simulado_fase3.xlsx"
    )

    provider_status_df.to_excel(
        simulated_status_path,
        index=False,
    )

    created_for_ambitos = int(
        pd.to_numeric(
            provider_status_df[
                "creado"
            ],
            errors="coerce",
        )
        .eq(1)
        .sum()
    )

    print(
        f"Relaciones habilitadas        : "
        f"{created_for_ambitos}"
    )

    print(
        f"Estado simulado:\n"
        f"{simulated_status_path}"
    )


    # =========================================================
    # 5. FASE 3 PREVIEW
    # =========================================================

    section(
        "5. FASE 3 PER - PREVIEW DE AMBITOS"
    )

    phase3_preview = (
        run_phase3_preview(
            valid_report_path=
                phase1[
                    "valid_path"
                ],
            country_code="PER",
            provider_status_df=
                provider_status_df,
        )
    )

    print(
        f"Registros fuente              : "
        f"{phase3_preview['usuarios_fuente']}"
    )

    print(
        f"Registros con creado=1        : "
        f"{phase3_preview['usuarios']}"
    )

    print(
        f"Matched DOLLARCITY            : "
        f"{phase3_preview['matched']}"
    )

    print(
        f"Revision manual               : "
        f"{phase3_preview['no_match']}"
    )

    print(
        f"Entidades                     : "
        f"{phase3_preview['entidades']}"
    )

    print(
        f"RelacionNueva                 : "
        f"{phase3_preview['relacion_nueva']}"
    )

    print(
        f"Ambitos                       : "
        f"{phase3_preview['ambitos']}"
    )

    print()
    print(
        "Plantilla PREVIEW:"
    )

    print(
        phase3_preview[
            "template_path"
        ]
    )

    if (
        phase3_preview[
            "no_match"
        ] != 0
    ):
        print()
        print(
            "[REVISAR] Existen relaciones "
            "que requieren revision de cliente."
        )

        print(
            "Archivo:"
        )

        print(
            phase3_preview[
                "review_path"
            ]
        )

        raise RuntimeError(
            "No se genera FINAL mientras existan "
            "clientes sin resolver."
        )


    # =========================================================
    # 6. FASE 3 FINAL
    # =========================================================

    section(
        "6. FASE 3 PER - PLANTILLA FINAL DE AMBITOS"
    )

    phase3_final = (
        run_phase3_final(
            valid_report_path=
                phase1[
                    "valid_path"
                ],
            country_code="PER",
            provider_status_df=
                provider_status_df,
        )
    )

    print(
        f"creado=1                     : "
        f"{phase3_final['creado_1']}"
    )

    print(
        f"Automaticos                  : "
        f"{phase3_final['automaticos']}"
    )

    print(
        f"Pendientes cliente           : "
        f"{phase3_final['pendientes_cliente']}"
    )

    print(
        f"Pendientes tecnicos          : "
        f"{phase3_final['pendientes_tecnicos']}"
    )

    print(
        f"Registros finales            : "
        f"{phase3_final['registros_finales']}"
    )

    print(
        f"Entidades                    : "
        f"{phase3_final['entidades']}"
    )

    print(
        f"RelacionNueva                : "
        f"{phase3_final['relacion_nueva']}"
    )

    print(
        f"Ambitos                      : "
        f"{phase3_final['ambitos']}"
    )

    print()
    print(
        "Plantilla FINAL:"
    )

    print(
        phase3_final[
            "template_path"
        ]
    )


    # =========================================================
    # 7. RESUMEN
    # =========================================================

    section(
        "7. RESUMEN DEL TEST INTEGRAL"
    )

    summary_rows = [
        {
            "ETAPA":
                "ORIGEN",
            "METRICA":
                "Filas Excel SharePoint",
            "VALOR":
                len(source_real),
        },
        {
            "ETAPA":
                "ORIGEN",
            "METRICA":
                "creado=1 real antes del test",
            "VALOR":
                original_status[
                    "creado_1"
                ],
        },
        {
            "ETAPA":
                "SIMULACION",
            "METRICA":
                "Filas tratadas como creado=0",
            "VALOR":
                len(source_simulated),
        },
        {
            "ETAPA":
                "FASE 1",
            "METRICA":
                "Relaciones validas",
            "VALOR":
                phase1[
                    "valid_relations"
                ],
        },
        {
            "ETAPA":
                "FASE 1",
            "METRICA":
                "Errores",
            "VALOR":
                phase1[
                    "errors"
                ],
        },
        {
            "ETAPA":
                "FASE 1",
            "METRICA":
                "Usuarios unicos",
            "VALOR":
                phase1[
                    "unique_users"
                ],
        },
        {
            "ETAPA":
                "FASE 2",
            "METRICA":
                "Cuentas simuladas disponibles",
            "VALOR":
                phase2_summary[
                    "cuentas_disponibles"
                ],
        },
        {
            "ETAPA":
                "FASE 2",
            "METRICA":
                "Relaciones creado=1",
            "VALOR":
                phase2_summary[
                    "relaciones_creado_1"
                ],
        },
        {
            "ETAPA":
                "FASE 2",
            "METRICA":
                "Relaciones creado=2",
            "VALOR":
                phase2_summary[
                    "relaciones_creado_2"
                ],
        },
        {
            "ETAPA":
                "FASE 3 PREVIEW",
            "METRICA":
                "Matched",
            "VALOR":
                phase3_preview[
                    "matched"
                ],
        },
        {
            "ETAPA":
                "FASE 3 PREVIEW",
            "METRICA":
                "No match",
            "VALOR":
                phase3_preview[
                    "no_match"
                ],
        },
        {
            "ETAPA":
                "FASE 3 FINAL",
            "METRICA":
                "Entidades",
            "VALOR":
                phase3_final[
                    "entidades"
                ],
        },
        {
            "ETAPA":
                "FASE 3 FINAL",
            "METRICA":
                "RelacionNueva",
            "VALOR":
                phase3_final[
                    "relacion_nueva"
                ],
        },
        {
            "ETAPA":
                "FASE 3 FINAL",
            "METRICA":
                "Ambitos",
            "VALOR":
                phase3_final[
                    "ambitos"
                ],
        },
        {
            "ETAPA":
                "FASE 3 FINAL",
            "METRICA":
                "Pendientes totales",
            "VALOR":
                phase3_final[
                    "pendientes_total"
                ],
        },
    ]

    summary_path = (
        run_folder
        / "resumen_flujo_completo_PER.xlsx"
    )

    with pd.ExcelWriter(
        summary_path,
        engine="openpyxl",
    ) as writer:
        pd.DataFrame(
            summary_rows
        ).to_excel(
            writer,
            sheet_name="RESUMEN",
            index=False,
        )

        phase2[
            "account_results"
        ].to_excel(
            writer,
            sheet_name="CUENTAS_SIMULADAS",
            index=False,
        )

        phase2[
            "relation_results"
        ].to_excel(
            writer,
            sheet_name="RELACIONES_FASE2",
            index=False,
        )

        provider_status_df.to_excel(
            writer,
            sheet_name="ESTADO_FASE3",
            index=False,
        )


    final_ok = (
        phase3_preview[
            "no_match"
        ] == 0
        and phase3_final[
            "pendientes_total"
        ] == 0
        and phase3_final[
            "registros_finales"
        ] > 0
    )

    print(
        f"Carpeta general:\n"
        f"{test_root}"
    )

    print()

    print(
        f"Carpeta ejecucion:\n"
        f"{run_folder}"
    )

    print()

    print(
        f"Resumen:\n"
        f"{summary_path}"
    )

    print()

    print(
        f"Evidencia Fase 2:\n"
        f"{phase2_evidence_path}"
    )

    print()

    if final_ok:
        print(
            "[OK] FLUJO COMPLETO PER FINALIZADO "
            "CORRECTAMENTE"
        )

        print(
            "[OK] No se modifico el Excel remoto."
        )

        print(
            "[OK] Todas las relaciones validas "
            "fueron simuladas como creadas."
        )

        print(
            "[OK] La plantilla FINAL de Ambitos "
            "fue generada."
        )

    else:
        print(
            "[REVISAR] El flujo termino, "
            "pero existen pendientes."
        )


if __name__ == "__main__":
    main()
