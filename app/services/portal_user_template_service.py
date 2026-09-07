from pathlib import Path
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

import pandas as pd


class PortalUserTemplateService:

    EXPECTED_SHEETS = [
        "USUARIOS",
        "CLIENTES",
        "SERVICIOS",
        "MAESTROS",
    ]

    USER_COLUMNS = [
        "NOMBRE",
        "APELLIDO",
        "CORREO",
        "PAIS",
        "PERFIL DE USUARIO",
        "TIPO DE USUARIO",
        "TIPO DE DOCUMENTO IDENTIDAD",
        "DOCUMENTO",
        "SOCIEDAD",
        "CLIENTE",
        "SERVICIO",
    ]

    TEMPLATE_MIN_ROW = 22

    def __init__(self, template_path=None):

        project_root = Path(__file__).resolve().parents[2]

        self.template_path = Path(
            template_path
            or project_root
            / "app"
            / "templates"
            / "subida_usuarios.xlsx"
        )

    def write(
        self,
        usuarios: pd.DataFrame,
        output_path,
        service_name: str,
    ) -> str:

        self._validate_template()

        missing = [
            column
            for column in self.USER_COLUMNS
            if column not in usuarios.columns
        ]

        if missing:
            raise ValueError(
                "Faltan columnas USUARIOS: "
                + ", ".join(missing)
            )

        usuarios = (
            usuarios[self.USER_COLUMNS]
            .fillna("")
            .astype(str)
        )

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = output_path.with_suffix(
            output_path.suffix + ".tmp"
        )

        if temp_path.exists():
            temp_path.unlink()

        with zipfile.ZipFile(
            self.template_path,
            "r",
        ) as source:

            with zipfile.ZipFile(
                temp_path,
                "w",
            ) as target:

                for item in source.infolist():

                    data = source.read(
                        item.filename
                    )

                    if (
                        item.filename
                        == "xl/worksheets/sheet1.xml"
                    ):
                        data = self._build_usuarios_xml(
                            xml_bytes=data,
                            usuarios=usuarios,
                        )

                    elif (
                        item.filename
                        == "xl/worksheets/sheet3.xml"
                    ):
                        data = self._build_servicios_xml(
                            xml_bytes=data,
                            service_name=service_name,
                        )

                    target.writestr(
                        item,
                        data,
                    )

        os.replace(
            temp_path,
            output_path,
        )

        return str(output_path)

    def _validate_template(self):

        if not self.template_path.exists():

            raise FileNotFoundError(
                "No existe plantilla oficial: "
                f"{self.template_path}"
            )

        with zipfile.ZipFile(
            self.template_path,
            "r",
        ) as workbook:

            root = ET.fromstring(
                workbook.read(
                    "xl/workbook.xml"
                )
            )

        namespace = {
            "m":
                "http://schemas.openxmlformats.org/"
                "spreadsheetml/2006/main"
        }

        sheets = [
            sheet.attrib["name"]
            for sheet in root.findall(
                "m:sheets/m:sheet",
                namespace,
            )
        ]

        if sheets != self.EXPECTED_SHEETS:

            raise ValueError(
                "La plantilla oficial tiene hojas "
                f"distintas: {sheets}"
            )

    def _build_usuarios_xml(
        self,
        xml_bytes,
        usuarios,
    ):

        text = xml_bytes.decode(
            "utf-8"
        )

        header = self._get_header_row(
            text
        )

        rows = [header]

        for row_number, (_, user) in enumerate(
            usuarios.iterrows(),
            start=2,
        ):

            values = [
                user[column]
                for column in self.USER_COLUMNS
            ]

            rows.append(
                self._build_row(
                    row_number=row_number,
                    values=values,
                    numeric_columns={11},
                    style_columns={8: "11"},
                )
            )

        max_row = max(
            self.TEMPLATE_MIN_ROW,
            len(usuarios) + 1,
        )

        first_empty_row = (
            len(usuarios) + 2
        )

        for row_number in range(
            first_empty_row,
            max_row + 1,
        ):

            rows.append(
                self._build_row(
                    row_number=row_number,
                    values=[
                        ""
                        for _ in self.USER_COLUMNS
                    ],
                    numeric_columns={11},
                    style_columns={8: "11"},
                )
            )

        return self._replace_sheet_data(
            text=text,
            rows=rows,
            dimension=f"A1:K{max_row}",
        )

    def _build_servicios_xml(
        self,
        xml_bytes,
        service_name,
    ):

        text = xml_bytes.decode(
            "utf-8"
        )

        header = self._get_header_row(
            text
        )

        rows = [
            header,
            self._build_row(
                row_number=2,
                values=[
                    service_name,
                    "PACCESO_PROVEEDOR",
                    1,
                ],
                numeric_columns={3},
            ),
            self._build_row(
                row_number=3,
                values=[
                    service_name,
                    "PACCESO_CLIENTE",
                    2,
                ],
                numeric_columns={3},
            ),
        ]

        return self._replace_sheet_data(
            text=text,
            rows=rows,
            dimension="A1:C3",
        )

    @staticmethod
    def _get_header_row(text):

        match = re.search(
            r'(<row r="1".*?</row>)',
            text,
            flags=re.DOTALL,
        )

        if not match:

            raise RuntimeError(
                "No se encontro encabezado "
                "de la hoja"
            )

        return match.group(1)

    @staticmethod
    def _replace_sheet_data(
        text,
        rows,
        dimension,
    ):

        new_sheet_data = (
            "<sheetData>"
            + "".join(rows)
            + "</sheetData>"
        )

        text, count = re.subn(
            r"<sheetData>.*?</sheetData>",
            new_sheet_data,
            text,
            count=1,
            flags=re.DOTALL,
        )

        if count != 1:

            raise RuntimeError(
                "No se pudo actualizar sheetData"
            )

        text, count = re.subn(
            r'<dimension ref="[^"]+"',
            f'<dimension ref="{dimension}"',
            text,
            count=1,
        )

        if count != 1:

            raise RuntimeError(
                "No se pudo actualizar dimension"
            )

        return text.encode(
            "utf-8"
        )

    def _build_row(
        self,
        row_number,
        values,
        numeric_columns=None,
        style_columns=None,
    ):

        numeric_columns = (
            numeric_columns or set()
        )

        style_columns = (
            style_columns or {}
        )

        cells = []

        for index, value in enumerate(
            values,
            start=1,
        ):

            column = self._column_letter(
                index
            )

            cell_ref = (
                f"{column}{row_number}"
            )

            style = style_columns.get(
                index,
                "6",
            )

            value = (
                ""
                if value is None
                else str(value)
            )

            if (
                index in numeric_columns
                and value.strip().isdigit()
            ):

                cells.append(
                    f'<c r="{cell_ref}" '
                    f's="{style}">'
                    f'<v>{int(value)}</v>'
                    '</c>'
                )

            elif value:

                encoded = escape(
                    value
                )

                cells.append(
                    f'<c r="{cell_ref}" '
                    f's="{style}" '
                    't="inlineStr">'
                    '<is>'
                    '<t xml:space="preserve">'
                    f'{encoded}'
                    '</t>'
                    '</is>'
                    '</c>'
                )

            else:

                cells.append(
                    f'<c r="{cell_ref}" '
                    f's="{style}"/>'
                )

        return (
            f'<row r="{row_number}">'
            + "".join(cells)
            + "</row>"
        )

    @staticmethod
    def _column_letter(index):

        result = ""

        while index:

            index, remainder = divmod(
                index - 1,
                26,
            )

            result = (
                chr(65 + remainder)
                + result
            )

        return result
