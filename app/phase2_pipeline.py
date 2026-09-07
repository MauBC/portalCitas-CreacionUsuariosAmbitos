import os

from app.services.user_creation_phase2_service import (
    UserCreationPhase2Service
)

from app.services.sharepoint_creation_status_service import (
    SharePointCreationStatusService
)


def run_phase2(
    run_folder: str,
    portal_error_excel: str,
    dry_run: bool = True,
) -> dict:

    if not os.path.isdir(run_folder):
        raise FileNotFoundError(
            f"No existe carpeta de ejecucion: {run_folder}"
        )

    if not os.path.isfile(portal_error_excel):
        raise FileNotFoundError(
            f"No existe Excel del portal: {portal_error_excel}"
        )

    phase2 = UserCreationPhase2Service()

    results = phase2.preview(
        run_folder=run_folder,
        portal_error_excel=portal_error_excel,
    )

    # Guardar siempre evidencia del resultado calculado
    result_path = os.path.join(
        run_folder,
        "resultado_creacion_usuarios.xlsx"
    )

    results.to_excel(
        result_path,
        index=False
    )

    sharepoint = SharePointCreationStatusService()

    update_result = sharepoint.apply(
        results=results,
        dry_run=dry_run,
    )

    return {
        "ok": len(update_result["failed"]) == 0,
        "dry_run": dry_run,
        "total": len(results),
        "creados": int((results["creado"] == 1).sum()),
        "errores": int((results["creado"] == 2).sum()),
        "updated": update_result["updated"],
        "skipped": update_result["skipped"],
        "failed": update_result["failed"],
        "preview": update_result["preview"],
        "result_path": os.path.abspath(result_path),
    }
