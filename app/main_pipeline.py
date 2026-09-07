from datetime import datetime

from app.config.paths import create_run_folder
from app.config.settings import settings
from app.services.country_cleaning_service import CountryCleaningService
from app.services.country_mapping_service import CountryMappingService
from app.services.email_validation_service import EmailValidationService
from app.services.excel_service import ExcelService
from app.services.sharepoint_service import SharePointService
from app.services.user_creation_manifest_service import (
    UserCreationManifestService,
)


def run_pipeline() -> dict:
    run_folder = create_run_folder("ejecucion")

    source = SharePointService().load_form_responses_as_dataframe()

    if source.empty:
        return {
            "ok": False,
            "message": "No se encontraron registros en SharePoint.",
            "run_folder": str(run_folder),
        }

    mapped = CountryMappingService().map(source)
    cleaned = CountryCleaningService().clean(mapped)

    existing_email_count = 0

    if settings.VALIDATE_EMAIL_EXISTS_IN_DB:
        cleaned, existing_email_count = (
            EmailValidationService(country_code="SLV").validate_existing_emails(cleaned)
        )

    excel = ExcelService(output_dir=str(run_folder))
    report_paths = excel.export_validos_errores(
        cleaned,
        base_name="reporte",
    )

    valid_users = cleaned[
        cleaned["estado"].eq("OK")
    ].copy()

    template_path = None
    manifest_path = None

    if not valid_users.empty:
        template_path = excel.export_template(valid_users)
        manifest_path = UserCreationManifestService().save(
            df_validos=valid_users,
            output_dir=str(run_folder),
        )

    valid_count = int(cleaned["estado"].eq("OK").sum())
    error_count = int(cleaned["estado"].eq("ERROR").sum())

    log_path = run_folder / "proceso_log.txt"
    log_path.write_text(
        (
            f"Fecha: {datetime.now()}\n"
            f"Total: {len(cleaned)}\n"
            f"Validos finales: {valid_count}\n"
            f"Errores finales: {error_count}\n"
            f"Correos ya existentes en BD: {existing_email_count}\n"
            "SharePoint actualizados: 0\n"
            "SharePoint fallidos: 0\n"
        ),
        encoding="utf-8",
    )

    return {
        "ok": True,
        "message": "Proceso completado correctamente.",
        "total": len(cleaned),
        "validos": valid_count,
        "errores": error_count,
        "correos_existentes_bd": existing_email_count,
        "clientes_revision": 0,
        "path_validos": report_paths["validos"],
        "path_errores": report_paths["errores"],
        "path_template": template_path,
        "path_manifest": manifest_path,
        "sharepoint_updated": 0,
        "sharepoint_failed": [],
        "run_folder": str(run_folder),
        "log_path": str(log_path),
    }
