from pathlib import Path
import sys

import pandas as pd


def find_one(folder: Path, pattern: str) -> Path:
    files = sorted(folder.glob(pattern))

    if len(files) != 1:
        raise RuntimeError(
            f"Se esperaba 1 archivo para {pattern}, "
            f"pero se encontraron {len(files)}."
        )

    return files[0]


def read_report(path: Path) -> pd.DataFrame:
    xls = pd.ExcelFile(path)

    if "DATOS_TECNICOS" in xls.sheet_names:
        sheet = "DATOS_TECNICOS"
    else:
        sheet = xls.sheet_names[0]

    return pd.read_excel(
        path,
        sheet_name=sheet,
        dtype=str,
        keep_default_na=False,
    )


def find_email_column(df: pd.DataFrame) -> str:
    candidates = {
        "correo",
        "email",
        "correo_electronico",
        "correo electrónico",
    }

    normalized = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]

    raise RuntimeError(
        "No se encontro una columna de correo "
        f"en: {list(df.columns)}"
    )


def normalize_email_series(series: pd.Series) -> pd.Series:
    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )


def main():
    if len(sys.argv) != 2:
        print(
            "Uso: python validar_ejecucion_proveedores.py "
            "<carpeta_ejecucion>"
        )
        raise SystemExit(2)

    folder = Path(sys.argv[1]).resolve()

    if not folder.exists():
        raise FileNotFoundError(
            f"No existe la carpeta: {folder}"
        )

    validos_path = find_one(
        folder,
        "reporte_excel_VALIDOS_*.xlsx",
    )

    errores_path = find_one(
        folder,
        "reporte_excel_ERRORES_*.xlsx",
    )

    plantilla_path = find_one(
        folder,
        "plantilla_usuarios_*.xlsx",
    )

    validos = read_report(validos_path)
    errores = read_report(errores_path)

    usuarios = pd.read_excel(
        plantilla_path,
        sheet_name="USUARIOS",
        dtype=str,
        keep_default_na=False,
    )

    print("=" * 95)
    print("COMPROBACION DE CREACION DE USUARIOS")
    print("=" * 95)

    print()
    print("ARCHIVOS")
    print("-" * 95)
    print(f"VALIDOS   : {validos_path.name}")
    print(f"ERRORES   : {errores_path.name}")
    print(f"PLANTILLA : {plantilla_path.name}")

    valid_email_column = find_email_column(
        validos
    )

    valid_emails = normalize_email_series(
        validos[valid_email_column]
    )

    user_emails = normalize_email_series(
        usuarios["CORREO"]
    )

    valid_emails_nonempty = valid_emails[
        valid_emails != ""
    ]

    user_emails_nonempty = user_emails[
        user_emails != ""
    ]

    unique_valid_emails = set(
        valid_emails_nonempty
    )

    unique_user_emails = set(
        user_emails_nonempty
    )

    missing_users = sorted(
        unique_valid_emails
        - unique_user_emails
    )

    extra_users = sorted(
        unique_user_emails
        - unique_valid_emails
    )

    duplicate_users = int(
        user_emails_nonempty.duplicated().sum()
    )

    empty_users = int(
        (user_emails == "").sum()
    )

    required_columns = [
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

    missing_columns = [
        column
        for column in required_columns
        if column not in usuarios.columns
    ]

    countries = sorted(
        {
            value
            for value in (
                usuarios["PAIS"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
            )
            if value
        }
    )

    print()
    print("CONTEOS")
    print("-" * 95)
    print(
        f"Relaciones VALIDAS          : "
        f"{len(validos):,}"
    )
    print(
        f"Registros con ERROR         : "
        f"{len(errores):,}"
    )
    print(
        f"Usuarios unicos en VALIDOS  : "
        f"{len(unique_valid_emails):,}"
    )
    print(
        f"Usuarios en plantilla       : "
        f"{len(usuarios):,}"
    )

    print()
    print("INTEGRIDAD")
    print("-" * 95)
    print(
        f"Correos vacios plantilla    : "
        f"{empty_users}"
    )
    print(
        f"Correos duplicados plantilla: "
        f"{duplicate_users}"
    )
    print(
        f"Usuarios faltantes          : "
        f"{len(missing_users)}"
    )
    print(
        f"Usuarios extra              : "
        f"{len(extra_users)}"
    )
    print(
        f"Columnas faltantes          : "
        f"{missing_columns}"
    )
    print(
        f"Paises en plantilla         : "
        f"{countries}"
    )

    errors = []

    if len(validos) != 230:
        errors.append(
            f"Se esperaban 230 relaciones validas "
            f"y hay {len(validos)}."
        )

    if len(errores) != 91:
        errors.append(
            f"Se esperaban 91 errores "
            f"y hay {len(errores)}."
        )

    if len(unique_valid_emails) != 225:
        errors.append(
            "Los 230 registros validos no producen "
            "225 correos unicos."
        )

    if len(usuarios) != 225:
        errors.append(
            f"La plantilla tiene {len(usuarios)} "
            "usuarios en lugar de 225."
        )

    if empty_users:
        errors.append(
            f"Hay {empty_users} correo(s) vacio(s)."
        )

    if duplicate_users:
        errors.append(
            f"Hay {duplicate_users} correo(s) "
            "duplicado(s) en USUARIOS."
        )

    if missing_users:
        errors.append(
            f"Faltan {len(missing_users)} usuarios "
            "validos en la plantilla."
        )

    if extra_users:
        errors.append(
            f"Hay {len(extra_users)} usuarios "
            "en la plantilla que no estan en VALIDOS."
        )

    if missing_columns:
        errors.append(
            "Faltan columnas obligatorias "
            "en la hoja USUARIOS."
        )

    if countries != ["PERU"]:
        errors.append(
            f"Se esperaba solamente PERU y se obtuvo "
            f"{countries}."
        )

    print()
    print("=" * 95)

    if errors:
        print("RESULTADO: ERROR")
        print()

        for error in errors:
            print(f"[ERROR] {error}")

        if missing_users:
            print()
            print("PRIMEROS USUARIOS FALTANTES:")
            for email in missing_users[:10]:
                print(f"  - {email}")

        if extra_users:
            print()
            print("PRIMEROS USUARIOS EXTRA:")
            for email in extra_users[:10]:
                print(f"  - {email}")

        raise SystemExit(1)

    print("RESULTADO: OK")
    print()
    print(
        "Los 230 registros validos generan "
        "exactamente 225 usuarios unicos."
    )
    print(
        "La plantilla contiene exactamente "
        "esos mismos 225 usuarios."
    )
    print(
        "No existen usuarios faltantes, "
        "extras ni correos duplicados."
    )
    print("=" * 95)


if __name__ == "__main__":
    main()