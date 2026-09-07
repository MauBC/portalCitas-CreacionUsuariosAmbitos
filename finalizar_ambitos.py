from app.phase3_pipeline import (
    run_phase3_final
)


def main():
    result = run_phase3_final()

    print("=" * 110)
    print("FASE 3 - GENERACION FINAL DE AMBITOS")
    print("=" * 110)

    print(
        f"Pais                  : "
        f"{result['country']}"
    )

    print(
        f"Registros fuente      : "
        f"{result['registros_fuente']}"
    )

    print(
        f"CREADO=1              : "
        f"{result['creado_1']}"
    )

    print(
        f"Automaticos           : "
        f"{result['automaticos']}"
    )

    print(
        f"Revision total        : "
        f"{result['revision_total']}"
    )

    print(
        f"Manuales asignados    : "
        f"{result['manuales_asignados']}"
    )

    print(
        f"Manuales incorporados : "
        f"{result['manuales_incorporados']}"
    )

    print(
        f"Pendientes cliente    : "
        f"{result['pendientes_cliente']}"
    )

    print(
        f"Pendientes tecnicos   : "
        f"{result['pendientes_tecnicos']}"
    )

    print(
        f"Registros finales     : "
        f"{result['registros_finales']}"
    )

    print(
        f"Ambitos finales       : "
        f"{result['ambitos']}"
    )

    print()
    print(
        "[OK] Plantilla final:"
    )
    print(
        result["template_path"]
    )

    print()
    print(
        "Diagnostico:"
    )
    print(
        result["diagnostics_path"]
    )

    if result["pendientes_total"]:
        print()
        print(
            f"[WARN] "
            f"{result['pendientes_total']} "
            "registro(s) quedaron pendientes "
            "y NO fueron incluidos."
        )

    print("=" * 110)


if __name__ == "__main__":
    main()
