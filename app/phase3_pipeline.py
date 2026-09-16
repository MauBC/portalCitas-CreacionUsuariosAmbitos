import glob
import os

import pandas as pd

from app.clients.sharepoint_client import (
    SharePointClient
)
from app.config.settings import settings
from app.services.ambitos_assignment_service import (
    AmbitosAssignmentService
)
from app.services.ambitos_builder_service import (
    AmbitosBuilderService
)
from app.services.ambitos_config_service import (
    AmbitosConfigService
)
from app.services.ambitos_excel_service import (
    AmbitosExcelService
)
from app.services.ambitos_review_service import (
    AmbitosReviewService
)
from app.services.db_validation_service import (
    DbValidationService
)
from app.services.provider_excel_mapping_service import (
    ProviderExcelMappingService
)
from app.services.provider_excel_source_service import (
    ProviderExcelSourceService
)


def _normalize_item_id(
    value,
) -> str:
    text = str(
        value or ""
    ).strip()

    if text.endswith(".0"):
        prefix = text[:-2]

        if prefix.isdigit():
            return prefix

    return text


def _parse_created_status(
    value,
) -> int | None:
    text = str(
        value or ""
    ).strip()

    if not text:
        return 0

    try:
        status = int(
            float(text)
        )
    except (TypeError, ValueError):
        return None

    if status not in {0, 1, 2}:
        return None

    return status


def _filter_created_rows_slv(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    if "_item_id" not in df.columns:
        raise ValueError(
            "FASE 3 requiere _item_id "
            "para validar CREADO en SharePoint."
        )

    client = SharePointClient()

    items = client.get_list_items(
        settings.SHAREPOINT_LIST_NAME
    )

    available_ids = set()
    invalid_statuses = []

    for item in items:
        item_id = _normalize_item_id(
            item.get("id")
        )

        fields = item.get(
            "fields",
            {},
        )

        status = _parse_created_status(
            fields.get("CREADO")
        )

        if status is None:
            invalid_statuses.append(
                item_id
            )
            continue

        if status == 1:
            available_ids.add(
                item_id
            )

    if invalid_statuses:
        raise ValueError(
            "Existen estados CREADO invalidos "
            "en SharePoint SLV: "
            + ", ".join(
                invalid_statuses[:10]
            )
        )

    work = df.copy()

    work["_item_id"] = (
        work["_item_id"]
        .apply(
            _normalize_item_id
        )
    )

    before = len(work)

    work = (
        work[
            work["_item_id"].isin(
                available_ids
            )
        ]
        .copy()
        .reset_index(drop=True)
    )

    return (
        work,
        {
            "filtered_out":
                before - len(work),
            "status_source_count":
                len(items),
            "status_created_1":
                len(available_ids),
            "status_not_created_1":
                len(items) - len(available_ids),
        },
    )


def _prepare_per_status_df(
    provider_status_df: pd.DataFrame,
) -> pd.DataFrame:
    if (
        "_item_id"
        in provider_status_df.columns
        and "creado"
        in provider_status_df.columns
    ):
        return provider_status_df.copy()

    return (
        ProviderExcelMappingService()
        .map(
            provider_status_df,
            "PER",
        )
    )


def _filter_created_rows_per(
    df: pd.DataFrame,
    provider_shared_url: str | None = None,
    provider_status_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    if "_item_id" not in df.columns:
        raise ValueError(
            "FASE 3 PER requiere _item_id "
            "para validar creado en el Excel."
        )

    if provider_status_df is None:
        provider_shared_url = str(
            provider_shared_url or ""
        ).strip()

        if not provider_shared_url:
            raise ValueError(
                "FASE 3 PER requiere la URL "
                "del Excel de proveedores en SharePoint."
            )

        provider_status_df = (
            ProviderExcelSourceService()
            .load_sharepoint(
                provider_shared_url
            )
        )

    status_df = _prepare_per_status_df(
        provider_status_df
    )

    status_df["_item_id"] = (
        status_df["_item_id"]
        .apply(
            _normalize_item_id
        )
    )

    status_df["_created_status"] = (
        status_df["creado"]
        .apply(
            _parse_created_status
        )
    )

    invalid_rows = status_df[
        status_df["_created_status"]
        .isna()
    ]

    if not invalid_rows.empty:
        invalid_ids = (
            invalid_rows["_item_id"]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            "Existen estados creado invalidos "
            "en el Excel PER: "
            + ", ".join(
                invalid_ids[:10]
            )
        )

    if status_df["_item_id"].duplicated().any():
        raise ValueError(
            "El Excel PER contiene _item_id "
            "duplicados para FASE 3."
        )

    work = df.copy()

    work["_item_id"] = (
        work["_item_id"]
        .apply(
            _normalize_item_id
        )
    )

    remote_ids = set(
        status_df["_item_id"]
        .astype(str)
    )

    report_ids = set(
        work["_item_id"]
        .astype(str)
    )

    missing_ids = sorted(
        report_ids - remote_ids
    )

    if missing_ids:
        raise ValueError(
            "El reporte PER contiene filas que "
            "ya no existen en el Excel remoto: "
            + ", ".join(
                missing_ids[:10]
            )
        )

    available_ids = set(
        status_df.loc[
            status_df["_created_status"] == 1,
            "_item_id",
        ].astype(str)
    )

    before = len(work)

    work = (
        work[
            work["_item_id"].isin(
                available_ids
            )
        ]
        .copy()
        .reset_index(drop=True)
    )

    return (
        work,
        {
            "filtered_out":
                before - len(work),
            "status_source_count":
                len(status_df),
            "status_created_1":
                int(
                    (
                        status_df["_created_status"]
                        == 1
                    ).sum()
                ),
            "status_not_created_1":
                int(
                    (
                        status_df["_created_status"]
                        != 1
                    ).sum()
                ),
        },
    )


def _filter_created_rows(
    df: pd.DataFrame,
    country: str,
    provider_shared_url: str | None = None,
    provider_status_df: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, dict]:
    country = str(
        country or ""
    ).strip().upper()

    if country == "SLV":
        return _filter_created_rows_slv(
            df
        )

    if country == "PER":
        return _filter_created_rows_per(
            df=df,
            provider_shared_url=provider_shared_url,
            provider_status_df=provider_status_df,
        )

    raise ValueError(
        f"Pais no soportado en FASE 3: {country}"
    )


def _find_valid_report(
    country_code: str | None = None,
) -> str:
    root = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
        )
    )

    country = str(
        country_code or "SLV"
    ).strip().upper()

    if country == "PER":
        patterns = [
            os.path.join(
                root,
                "salidas",
                "excel_proveedores_*",
                "reporte_excel_VALIDOS_*.xlsx",
            ),
        ]

    elif country == "SLV":
        patterns = [
            os.path.join(
                root,
                "salidas",
                "ejecucion_*",
                "reporte_VALIDOS_*.xlsx",
            ),
        ]

    else:
        raise ValueError(
            f"Pais no soportado en FASE 3: {country}"
        )

    files = []

    for pattern in patterns:
        files.extend(
            glob.glob(pattern)
        )

    if not files:
        raise FileNotFoundError(
            "No existen reportes VALIDOS "
            f"para {country}."
        )

    return max(
        files,
        key=os.path.getmtime,
    )


def _load_source(
    valid_report_path: str | None,
    country_code: str | None = None,
    provider_shared_url: str | None = None,
    provider_status_df: pd.DataFrame | None = None,
) -> dict:
    if not valid_report_path:
        valid_report_path = (
            _find_valid_report(
                country_code
            )
        )

    valid_report_path = os.path.abspath(
        valid_report_path
    )

    with pd.ExcelFile(
        valid_report_path
    ) as workbook:
        if (
            "DATOS_TECNICOS"
            in workbook.sheet_names
        ):
            sheet = "DATOS_TECNICOS"

        elif "VALIDOS" in workbook.sheet_names:
            sheet = "VALIDOS"

        else:
            sheet = workbook.sheet_names[0]

        df_source = pd.read_excel(
            workbook,
            sheet_name=sheet,
            dtype=str,
        )

    source_count = len(
        df_source
    )

    if "pais" not in df_source.columns:
        raise ValueError(
            "El reporte no contiene pais."
        )

    countries = (
        df_source["pais"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    countries = [
        value
        for value in countries.unique()
        if value
    ]

    if len(countries) != 1:
        raise ValueError(
            "Ambitos requiere una "
            "ejecucion por pais."
        )

    country = countries[0]

    requested_country = str(
        country_code or ""
    ).strip().upper()

    if (
        requested_country
        and requested_country != country
    ):
        raise ValueError(
            "El pais solicitado no coincide "
            "con el reporte: "
            f"{requested_country} != {country}"
        )

    df, status_info = (
        _filter_created_rows(
            df=df_source,
            country=country,
            provider_shared_url=provider_shared_url,
            provider_status_df=provider_status_df,
        )
    )

    if df.empty:
        raise ValueError(
            "No existen registros con "
            "CREADO/creado=1 para Ambitos."
        )

    return {
        "valid_report_path":
            valid_report_path,
        "df_source":
            df_source,
        "df":
            df,
        "source_count":
            source_count,
        "filtered_out":
            status_info["filtered_out"],
        "status_source_count":
            status_info["status_source_count"],
        "status_created_1":
            status_info["status_created_1"],
        "status_not_created_1":
            status_info["status_not_created_1"],
        "country":
            country,
        "run_folder":
            os.path.dirname(
                valid_report_path
            ),
    }


def _load_clients(
    country: str,
    simulate_client: dict | None = None,
) -> list[dict]:
    config_service = (
        AmbitosConfigService()
    )

    configured_client_names = (
        config_service
        .get_client_names(
            country
        )
    )

    db = DbValidationService(country_code=country)

    clients = db.get_persons_by_names(
        configured_client_names
    )

    if simulate_client:
        clients = clients.copy()

        clients.append({
            "client_id":
                simulate_client.get(
                    "client_id",
                    "SIMULATED",
                ),
            "name":
                simulate_client.get(
                    "name"
                ),
            "document_number":
                simulate_client.get(
                    "document_number"
                ),
        })

    return clients


def _build_result(
    df: pd.DataFrame,
    clients: list[dict],
    country: str,
) -> dict:
    builder = AmbitosBuilderService()

    result = (
        builder.build_from_dataframe(
            df=df,
            db_clients=clients,
        )
    )

    assignment = (
        AmbitosAssignmentService()
    )

    result = assignment.enrich(
        result=result,
        country=country,
    )

    _stringify_identifiers(
        result
    )

    return result


def _stringify_identifiers(
    result: dict,
):
    for collection, fields in [
        (
            result.get(
                "entidades",
                [],
            ),
            ["RUC"],
        ),
        (
            result.get(
                "relacion_nueva",
                [],
            ),
            ["RUC"],
        ),
        (
            result.get(
                "ambitos",
                [],
            ),
            ["Empresa"],
        ),
    ]:
        for row in collection:
            for field in fields:
                if field in row:
                    row[field] = str(
                        row[field]
                        or ""
                    )


def _write_diagnostics(
    output_path: str,
    result: dict,
    extra_sheets: dict | None = None,
):
    extra_sheets = (
        extra_sheets or {}
    )

    with pd.ExcelWriter(
        output_path,
        engine="openpyxl",
    ) as writer:
        pd.DataFrame(
            result.get(
                "matched_relations",
                [],
            )
        ).to_excel(
            writer,
            sheet_name="MATCHED",
            index=False,
        )

        pd.DataFrame(
            result.get(
                "no_match",
                [],
            )
        ).to_excel(
            writer,
            sheet_name="NO_MATCH",
            index=False,
        )

        pd.DataFrame(
            result.get(
                "tipo_negocio_nuevo",
                [],
            )
        ).to_excel(
            writer,
            sheet_name="NEGOCIOS",
            index=False,
        )

        pd.DataFrame(
            result.get(
                "sede_nueva",
                [],
            )
        ).to_excel(
            writer,
            sheet_name="SEDES",
            index=False,
        )

        for sheet_name, rows in (
            extra_sheets.items()
        ):
            pd.DataFrame(
                rows
            ).to_excel(
                writer,
                sheet_name=sheet_name[
                    :31
                ],
                index=False,
            )


def run_phase3_preview(
    valid_report_path: str | None = None,
    simulate_client: dict | None = None,
    country_code: str | None = None,
    provider_shared_url: str | None = None,
    provider_status_df: pd.DataFrame | None = None,
) -> dict:
    source = _load_source(
        valid_report_path=valid_report_path,
        country_code=country_code,
        provider_shared_url=provider_shared_url,
        provider_status_df=provider_status_df,
    )

    country = source["country"]

    clients = _load_clients(
        country=country,
        simulate_client=simulate_client,
    )

    result = _build_result(
        df=source["df"],
        clients=clients,
        country=country,
    )

    run_folder = source[
        "run_folder"
    ]

    excel_service = (
        AmbitosExcelService(
            output_dir=run_folder
        )
    )

    template_path = os.path.join(
        run_folder,
        "plantilla_ambitos_PREVIEW.xlsx",
    )

    excel_service.export_template_ambitos(
        data=result,
        output_path=template_path,
    )

    diagnostics_path = os.path.join(
        run_folder,
        "fase3_diagnostico.xlsx",
    )

    _write_diagnostics(
        output_path=diagnostics_path,
        result=result,
    )

    no_match_rows = result.get(
        "no_match",
        [],
    )

    review_path = os.path.join(
        run_folder,
        "revision_clientes_ambitos.xlsx",
    )

    if no_match_rows:
        review_service = (
            AmbitosReviewService()
        )

        review_path = (
            review_service.export(
                no_match=no_match_rows,
                output_path=review_path,
                country_code=country,
            )
        )

    else:
        if os.path.exists(
            review_path
        ):
            os.remove(
                review_path
            )

        review_path = None

    return {
        "country":
            country,
        "usuarios_fuente":
            source["source_count"],
        "usuarios":
            len(source["df"]),
        "filtrados_creado":
            source["filtered_out"],
        "estado_fuente":
            source["status_source_count"],
        "estado_creado_1":
            source["status_created_1"],
        "estado_no_creado_1":
            source["status_not_created_1"],
        "clientes_bd":
            len(clients),
        "matched":
            len(
                result.get(
                    "matched_relations",
                    [],
                )
            ),
        "no_match":
            len(
                no_match_rows
            ),
        "entidades":
            len(
                result.get(
                    "entidades",
                    [],
                )
            ),
        "relacion_nueva":
            len(
                result.get(
                    "relacion_nueva",
                    [],
                )
            ),
        "ambitos":
            len(
                result.get(
                    "ambitos",
                    [],
                )
            ),
        "template_path":
            os.path.abspath(
                template_path
            ),
        "diagnostics_path":
            os.path.abspath(
                diagnostics_path
            ),
        "review_path":
            review_path,
    }


def run_phase3_final(
    valid_report_path: str | None = None,
    review_path: str | None = None,
    country_code: str | None = None,
    provider_shared_url: str | None = None,
    provider_status_df: pd.DataFrame | None = None,
) -> dict:
    source = _load_source(
        valid_report_path=valid_report_path,
        country_code=country_code,
        provider_shared_url=provider_shared_url,
        provider_status_df=provider_status_df,
    )

    country = source["country"]
    df = source["df"].copy()

    clients = _load_clients(
        country=country
    )

    automatic_result = _build_result(
        df=df,
        clients=clients,
        country=country,
    )

    automatic_no_match = (
        automatic_result.get(
            "no_match",
            [],
        )
    )

    automatic_pending = {
        _normalize_item_id(
            row.get("_item_id")
        ): row
        for row in automatic_no_match
        if _normalize_item_id(
            row.get("_item_id")
        )
    }

    run_folder = source[
        "run_folder"
    ]

    if review_path is None:
        review_path = os.path.join(
            run_folder,
            "revision_clientes_ambitos.xlsx",
        )

    review_result = {
        "resolved": [],
        "pending": [],
        "invalid": [],
        "rows": [],
    }

    review_service = (
        AmbitosReviewService()
    )

    if automatic_pending:
        if not os.path.exists(
            review_path
        ):
            raise FileNotFoundError(
                "Existen clientes pendientes. "
                "Primero ejecute Preparar Ambitos "
                "para generar "
                "revision_clientes_ambitos.xlsx."
            )

        review_result = (
            review_service.read_assignments(
                review_path=review_path,
                country_code=country,
            )
        )

        if review_result["invalid"]:
            details = "; ".join(
                (
                    f"ITEM "
                    f"{row.get('_item_id')}: "
                    f"{row.get('error')}"
                )
                for row in (
                    review_result[
                        "invalid"
                    ]
                )
            )

            raise ValueError(
                "Hay asignaciones manuales "
                "invalidas: "
                + details
            )

    current_ids = {
        _normalize_item_id(
            value
        )
        for value in df[
            "_item_id"
        ].tolist()
    }

    resolved_by_id = {}

    for row in review_result[
        "resolved"
    ]:
        item_id = _normalize_item_id(
            row.get("_item_id")
        )

        if (
            item_id
            and item_id
            in automatic_pending
            and item_id
            in current_ids
        ):
            resolved_by_id[
                item_id
            ] = row[
                "cliente_canonico"
            ]

    pending_ids = (
        set(
            automatic_pending
        )
        - set(
            resolved_by_id
        )
    )

    work = df.copy()

    work["_item_id"] = (
        work["_item_id"]
        .apply(
            _normalize_item_id
        )
    )

    if "nombre_cliente" not in (
        work.columns
    ):
        work[
            "nombre_cliente"
        ] = ""

    for item_id, client_name in (
        resolved_by_id.items()
    ):
        mask = (
            work["_item_id"]
            == item_id
        )

        work.loc[
            mask,
            "nombre_cliente",
        ] = client_name

    if pending_ids:
        work = (
            work[
                ~work["_item_id"].isin(
                    pending_ids
                )
            ]
            .copy()
            .reset_index(drop=True)
        )

    candidate_result = _build_result(
        df=work,
        clients=clients,
        country=country,
    )

    technical_no_match = (
        candidate_result.get(
            "no_match",
            [],
        )
    )

    technical_pending_ids = {
        _normalize_item_id(
            row.get("_item_id")
        )
        for row in technical_no_match
        if _normalize_item_id(
            row.get("_item_id")
        )
    }

    if technical_pending_ids:
        safe_work = (
            work[
                ~work["_item_id"].isin(
                    technical_pending_ids
                )
            ]
            .copy()
            .reset_index(drop=True)
        )

        if safe_work.empty:
            raise ValueError(
                "No existen relaciones seguras "
                "para generar la plantilla final."
            )

        final_result = _build_result(
            df=safe_work,
            clients=clients,
            country=country,
        )

    else:
        safe_work = work
        final_result = (
            candidate_result
        )

    if final_result.get(
        "no_match",
        [],
    ):
        raise RuntimeError(
            "La plantilla final todavia "
            "contiene relaciones no resueltas."
        )

    excel_service = (
        AmbitosExcelService(
            output_dir=run_folder
        )
    )

    template_path = os.path.join(
        run_folder,
        "plantilla_ambitos_FINAL.xlsx",
    )

    excel_service.export_template_ambitos(
        data=final_result,
        output_path=template_path,
    )

    pending_client_rows = [
        {
            **automatic_pending[
                item_id
            ],
            "estado":
                "PENDIENTE_CLIENTE",
        }
        for item_id in sorted(
            pending_ids
        )
    ]

    technical_pending_rows = [
        {
            **row,
            "estado":
                "PENDIENTE_TECNICO",
        }
        for row in technical_no_match
    ]

    manual_rows = [
        {
            "_item_id":
                item_id,
            "cliente_canonico":
                client_name,
            "estado":
                "MANUAL_VALIDADO",
        }
        for item_id, client_name in (
            sorted(
                resolved_by_id.items()
            )
        )
    ]

    diagnostics_path = os.path.join(
        run_folder,
        "fase3_final_diagnostico.xlsx",
    )

    _write_diagnostics(
        output_path=diagnostics_path,
        result=final_result,
        extra_sheets={
            "MANUALES":
                manual_rows,
            "PEND_CLIENTE":
                pending_client_rows,
            "PEND_TECNICO":
                technical_pending_rows,
        },
    )

    incorporated_manual_ids = {
        _normalize_item_id(
            row.get("_item_id")
        )
        for row in final_result.get(
            "matched_relations",
            [],
        )
        if _normalize_item_id(
            row.get("_item_id")
        )
        in resolved_by_id
    }

    final_pending_ids = (
        pending_ids
        | technical_pending_ids
    )

    return {
        "country":
            country,
        "registros_fuente":
            source["source_count"],
        "creado_1":
            len(df),
        "filtrados_creado":
            source["filtered_out"],
        "estado_fuente":
            source["status_source_count"],
        "estado_creado_1":
            source["status_created_1"],
        "estado_no_creado_1":
            source["status_not_created_1"],
        "automaticos":
            (
                len(df)
                - len(
                    automatic_pending
                )
            ),
        "revision_total":
            len(
                automatic_pending
            ),
        "manuales_asignados":
            len(
                resolved_by_id
            ),
        "manuales_incorporados":
            len(
                incorporated_manual_ids
            ),
        "pendientes_cliente":
            len(
                pending_ids
            ),
        "pendientes_tecnicos":
            len(
                technical_pending_ids
            ),
        "pendientes_total":
            len(
                final_pending_ids
            ),
        "registros_finales":
            len(
                safe_work
            ),
        "matched_final":
            len(
                final_result.get(
                    "matched_relations",
                    [],
                )
            ),
        "entidades":
            len(
                final_result.get(
                    "entidades",
                    [],
                )
            ),
        "relacion_nueva":
            len(
                final_result.get(
                    "relacion_nueva",
                    [],
                )
            ),
        "ambitos":
            len(
                final_result.get(
                    "ambitos",
                    [],
                )
            ),
        "template_path":
            os.path.abspath(
                template_path
            ),
        "diagnostics_path":
            os.path.abspath(
                diagnostics_path
            ),
        "review_path":
            (
                os.path.abspath(
                    review_path
                )
                if os.path.exists(
                    review_path
                )
                else None
            ),
    }
