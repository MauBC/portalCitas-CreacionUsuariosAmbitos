import os
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment


class AmbitosExcelService:
    def __init__(self, output_dir: str = "salidas"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def export_template_ambitos(self, data: dict | None = None, output_path: str | None = None) -> str:
        data = data or {}

        wb = Workbook()
        default_sheet = wb.active
        wb.remove(default_sheet)

        self._create_sheet(
            wb=wb,
            sheet_name="Entidades",
            headers=[
                "Razon Social",
                "Apellidos y nombres",
                "Tipo",
                "RUC",
                "Email",
                "Telefono",
                "Direccion",
                "Tipo Usuario",
                "Tipo de negocio Nuevo",
                "Tipo de negocio Eliminar",
                "Relacion Nueva",
                "Relacion Eliminada",
                "Estado",
                "Comentario",
            ],
            widths={
                "A": 37.29,
                "B": 33.71,
                "C": 14.57,
                "D": 13.71,
                "E": 32.71,
                "F": 12.00,
                "G": 20.00,
                "H": 35.86,
                "I": 20.86,
                "J": 23.29,
                "K": 26.43,
                "L": 23.71,
                "M": 17.43,
                "N": 58.43,
            },
            data_rows=data.get("entidades", []),
            freeze_panes="A2",
        )

        self._create_sheet(
            wb=wb,
            sheet_name="Ambitos",
            headers=[
                "Email",
                "Empresa",
                "Todos los negocios",
                "Todas las sedes",
                "Sedes Nuevas",
                "Sedes Eliminadas",
                "Estado",
                "Comentario",
            ],
            widths={
                "A": 35.14,
                "B": 19.86,
                "C": 23.29,
                "D": 14.00,
                "E": 19.43,
                "F": 21.43,
                "G": 11.43,
                "H": 38.57,
            },
            data_rows=data.get("ambitos", []),
        )

        self._create_sheet(
            wb=wb,
            sheet_name="RelacionNueva",
            headers=[
                "Grupo",
                "Razon Social",
                "RUC",
            ],
            widths={
                "A": 11.57,
                "B": 40.14,
                "C": 43.00,
            },
            data_rows=data.get("relacion_nueva", []),
        )

        self._create_sheet(
            wb=wb,
            sheet_name="RelacionEliminar",
            headers=[
                "Grupo",
                "Razon Social",
                "RUC",
            ],
            widths={
                "A": 11.43,
                "B": 46.14,
                "C": 39.86,
            },
            data_rows=[],
        )

        self._create_sheet(
            wb=wb,
            sheet_name="TipoNegocioNuevo",
            headers=[
                "Grupo",
                "Tipo de negocio",
                "Rubro",
            ],
            widths={
                "A": 11.43,
                "B": 43.29,
                "C": 87.14,
            },
            data_rows=[
                {"Grupo": 1, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Tecnologia"},
                {"Grupo": 2, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Consumo masivo"},
                {"Grupo": 3, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Perfumeria y farmacia"},
                {"Grupo": 4, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Retail"},
                {"Grupo": 5, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Alimentos y bebidas"},
                {"Grupo": 6, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Productos adhesivos"},
                {"Grupo": 7, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Tratamiento y distribucion de agua"},
                {"Grupo": 8, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Farmacia y cosmeticos"},
                {"Grupo": 9, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Mineria"},
                {"Grupo": 10, "Tipo de negocio": "Fresh & Cold", "Rubro": "Alimentos y bebidas"},
            ],
        )

        self._create_sheet(
            wb=wb,
            sheet_name="TipoNegocioEliminar",
            headers=[
                "Grupo",
                "Tipo de negocio",
                "Rubro",
            ],
            widths={
                "A": 11.43,
                "B": 47.43,
                "C": 66.43,
            },
            data_rows=[
                {"Grupo": 1, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Tecnologia"},
                {"Grupo": 2, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Consumo masivo"},
                {"Grupo": 3, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Perfumeria y farmacia"},
                {"Grupo": 4, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Retail"},
                {"Grupo": 5, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Alimentos y bebidas"},
                {"Grupo": 6, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Productos adhesivos"},
                {"Grupo": 7, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Tratamiento y distribucion de agua"},
                {"Grupo": 8, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Farmacia y cosmeticos"},
                {"Grupo": 9, "Tipo de negocio": "Centros de Distribucion", "Rubro": "Mineria"},
                {"Grupo": 10, "Tipo de negocio": "Fresh & Cold", "Rubro": "Alimentos y bebidas"},
            ],
        )

        self._create_sheet(
            wb=wb,
            sheet_name="SedeNueva",
            headers=[
                "Grupo",
                "Sede",
                "Tipo de negocio",
            ],
            widths={
                "A": 11.43,
                "B": 43.86,
                "C": 74.29,
            },
            data_rows=[
                {"Grupo": 1, "Sede": "RSA", "Tipo de negocio": "Centros de Distribucion"},
                {"Grupo": 2, "Sede": "RAA", "Tipo de negocio": "Centros de Distribucion"},
                {"Grupo": 3, "Sede": "Ransa Lurin", "Tipo de negocio": "Centros de Distribucion"},
                {"Grupo": 4, "Sede": "RAA", "Tipo de negocio": "Fresh & Cold"},
            ],
        )

        self._create_sheet(
            wb=wb,
            sheet_name="SedeEliminar",
            headers=[
                "Grupo",
                "Sede",
                "Tipo de negocio",
            ],
            widths={
                "A": 11.43,
                "B": 38.86,
                "C": 54.57,
            },
            data_rows=[
                {"Grupo": 1, "Sede": "RSA", "Tipo de negocio": "Centros de Distribucion"},
                {"Grupo": 2, "Sede": "RAA", "Tipo de negocio": "Centros de Distribucion"},
                {"Grupo": 3, "Sede": "Ransa Lurin", "Tipo de negocio": "Centros de Distribucion"},
                {"Grupo": 4, "Sede": "RAA", "Tipo de negocio": "Fresh & Cold"},
            ],
        )

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(
                self.output_dir,
                f"plantilla_ambitos_{timestamp}.xlsx"
            )

        wb.save(output_path)
        return os.path.abspath(output_path)

    def _create_sheet(
        self,
        wb,
        sheet_name: str,
        headers: list[str],
        widths: dict[str, float],
        data_rows: list,
        freeze_panes: str | None = None,
    ):
        ws = wb.create_sheet(title=sheet_name)

        if freeze_panes:
            ws.freeze_panes = freeze_panes

        header_fill = PatternFill(fill_type="solid", fgColor="FF002060")
        header_font = Font(bold=True, color="FFFFFFFF")
        thin_side = Side(style="thin", color="FF000000")
        medium_side = Side(style="medium", color="FF000000")

        for col_idx, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

            left_side = medium_side if col_idx == 1 else thin_side
            cell.border = Border(
                left=left_side,
                right=thin_side,
                top=thin_side,
                bottom=thin_side,
            )

        for row_idx, row_data in enumerate(data_rows, start=2):
            for col_idx, header in enumerate(headers, start=1):
                value = row_data.get(header, "") if isinstance(row_data, dict) else ""
                ws.cell(row=row_idx, column=col_idx, value=value)

        for col_letter, width in widths.items():
            ws.column_dimensions[col_letter].width = width

        ws.row_dimensions[1].height = 22
