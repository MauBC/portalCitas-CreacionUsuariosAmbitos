import glob
import os

import pandas as pd
from openpyxl import load_workbook

from app.services.ambitos_builder_service import (
    AmbitosBuilderService
)

from app.services.ambitos_assignment_service import (
    AmbitosAssignmentService
)

from app.services.ambitos_excel_service import (
    AmbitosExcelService
)

from app.services.ambitos_config_service import AmbitosConfigService

from app.services.db_validation_service import (
    DbValidationService
)




def _rewrite_dynamic_catalogs(
    template_path: str,
    result: dict,
):
    """
    Reemplaza los datos estaticos antiguos de las hojas:

        TipoNegocioNuevo
        SedeNueva

    por los valores calculados desde ambitos_config.json.

    Esto evita que configuraciones antiguas de Peru como:
        RSA
        RAA
        Ransa Lurin
        Centros de Distribucion
        Fresh & Cold

    aparezcan accidentalmente en una carga de El Salvador.
    """

    workbook = load_workbook(
        template_path
    )

    configurations = [
        (
            "TipoNegocioNuevo",
            [
                "Grupo",
                "Tipo de negocio",
                "Rubro",
            ],
            result.get(
                "tipo_negocio_nuevo",
                []
            ),
        ),
        (
            "SedeNueva",
            [
                "Grupo",
                "Sede",
                "Tipo de negocio",
            ],
            result.get(
                "sede_nueva",
                []
            ),
        ),
    ]

    for sheet_name, headers, rows in configurations:

        worksheet = workbook[
            sheet_name
        ]

        # Eliminamos datos antiguos,
        # conservando la primera fila/encabezados.
        if worksheet.max_row > 1:
            worksheet.delete_rows(
                2,
                worksheet.max_row - 1,
            )

        # Reescribimos encabezados para asegurar
        # que coincidan con la estructura esperada.
        for column, header in enumerate(
            headers,
            start=1,
        ):
            worksheet.cell(
                row=1,
                column=column,
                value=header,
            )

        for row in rows:

            worksheet.append([
                row.get(
                    header,
                    ""
                )
                for header in headers
            ])

    workbook.save(
        template_path
    )


def run_phase3_preview(
    valid_report_path: str | None = None,
    simulate_client: dict | None = None,
) -> dict:

    # ==========================================================
    # REPORTE VALIDOS
    # ==========================================================

    if not valid_report_path:

        root = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
            )
        )

        files = glob.glob(
            os.path.join(
                root,
                "salidas",
                "ejecucion_*",
                "reporte_VALIDOS_*.xlsx",
            )
        )

        if not files:
            raise FileNotFoundError(
                "No existen reportes VALIDOS."
            )

        valid_report_path = max(
            files,
            key=os.path.getmtime,
        )

    valid_report_path = os.path.abspath(
        valid_report_path
    )

    workbook = pd.ExcelFile(
        valid_report_path
    )

    if "DATOS_TECNICOS" in workbook.sheet_names:
        sheet = "DATOS_TECNICOS"

    elif "VALIDOS" in workbook.sheet_names:
        sheet = "VALIDOS"

    else:
        sheet = workbook.sheet_names[0]

    # Leer como texto para preservar identificadores.
    #
    # Importante para El Salvador:
    # los NIT pueden comenzar con cero (ej. 06141702991026).
    # Si Pandas infiere la columna como numerica, elimina ese cero
    # antes de que AmbitosBuilderService pueda procesarlo.
    df = pd.read_excel(
        valid_report_path,
        sheet_name=sheet,
        dtype=str,
    )

    # ==========================================================
    # PAIS
    # ==========================================================

    countries = (
        df["pais"]
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
            "FASE 3 actualmente requiere "
            "una ejecucion por pais."
        )

    country = countries[0]

    # ==========================================================
    # BD
    # ==========================================================

    db = DbValidationService()

    # Para generar nuevas relaciones no debemos depender de
    # ClientSupplier. Un cliente puede existir en Person aunque
    # todavia no tenga proveedores relacionados.
    config_service = AmbitosConfigService()

    configured_client_names = list(
        config_service
        .get_clients(country)
        .keys()
    )

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
                    "name",
                ),

            "document_number":
                simulate_client.get(
                    "document_number",
                ),
        })

    # ==========================================================
    # MATCHING
    # ==========================================================

    builder = AmbitosBuilderService()

    result = builder.build_from_dataframe(
        df=df,
        db_clients=clients,
    )

    # ==========================================================
    # NEGOCIOS + SEDES
    # ==========================================================

    assignment = AmbitosAssignmentService()

    result = assignment.enrich(
        result=result,
        country=country,
    )

    # ==========================================================
    # PROTEGER IDENTIFICADORES
    # ==========================================================

    for collection, fields in [
        (
            result.get(
                "entidades",
                []
            ),
            ["RUC"],
        ),
        (
            result.get(
                "relacion_nueva",
                []
            ),
            ["RUC"],
        ),
        (
            result.get(
                "ambitos",
                []
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

    # ==========================================================
    # OUTPUT
    # ==========================================================

    run_folder = os.path.dirname(
        valid_report_path
    )

    excel_service = AmbitosExcelService(
        output_dir=run_folder
    )

    template_path = os.path.join(
        run_folder,
        "plantilla_ambitos_PREVIEW.xlsx"
    )

    excel_service.export_template_ambitos(
        data=result,
        output_path=template_path,
    )

    # Reemplazar catalogos estaticos antiguos por la
    # configuracion real del cliente/pais.
    _rewrite_dynamic_catalogs(
        template_path=template_path,
        result=result,
    )

    # ==========================================================
    # REPORTE DIAGNOSTICO
    # ==========================================================

    diagnostics_path = os.path.join(
        run_folder,
        "fase3_diagnostico.xlsx"
    )

    with pd.ExcelWriter(
        diagnostics_path,
        engine="openpyxl",
    ) as writer:

        pd.DataFrame(
            result.get(
                "matched_relations",
                []
            )
        ).to_excel(
            writer,
            sheet_name="MATCHED",
            index=False,
        )

        pd.DataFrame(
            result.get(
                "no_match",
                []
            )
        ).to_excel(
            writer,
            sheet_name="NO_MATCH",
            index=False,
        )

        pd.DataFrame(
            result.get(
                "tipo_negocio_nuevo",
                []
            )
        ).to_excel(
            writer,
            sheet_name="NEGOCIOS",
            index=False,
        )

        pd.DataFrame(
            result.get(
                "sede_nueva",
                []
            )
        ).to_excel(
            writer,
            sheet_name="SEDES",
            index=False,
        )

    return {
        "country":
            country,

        "usuarios":
            len(df),

        "clientes_bd":
            len(clients),

        "matched":
            len(
                result.get(
                    "matched_relations",
                    []
                )
            ),

        "no_match":
            len(
                result.get(
                    "no_match",
                    []
                )
            ),

        "entidades":
            len(
                result.get(
                    "entidades",
                    []
                )
            ),

        "relacion_nueva":
            len(
                result.get(
                    "relacion_nueva",
                    []
                )
            ),

        "ambitos":
            len(
                result.get(
                    "ambitos",
                    []
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
    }




