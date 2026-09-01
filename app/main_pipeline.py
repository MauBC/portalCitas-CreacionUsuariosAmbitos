import os
import json
from datetime import datetime

from app.services.sharepoint_service import SharePointService
from app.services.country_cleaning_service import CountryCleaningService
from app.services.country_mapping_service import CountryMappingService
from app.services.excel_service import ExcelService
from app.services.user_creation_manifest_service import UserCreationManifestService
from app.services.db_validation_service import DbValidationService
from app.services.client_validation_service import ClientValidationService
from app.config.settings import settings
from app.services.gemini_client_parser_service import GeminiClientParserService
from app.services.control_sheet_service import ControlSheetService
# crear carpeta base si no existe
def _get_base_output_dir():
    project_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

    base_dir = os.path.join(
        project_root,
        "salidas"
    )

    os.makedirs(base_dir, exist_ok=True)
    return base_dir


# crear carpeta unica por ejecucion
def _create_run_folder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = os.path.join(_get_base_output_dir(), f"ejecucion_{timestamp}")
    os.makedirs(run_folder, exist_ok=True)
    return run_folder


# marcar como error si el correo ya existe en bd
def _apply_email_database_validation(df, db_validator):
    df = df.copy()

    if "email" not in df.columns:
        return df, 0

    mask_ok = df["estado"] == "OK"
    df_ok = df[mask_ok].copy()

    if df_ok.empty:
        return df, 0

    emails = (
        df_ok["email"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.lower()
        .tolist()
    )

    existing_emails = db_validator.get_existing_emails(emails)

    if not existing_emails:
        return df, 0

    normalized_email_series = (
        df["email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    duplicate_mask = mask_ok & normalized_email_series.isin(existing_emails)

    df.loc[duplicate_mask, "observaciones"] = "CORREO YA EXISTE EN BD"
    df.loc[duplicate_mask, "estado"] = "ERROR"

    return df, int(duplicate_mask.sum())

def _run_gemini_client_normalization(df_validos, run_folder):
    service = GeminiClientParserService()

    items = []
    original_rows = []

    for _, row in df_validos.iterrows():
        if str(row.get("perfil", "")).upper() != "PROVEEDOR":
            continue

        input_clientes = str(row.get("nombre_cliente") or "").strip()

        if not input_clientes:
            continue

        items.append({
            "input_clientes": input_clientes
        })

        original_rows.append({
            "proveedor_nombre": row.get("nombre_proveedor"),
            "proveedor_ruc": row.get("ruc_proveedor"),
            "input_clientes": input_clientes
        })

    if not items:
        return None

    result = service.parse_providers_clients(
        providers=items,
        batch_size=20,
        output_dir=run_folder
    )

    # recombinar
    final_results = []

    for i, item in enumerate(result["resultados"]):
        original = original_rows[i]

        final_results.append({
            "proveedor_nombre": original["proveedor_nombre"],
            "proveedor_ruc": original["proveedor_ruc"],
            "proveedor_email": original["proveedor_email"],

            "input_clientes": original["input_clientes"],
            "clientes_detectados": item.get("clientes_detectados", [])
        })

    # guardar archivo final limpio
    output_path = os.path.join(run_folder, "gemini_clientes_final.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)

    return output_path

def run_pipeline():
    # carpeta de salida por ejecucion
    run_folder = _create_run_folder()

    sp = SharePointService()
    mapper = CountryMappingService()
    cleaner = CountryCleaningService()
    excel_service = ExcelService(output_dir=run_folder)
    manifest_service = UserCreationManifestService()
    db_validator = DbValidationService()
    client_validator = ClientValidationService()

    # cargar datos desde sharepoint
    df = sp.load_form_responses_as_dataframe()

    if df.empty:
        return {
            "ok": False,
            "message": "No se encontraron registros en SharePoint.",
            "run_folder": run_folder,
        }

    # mapear columnas segun pais
    df_mapped = mapper.map(df)

    # limpiar y validar segun pais
    df_clean = cleaner.clean(df_mapped)

    # Validacion y normalizacion del cliente.
    # SLV actualmente admite:
    # - DOCTOR SV
    # - CALLEJA S.A
    #
    # Los casos ambiguos/no reconocidos pasan a ERROR
    # para revision manual.
    df_clean = client_validator.validate_dataframe(df_clean)

    client_review_count = int(
        df_clean["requiere_revision_cliente"]
        .fillna(False)
        .astype(bool)
        .sum()
    )

    # validacion extra contra bd
    duplicate_email_count = 0

    if settings.VALIDATE_EMAIL_EXISTS_IN_DB:
        df_clean, duplicate_email_count = _apply_email_database_validation(df_clean, db_validator)
    
    # exportar excels
    excel_paths = excel_service.export_validos_errores(df_clean, base_name="reporte")

    # template solo con ok final
    df_validos = df_clean[df_clean["estado"] == "OK"].copy()

    template_path = None
    manifest_path = None

    if not df_validos.empty:
        template_path = excel_service.export_template(df_validos)

        # Agregar hoja de control al mismo Excel.
        # Esta hoja NO forma parte de la carga del portal;
        # sirve solamente para revision operativa.
        control_service = ControlSheetService()

        control_service.add_to_template(
            template_path=template_path,
            valid_path=excel_paths["validos"],
            error_path=excel_paths["errores"],
        )

        manifest_path = manifest_service.save(
            df_validos=df_validos,
            output_dir=run_folder
        )
    
    # Gemini queda temporalmente fuera del pipeline.
    #
    # La limpieza actual se realiza mediante:
    # CountryMappingService -> CountryCleaningService
    #
    # El codigo de Gemini se conserva para una futura
    # normalizacion inteligente de clientes/proveedores.
    gemini_output_path = None

    
    
    # FASE 1:
    # Todavia no se actualiza CREADO.
    # CREADO se actualizara despues de procesar
    # el Excel de respuesta del portal.
    updated_count = 0
    failed_updates = []

    # guardar log de ejecucion
    log_content = (
        f"Fecha: {datetime.now()}\n"
        f"Total: {len(df_clean)}\n"
        f"Validos finales: {(df_clean['estado'] == 'OK').sum()}\n"
        f"Errores finales: {(df_clean['estado'] == 'ERROR').sum()}\n"
        f"Correos ya existentes en BD: {duplicate_email_count}\n"
        f"SharePoint actualizados: {updated_count}\n"
        f"SharePoint fallidos: {len(failed_updates)}\n"
    )

    log_path = os.path.join(run_folder, "proceso_log.txt")
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(log_content)

    # resultado final
    return {
        "ok": True,
        "message": "Proceso completado correctamente.",
        "total": len(df_clean),
        "validos": int((df_clean["estado"] == "OK").sum()),
        "errores": int((df_clean["estado"] == "ERROR").sum()),
        "correos_existentes_bd": duplicate_email_count,
        "clientes_revision": client_review_count,
        "path_validos": excel_paths["validos"],
        "path_errores": excel_paths["errores"],
        "path_template": template_path,
        "path_manifest": manifest_path,
        "sharepoint_updated": updated_count,
        "sharepoint_failed": failed_updates,
        "run_folder": run_folder,
        "log_path": log_path,
        "gemini_output": gemini_output_path,
    }










