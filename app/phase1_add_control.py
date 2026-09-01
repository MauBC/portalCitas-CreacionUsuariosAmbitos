from pathlib import Path

from app.services.control_sheet_service import (
    ControlSheetService,
)


ROOT = Path(
    __file__
).resolve().parent.parent

OUTPUT = ROOT / "salidas"


def latest_run():

    folders = sorted(
        OUTPUT.glob("ejecucion_*"),
        key=lambda x: x.stat().st_mtime,
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

        template = list(
            folder.glob(
                "plantilla_usuarios_*.xlsx"
            )
        )

        if valid and errors and template:

            return (
                folder,
                max(
                    valid,
                    key=lambda x: x.stat().st_mtime,
                ),
                max(
                    errors,
                    key=lambda x: x.stat().st_mtime,
                ),
                max(
                    template,
                    key=lambda x: x.stat().st_mtime,
                ),
            )

    raise FileNotFoundError(
        "No se encontro una FASE 1 completa"
    )


folder, valid, errors, template = latest_run()

print("=" * 100)
print("AGREGANDO HOJA CONTROL")
print("=" * 100)

print("Ejecucion :", folder)
print("Plantilla :", template)

service = ControlSheetService()

control = service.add_to_template(
    template_path=template,
    valid_path=valid,
    error_path=errors,
)

print()
print("TOTAL:", len(control))

print()
print(
    control["ESTADO"]
    .value_counts()
    .to_string()
)

print()
print(
    "REGISTROS CON ATENCION:"
)

attention = control[
    control["ESTADO"]
    != "LISTO_PARA_CARGA"
]

print(
    attention[
        [
            "ITEM_ID",
            "EMAIL",
            "CLIENTE_ORIGINAL",
            "CLIENTE_NORMALIZADO",
            "ESTADO",
            "OBSERVACION",
        ]
    ].to_string(
        index=False
    )
)

print()
print(
    "[OK] Hoja CONTROL agregada"
)
