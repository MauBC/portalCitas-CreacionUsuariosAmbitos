from rapidfuzz import fuzz

from app.services.ambitos_config_service import AmbitosConfigService


class ClientAssignmentService:

    MIN_FUZZY_SCORE = 90
    MIN_SCORE_MARGIN = 10

    def __init__(self):
        self.ambitos_config = AmbitosConfigService()

    # ==========================================================
    # API SIMPLE
    # ==========================================================

    def resolve(
        self,
        row,
        country_config: dict,
    ) -> str:
        """
        Mantiene compatibilidad con el resto del proyecto.

        Retorna cliente canónico solamente cuando la resolución
        es segura.

        Si requiere revisión:
            retorna ""
        """

        result = self.resolve_with_details(
            row=row,
            country_config=country_config,
        )

        if result["status"] == "OK":
            return result["resolved_client"]

        return ""

    # ==========================================================
    # API DETALLADA
    # ==========================================================

    def resolve_with_details(
        self,
        row,
        country_config: dict,
    ) -> dict:

        country = str(
            row.get("pais") or ""
        ).strip().upper()

        raw_client = str(
            row.get("nombre_cliente") or ""
        ).strip()

        default_client = str(
            country_config.get(
                "cliente_default",
                ""
            )
            or ""
        ).strip()

        force_default = bool(
            country_config.get(
                "force_default_client",
                False,
            )
        )

        # ======================================================
        # CLIENTE VACIO
        # ======================================================

        if not raw_client:

            return self._result(
                raw_client="",
                resolved_client="",
                candidate_client="",
                score=0,
                method="NONE",
                status="REVISAR",
                reason="CLIENTE VACIO",
            )

        # ======================================================
        # FORZADO - SOLO SI ALGUN PAIS LO REQUIERE
        # ======================================================

        if force_default and default_client:

            return self._result(
                raw_client=raw_client,
                resolved_client=default_client,
                candidate_client=default_client,
                score=100,
                method="FORZADO",
                status="OK",
                reason="",
            )

        # ======================================================
        # SI EL PAIS NO TIENE CATALOGO CONFIGURADO
        # NO BLOQUEAMOS EL FLUJO
        # ======================================================

        configured_clients = (
            self.ambitos_config.get_clients(
                country
            )
        )

        if not configured_clients:

            return self._result(
                raw_client=raw_client,
                resolved_client=raw_client,
                candidate_client=raw_client,
                score=100,
                method="SIN_CATALOGO",
                status="OK",
                reason="",
            )

        # ======================================================
        # 1. ALIAS EXACTO
        # ======================================================

        alias_result = (
            self.ambitos_config.resolve_alias(
                country,
                raw_client,
            )
        )

        if alias_result:

            return self._result(
                raw_client=raw_client,
                resolved_client=alias_result,
                candidate_client=alias_result,
                score=100,
                method="ALIAS",
                status="OK",
                reason="",
            )

        # ======================================================
        # 2. FUZZY
        # ======================================================

        normalized_raw = (
            self.ambitos_config.normalize(
                raw_client
            )
        )

        scores = []

        for canonical, config in configured_clients.items():

            candidates = [
                canonical,
                config.get(
                    "db_name",
                    canonical,
                ),
            ]

            candidates.extend(
                config.get(
                    "aliases",
                    []
                )
            )

            best_client_score = 0

            for candidate in candidates:

                normalized_candidate = (
                    self.ambitos_config.normalize(
                        candidate
                    )
                )

                score = fuzz.WRatio(
                    normalized_raw,
                    normalized_candidate,
                )

                best_client_score = max(
                    best_client_score,
                    score,
                )

            scores.append(
                (
                    canonical,
                    float(best_client_score),
                )
            )

        scores.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        best_client, best_score = scores[0]

        second_score = (
            scores[1][1]
            if len(scores) > 1
            else 0
        )

        margin = (
            best_score
            - second_score
        )

        # ======================================================
        # FUZZY SEGURO
        # ======================================================

        if (
            best_score >= self.MIN_FUZZY_SCORE
            and margin >= self.MIN_SCORE_MARGIN
        ):

            return self._result(
                raw_client=raw_client,
                resolved_client=best_client,
                candidate_client=best_client,
                score=best_score,
                method="FUZZY",
                status="OK",
                reason="",
            )

        # ======================================================
        # REQUIERE REVISION
        # ======================================================

        if best_score < self.MIN_FUZZY_SCORE:

            reason = (
                "CLIENTE NO RECONOCIDO "
                f"(mejor coincidencia: {best_client}, "
                f"score: {best_score:.2f})"
            )

        else:

            reason = (
                "CLIENTE AMBIGUO "
                f"(mejor: {best_client}, "
                f"score: {best_score:.2f}, "
                f"margen: {margin:.2f})"
            )

        return self._result(
            raw_client=raw_client,
            resolved_client="",
            candidate_client=best_client,
            score=best_score,
            method="REVISAR",
            status="REVISAR",
            reason=reason,
        )

    @staticmethod
    def _result(
        raw_client,
        resolved_client,
        candidate_client,
        score,
        method,
        status,
        reason,
    ):

        return {
            "raw_client":
                raw_client,

            "resolved_client":
                resolved_client,

            "candidate_client":
                candidate_client,

            "score":
                round(float(score), 2),

            "method":
                method,

            "status":
                status,

            "reason":
                reason,
        }
