"""Typed presentation adapters. Backend dictionaries and workflow gates stay unchanged."""
from dataclasses import dataclass
from typing import Any, Literal, Mapping

Country = Literal["PER", "SLV"]
Result = Mapping[str, Any]


@dataclass(frozen=True)
class Metric:
    title: str
    value: int


def metrics(result: Result, columns: tuple[tuple[str, str], ...]) -> tuple[Metric, ...]:
    return tuple(Metric(title, int(result.get(key, 0))) for title, key in columns)


@dataclass(frozen=True)
class Phase1Summary:
    total: int
    valid: int
    errors: int
    users: int
    message: str

    @classmethod
    def from_backend(cls, country: Country, result: Result) -> "Phase1Summary":
        total = int(result.get("total", 0))
        if country == "SLV":
            valid = int(result.get("validos", 0))
            return cls(total, valid, int(result.get("errores", 0)), valid,
                       "La plantilla de usuarios de El Salvador fue generada.")
        if country != "PER":
            raise ValueError(f"Pais no soportado: {country}")
        return cls(
            total, int(result.get("valid_relations", 0)),
            int(result.get("errors", 0)), int(result.get("unique_users", 0)),
            f"Ya creados omitidos: {int(result.get('already_created', 0))} · "
            f"Errores previos: {int(result.get('previous_errors', 0))}",
        )


@dataclass(frozen=True)
class ResultFiles:
    result_label: str
    plan_label: str
    result_available: bool
    evidence_available: bool
    plan_available: bool


def scope_metrics(mode: Literal["preview", "final"], result: Result) -> tuple[Metric, ...]:
    if mode == "preview":
        columns = (
            ("CREADO=1", "usuarios"), ("Matched", "matched"), ("Revisión", "no_match"),
            ("Entidades", "entidades"), ("Relaciones", "relacion_nueva"), ("Ámbitos", "ambitos"),
        )
    elif mode == "final":
        columns = (
            ("CREADO=1", "creado_1"), ("Finales", "registros_finales"),
            ("Pend. cliente", "pendientes_cliente"), ("Pend. técnicos", "pendientes_tecnicos"),
            ("Relaciones", "relacion_nueva"), ("Ámbitos", "ambitos"),
        )
    else:
        raise ValueError(f"Modo no soportado: {mode}")
    return metrics(result, columns)


@dataclass(frozen=True)
class Phase2Presentation:
    metrics: tuple[Metric, ...]
    detail: str
    files: ResultFiles | None = None

    @classmethod
    def from_backend(
        cls, country: Country, mode: Literal["preview", "local_copy", "apply"], result: Result,
    ) -> "Phase2Presentation":
        if country not in ("PER", "SLV"):
            raise ValueError(f"Pais no soportado: {country}")
        if mode == "local_copy":
            if country != "PER":
                raise ValueError("Copia local solo corresponde a PER")
            return cls(metrics(result, (
                ("Cambios locales", "cambios_aplicados"),
                ("Verificado = 1", "verificado_creado_1"),
                ("Verificado = 2", "verificado_creado_2"),
                ("Filas verificadas", "filas_verificadas"),
            )), "Copia local generada y verificada. SharePoint NO fue modificado. "
                "Esta copia representa el estado del Excel descargado en este momento.",
                ResultFiles("Abrir copia local", "Abrir reporte local",
                            bool(result.get("candidate_path")), bool(result.get("evidence_path")),
                            bool(result.get("report_path"))))
        if mode == "apply":
            if country == "PER":
                return cls(metrics(result, (
                    ("Relaciones", "relaciones_total"),
                    ("Verificado = 1", "verificado_creado_1"),
                    ("Verificado = 2", "verificado_creado_2"),
                    ("Filas verificadas", "filas_verificadas"),
                )), "Excel remoto actualizado, descargado nuevamente y verificado.")
            return cls(metrics(result, (
                ("Resultados", "total"), ("CREADO = 1", "creados"),
                ("CREADO = 2", "errores"), ("Actualizados", "updated"),
            )), "Estados CREADO actualizados en SharePoint.")
        if mode != "preview":
            raise ValueError(f"Modo no soportado: {mode}")
        if country == "PER":
            return cls(metrics(result, (
                ("Cuentas enviadas", "cuentas_enviadas"), ("Disponibles", "cuentas_disponibles"),
                ("No creadas", "cuentas_no_creadas"), ("Cambios remotos", "actualizaciones_remotas_preview"),
            )), f"Relaciones: {result.get('relaciones_total', 0)} · "
                f"creado=1: {result.get('relaciones_creado_1', 0)} · "
                f"creado=2: {result.get('relaciones_creado_2', 0)} · "
                f"sin resultado: {result.get('relaciones_sin_resultado', 0)} · "
                f"conflictos: {result.get('conflictos_remotos', 0)}",
                ResultFiles("Abrir resultado", "Abrir plan", bool(result.get("preview_path")),
                            bool(result.get("evidence_path")), bool(result.get("plan_path"))))
        return cls(metrics(result, (
            ("Resultados", "total"), ("Creados", "creados"), ("Errores", "errores"),
        )) + (Metric("Cambios preview", len(result.get("preview", []))),),
            f"Actualizados en dry-run: {result.get('updated', 0)} · "
            f"omitidos: {result.get('skipped', 0)} · fallidos: {len(result.get('failed', []))}",
            ResultFiles("Abrir resultado", "Abrir plan", bool(result.get("result_path")), False, False))
