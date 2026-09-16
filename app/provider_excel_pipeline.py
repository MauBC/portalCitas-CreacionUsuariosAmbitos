import argparse
from pathlib import Path

import pandas as pd

from app.config.paths import create_run_folder
from app.config.settings import settings
from app.services.country_cleaning_service import (
    CountryCleaningService,
)
from app.services.email_validation_service import (
    EmailValidationService,
)
from app.services.excel_service import (
    ExcelService,
)
from app.services.provider_creation_status_service import (
    ProviderCreationStatusService,
)
from app.services.provider_excel_mapping_service import (
    ProviderExcelMappingService,
)
from app.services.provider_excel_source_service import (
    ProviderExcelSourceService,
)
from app.services.user_creation_manifest_service import (
    UserCreationManifestService,
)
from app.services.provider_client_validation_service import ProviderClientValidationService


SUPPORTED_COUNTRIES = {
    "PER",
    "SLV",
}

SUPPORTED_SOURCES = {
    "local",
    "sharepoint",
}


def _mark_email_identity_conflicts(
    df,
):
    result = df.copy()

    if "advertencias" not in result.columns:
        result["advertencias"] = ""

    result["_orden_origen"] = range(
        1,
        len(result) + 1,
    )

    result["correo_repetido"] = False
    result["usuario_principal"] = False
    result["seleccion_usuario"] = ""

    if (
        "email" not in result.columns
        or "estado" not in result.columns
    ):
        return result

    result["_email_key"] = (
        result["email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    def append_warning(
        value,
        message,
    ):
        current = (
            ""
            if value is None
            else str(value).strip()
        )

        if current.lower() == "nan":
            current = ""

        if not current:
            return message

        parts = [
            part.strip()
            for part in current.split("|")
            if part.strip()
        ]

        if message not in parts:
            parts.append(message)

        return " | ".join(parts)

    work = result[
        result["_email_key"].ne("")
    ]

    for _, group in work.groupby(
        "_email_key",
        sort=False,
    ):
        is_duplicate = len(group) > 1

        if is_duplicate:
            result.loc[
                group.index,
                "correo_repetido",
            ] = True

        valid_group = group[
            group["estado"].eq("OK")
        ].sort_values(
            "_orden_origen",
            kind="stable",
        )

        if valid_group.empty:
            if is_duplicate:
                result.loc[
                    group.index,
                    "seleccion_usuario",
                ] = "SIN_REGISTRO_VALIDO"

            continue

        primary_index = valid_group.index[0]

        result.loc[
            primary_index,
            "usuario_principal",
        ] = True

        result.loc[
            primary_index,
            "seleccion_usuario",
        ] = (
            "PRIMER_REGISTRO_VALIDO"
            if is_duplicate
            else "UNICO"
        )

        if not is_duplicate:
            continue

        warning_primary = (
            "CORREO REPETIDO: "
            "CUENTA USA PRIMER REGISTRO VALIDO"
        )

        result.loc[
            primary_index,
            "advertencias",
        ] = append_warning(
            result.loc[
                primary_index,
                "advertencias",
            ],
            warning_primary,
        )

        other_valid_indexes = (
            valid_group.index[
                valid_group.index
                != primary_index
            ]
        )

        if len(other_valid_indexes):
            result.loc[
                other_valid_indexes,
                "seleccion_usuario",
            ] = "RELACION_ADICIONAL"

            for index in other_valid_indexes:
                result.loc[
                    index,
                    "advertencias",
                ] = append_warning(
                    result.loc[
                        index,
                        "advertencias",
                    ],
                    (
                        "CORREO REPETIDO: "
                        "RELACION ADICIONAL; "
                        "CUENTA USA PRIMER "
                        "REGISTRO VALIDO"
                    ),
                )

        invalid_indexes = (
            group.index[
                ~group.index.isin(
                    valid_group.index
                )
            ]
        )

        if len(invalid_indexes):
            result.loc[
                invalid_indexes,
                "seleccion_usuario",
            ] = "NO_USADO_CUENTA_POR_ERROR"

    return result.drop(
        columns=["_email_key"]
    )


def _build_unique_users(
    df,
):
    valid = df[
        df["estado"].eq("OK")
    ].copy()

    if valid.empty:
        return valid

    valid["_email_key"] = (
        valid["email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    valid = valid[
        valid["_email_key"].ne("")
    ].copy()

    if valid.empty:
        return valid.drop(
            columns=["_email_key"]
        )

    if "_orden_origen" not in valid.columns:
        valid["_orden_origen"] = range(
            1,
            len(valid) + 1,
        )

    valid = (
        valid.sort_values(
            "_orden_origen",
            kind="stable",
        )
        .drop_duplicates(
            subset=["_email_key"],
            keep="first",
        )
        .drop(
            columns=["_email_key"]
        )
        .reset_index(
            drop=True
        )
    )

    return valid


def _load_source(
    source_service:
        ProviderExcelSourceService,
    source_type: str,
    file_path: str | None,
    shared_url: str | None,
) -> pd.DataFrame:
    if source_type == "local":
        if not file_path:
            raise ValueError(
                "file_path es obligatorio "
                "para source_type='local'."
            )

        return source_service.load_local(
            file_path
        )

    if source_type == "sharepoint":
        if not shared_url:
            raise ValueError(
                "shared_url es obligatorio "
                "para source_type='sharepoint'."
            )

        return (
            source_service
            .load_sharepoint(
                shared_url
            )
        )

    raise ValueError(
        "source_type debe ser "
        "'local' o 'sharepoint'."
    )


def run_provider_excel(
    country_code: str,
    source_type: str,
    file_path: str | None = None,
    shared_url: str | None = None,
    validate_existing_emails:
        bool | None = None,
    email_validation_service:
        EmailValidationService | None = None,
    output_root:
        str | Path | None = None,
) -> dict:
    country = str(
        country_code or ""
    ).strip().upper()

    source = str(
        source_type or ""
    ).strip().lower()

    if country not in SUPPORTED_COUNTRIES:
        raise ValueError(
            "country_code debe ser "
            "'PER' o 'SLV'."
        )

    if source not in SUPPORTED_SOURCES:
        raise ValueError(
            "source_type debe ser "
            "'local' o 'sharepoint'."
        )

    raw = _load_source(
        source_service=
            ProviderExcelSourceService(),
        source_type=source,
        file_path=file_path,
        shared_url=shared_url,
    )

    mapped = (
        ProviderExcelMappingService()
        .map(
            df=raw,
            country_code=country,
        )
    )

    cleaned = (
        CountryCleaningService()
        .clean(
            mapped
        )
    )

    cleaned = (
        ProviderClientValidationService()
        .apply(
            cleaned,
            country_code=country,
        )
    )

    creation_status = (
        ProviderCreationStatusService()
    )

    cleaned = (
        creation_status
        .apply_source_status(
            cleaned
        )
    )

    cleaned = (
        _mark_email_identity_conflicts(
            cleaned
        )
    )

    should_validate_db = (
        settings.VALIDATE_EMAIL_EXISTS_IN_DB
        if validate_existing_emails
        is None
        else bool(
            validate_existing_emails
        )
    )

    existing_email_count = 0

    if should_validate_db:
        validator = (
            email_validation_service
            or EmailValidationService(
                country_code=country
            )
        )

        (
            cleaned,
            existing_email_count,
        ) = (
            validator
            .validate_existing_emails(
                cleaned
            )
        )

    cleaned = (
        creation_status
        .finalize(
            cleaned
        )
    )

    status_summary = (
        creation_status
        .summarize(
            cleaned
        )
    )

    unique_users = (
        _build_unique_users(
            cleaned
        )
    )

    run_folder = (
        create_run_folder(
            "excel_proveedores",
            output_root=output_root,
        )
    )

    excel = ExcelService(
        output_dir=str(
            run_folder
        )
    )

    reports = (
        excel
        .export_validos_errores(
            cleaned,
            base_name=
                "reporte_excel",
        )
    )

    normalized_path = (
        run_folder
        / "excel_proveedores_normalizado.xlsx"
    )

    cleaned.to_excel(
        normalized_path,
        index=False,
    )

    template_path = None
    manifest_path = None

    if not unique_users.empty:
        template_path = (
            excel.export_template(
                unique_users
            )
        )

        manifest_path = (
            UserCreationManifestService()
            .save(
                df_validos=
                    unique_users,
                output_dir=
                    str(run_folder),
            )
        )

    return {
        "ok":
            True,
        "country":
            country,
        "source_type":
            source,
        "total":
            len(cleaned),
        "valid_relations":
            int(
                cleaned[
                    "estado"
                ].eq("OK").sum()
            ),
        "errors":
            int(
                cleaned[
                    "estado"
                ].eq("ERROR").sum()
            ),
        "skipped":
            int(
                cleaned[
                    "estado"
                ].eq("OMITIDO").sum()
            ),
        "already_created":
            status_summary[
                "already_created"
            ],
        "previous_errors":
            status_summary[
                "previous_errors"
            ],
        "invalid_creation_status":
            status_summary[
                "invalid_status"
            ],
        "validation_errors":
            status_summary[
                "validation_errors"
            ],
        "warnings":
            (
                int(
                    cleaned[
                        "advertencias"
                    ]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .ne("")
                    .sum()
                )
                if (
                    "advertencias"
                    in cleaned.columns
                )
                else 0
            ),
        "unique_users":
            len(
                unique_users
            ),
        "existing_emails_db":
            existing_email_count,
        "run_folder":
            str(run_folder),
        "normalized_path":
            str(normalized_path),
        "valid_path":
            reports["validos"],
        "error_path":
            reports["errores"],
        "template_path":
            template_path,
        "manifest_path":
            manifest_path,
    }


def _print_result(
    result: dict,
) -> None:
    print(
        "=" * 100
    )
    print(
        "IMPORTADOR EXCEL "
        "DE PROVEEDORES"
    )
    print(
        "=" * 100
    )
    print(
        f"Pais              : "
        f"{result['country']}"
    )
    print(
        f"Fuente            : "
        f"{result['source_type']}"
    )
    print(
        f"Filas origen      : "
        f"{result['total']}"
    )
    print(
        f"Relaciones validas: "
        f"{result['valid_relations']}"
    )
    print(
        f"Errores nuevos    : "
        f"{result['errors']}"
    )
    print(
        f"Ya creados        : "
        f"{result['already_created']}"
    )
    print(
        f"Errores previos   : "
        f"{result['previous_errors']}"
    )
    print(
        f"Omitidos          : "
        f"{result['skipped']}"
    )
    print(
        f"Advertencias      : "
        f"{result['warnings']}"
    )
    print(
        f"Usuarios unicos   : "
        f"{result['unique_users']}"
    )
    print(
        f"Correos en BD     : "
        f"{result['existing_emails_db']}"
    )
    print()
    print(
        "Carpeta:"
    )
    print(
        result[
            "run_folder"
        ]
    )
    print()
    print(
        "Normalizado:"
    )
    print(
        result[
            "normalized_path"
        ]
    )
    print()
    print(
        "VALIDOS:"
    )
    print(
        result[
            "valid_path"
        ]
    )
    print()
    print(
        "ERRORES:"
    )
    print(
        result[
            "error_path"
        ]
    )
    print()
    print(
        "Plantilla usuarios:"
    )
    print(
        result[
            "template_path"
        ]
        or "No generada"
    )
    print(
        "=" * 100
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = (
        argparse.ArgumentParser(
            description=(
                "Importar Excel "
                "de proveedores desde "
                "archivo local o SharePoint."
            )
        )
    )

    parser.add_argument(
        "--country",
        required=True,
        choices=sorted(
            SUPPORTED_COUNTRIES
        ),
    )

    parser.add_argument(
        "--source",
        required=True,
        choices=sorted(
            SUPPORTED_SOURCES
        ),
    )

    parser.add_argument(
        "--file",
        default=None,
    )

    parser.add_argument(
        "--url",
        default=None,
    )

    parser.add_argument(
        "--skip-db-validation",
        action="store_true",
    )

    return parser


if __name__ == "__main__":
    parser = _build_parser()
    args = parser.parse_args()

    result = run_provider_excel(
        country_code=
            args.country,
        source_type=
            args.source,
        file_path=
            args.file,
        shared_url=
            args.url,
        validate_existing_emails=(
            False
            if args.skip_db_validation
            else None
        ),
    )

    _print_result(
        result
    )

