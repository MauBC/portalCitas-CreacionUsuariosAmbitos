import pandas as pd
from rapidfuzz import process, fuzz

from app.services.client_assignment_service import ClientAssignmentService
from app.config.portal_template_config import COUNTRY_TEMPLATE_CONFIG


class AmbitosBuilderService:
    MIN_SCORE_CLIENT_MATCH = 90

    def __init__(self):
        self.client_assignment = ClientAssignmentService()

    def build_from_gemini_results(
            self,
            gemini_results: list[dict],
            db_clients: list[dict],
            persons_by_ruc: dict | None = None,
            df_ambitos: pd.DataFrame | None = None,
        ) -> dict:
        clients_index = self._build_clients_index(db_clients)
        persons_by_ruc = persons_by_ruc or {}
        matched_relations = []
        no_match_rows = []

        for provider in gemini_results:
            proveedor_nombre = provider.get("proveedor_nombre")
            proveedor_ruc = self._normalize_ruc(provider.get("proveedor_ruc"))
            input_clientes = provider.get("input_clientes")
            clientes_detectados = provider.get("clientes_detectados", [])
            proveedor_email = provider.get("proveedor_email")

            if not proveedor_nombre or not proveedor_ruc:
                continue

            if not isinstance(clientes_detectados, list):
                clientes_detectados = []

            for detected in clientes_detectados:
                match_result = self._match_detected_client(detected, clients_index, input_clientes)
                if match_result["ok"]:
                    matched_relations.append({
                        "proveedor_nombre": proveedor_nombre,
                        "proveedor_ruc": proveedor_ruc,
                        "proveedor_email": proveedor_email,
                        "input_clientes": input_clientes,
                        "cliente_detectado": detected,
                        "cliente_bd": match_result["client"],
                        "match_field": match_result["match_field"],
                        "match_value": match_result["match_value"],
                        "match_score": match_result["score"],
                    })
                else:
                    no_match_rows.append({
                        "email": proveedor_email,
                        "proveedor_nombre": proveedor_nombre,
                        "proveedor_ruc": proveedor_ruc,
                        "input_clientes": input_clientes,
                        "cliente_input": detected.get("cliente_input"),
                        "cliente_canonico_sugerido": detected.get("cliente_canonico_sugerido"),
                        "grupo_economico": detected.get("grupo_economico"),
                        "confianza": detected.get("confianza"),
                        "mensaje": "No se encontro cliente en la base de datos",
                    })

        grouped_clients = self._assign_groups(matched_relations)

        entidades_rows = self._build_entidades_rows(grouped_clients, persons_by_ruc)        
        relacion_nueva_rows = self._build_relacion_nueva_rows(grouped_clients,persons_by_ruc)
        ambitos_rows = []

        if df_ambitos is not None:
            ambitos_rows = self.build_ambitos_rows_from_dataframe(df_ambitos)        
        
        return {
            "entidades": entidades_rows,
            "ambitos": ambitos_rows,
            "relacion_nueva": relacion_nueva_rows,
            "no_match": no_match_rows,
            "matched_relations": matched_relations,
        }

    def build_from_dataframe(
        self,
        df: pd.DataFrame,
        db_clients: list[dict],
        persons_by_ruc: dict | None = None,
    ) -> dict:
        """
        Construye la informacion de ambitos directamente desde
        el DataFrame limpio/validado.

        FLUJO ACTUAL:
        - SLV trabaja con PROVEEDORES.
        - ClientAssignmentService resuelve temporalmente DOCTOR SV.
        - Se busca el cliente contra PostgreSQL.
        - El NIT del proveedor se utiliza como identificador Empresa.

        FUTURO:
        - ClientAssignmentService podra utilizar Gemini.
        - Este metodo no necesitara cambiar.
        """

        persons_by_ruc = persons_by_ruc or {}

        clients_index = self._build_clients_index(
            db_clients
        )

        matched_relations = []
        no_match_rows = []

        for _, row in df.iterrows():

            email = str(
                row.get("email") or ""
            ).strip().lower()

            perfil = self._normalize_text(
                row.get("perfil")
            )

            pais = self._normalize_text(
                row.get("pais")
            )

            # --------------------------------------------------
            # Por ahora esta fase trabaja con proveedores.
            # El soporte CLIENTE se agregara cuando el formulario
            # permita distinguir ambos tipos.
            # --------------------------------------------------

            if perfil != "PROVEEDOR":
                continue

            country_config = COUNTRY_TEMPLATE_CONFIG.get(
                pais
            )

            if not country_config:
                no_match_rows.append({
                    "email": email,
                    "proveedor_nombre": "",
                    "proveedor_ruc": "",
                    "cliente_input": "",
                    "mensaje": (
                        f"No existe configuracion para pais {pais}"
                    ),
                })
                continue

            proveedor_nombre = (
                str(
                    row.get("nombre_proveedor")
                    or row.get("nombres")
                    or ""
                )
                .strip()
            )

            # Aunque internamente la funcion se llama normalize_ruc,
            # sirve para limpiar cualquier identificador tributario.
            #
            # SLV -> NIT
            # PER -> RUC
            proveedor_ruc = self._normalize_ruc(
                row.get("nit_proveedor")
                or row.get("ruc_proveedor")
            )

            cliente_resuelto = (
                self.client_assignment.resolve(
                    row=row,
                    country_config=country_config,
                )
            )

            if not email:
                continue

            if not proveedor_nombre:
                no_match_rows.append({
                    "email": email,
                    "proveedor_nombre": "",
                    "proveedor_ruc": proveedor_ruc,
                    "cliente_input": cliente_resuelto,
                    "mensaje": "Proveedor sin nombre",
                })
                continue

            if not proveedor_ruc:
                no_match_rows.append({
                    "email": email,
                    "proveedor_nombre": proveedor_nombre,
                    "proveedor_ruc": "",
                    "cliente_input": cliente_resuelto,
                    "mensaje": "Proveedor sin identificador tributario",
                })
                continue

            if not cliente_resuelto:
                no_match_rows.append({
                    "email": email,
                    "proveedor_nombre": proveedor_nombre,
                    "proveedor_ruc": proveedor_ruc,
                    "cliente_input": "",
                    "mensaje": "No se pudo resolver cliente",
                })
                continue

            # --------------------------------------------------
            # Primero hacemos matching contra PostgreSQL.
            #
            # Actualmente:
            #   DOCTOR SV -> cliente en BD
            #
            # Futuro:
            #   texto formulario
            #       -> Gemini
            #       -> cliente normalizado
            #       -> PostgreSQL
            # --------------------------------------------------

            match_result = self._match_text_against_clients(
                cliente_resuelto,
                clients_index,
            )

            if not match_result["ok"]:

                no_match_rows.append({
                    "email": email,
                    "proveedor_nombre": proveedor_nombre,
                    "proveedor_ruc": proveedor_ruc,
                    "cliente_input": cliente_resuelto,
                    "mensaje": (
                        "No se encontro cliente en la base de datos"
                    ),
                    "match_score": match_result.get(
                        "score",
                        0,
                    ),
                })

                continue

            matched_relations.append({
                "proveedor_nombre":
                    proveedor_nombre,

                "proveedor_ruc":
                    proveedor_ruc,

                "proveedor_email":
                    email,

                "input_clientes":
                    cliente_resuelto,

                "cliente_detectado": {
                    "cliente_input":
                        cliente_resuelto,
                },

                "cliente_bd":
                    match_result["client"],

                "match_field":
                    "cliente_resuelto",

                "match_value":
                    cliente_resuelto,

                "match_score":
                    match_result["score"],
            })

        # ------------------------------------------------------
        # Reutilizamos la logica que ya existia
        # ------------------------------------------------------

        grouped_clients = self._assign_groups(
            matched_relations
        )

        entidades_rows = self._build_entidades_rows(
            grouped_clients,
            persons_by_ruc,
        )

        relacion_nueva_rows = self._build_relacion_nueva_rows(
            grouped_clients,
            persons_by_ruc,
        )

        ambitos_rows = self._build_ambitos_rows(
            grouped_clients
        )

        return {
            "entidades": entidades_rows,
            "ambitos": ambitos_rows,
            "relacion_nueva": relacion_nueva_rows,
            "no_match": no_match_rows,
            "matched_relations": matched_relations,
        }

    def _build_clients_index(self, db_clients: list[dict]) -> dict:
        clients_by_name = {}

        for client in db_clients:
            name = self._normalize_text(client.get("name"))
            if not name:
                continue

            clients_by_name[name] = client

        return {
            "names": list(clients_by_name.keys()),
            "by_name": clients_by_name,
        }
    

    ##
    def build_ambitos_rows_from_dataframe(self, df_ambitos: pd.DataFrame) -> list[dict]:
        rows = []
        added = set()

        for _, row in df_ambitos.iterrows():
            email = str(row.get("email") or "").strip().lower()
            perfil = str(row.get("perfil") or "").strip().upper()
            sede = row.get("sede")

            if not email:
                continue

            empresa = ""

            if perfil == "PROVEEDOR":
                empresa = self._normalize_ruc(row.get("ruc_proveedor"))

            elif perfil == "CLIENTE":
                empresa = self._normalize_ruc(row.get("ruc_cliente"))

            else:
                continue

            if not empresa:
                continue

            key = (email, empresa, str(sede).strip().upper())

            if key in added:
                continue

            added.add(key)

            rows.append({
                "Email": email,
                "Empresa": empresa,
                "Todos los negocios": False,
                "Todas las sedes": False,
                "Sedes Nuevas": self._map_sede(sede),
                "Sedes Eliminadas": "",
                "Estado": "",
                "Comentario": "",
            })

        return rows



    def _map_sede(self, sede):
        if pd.isna(sede):
            return ""

        sede = str(sede).strip().upper()

        mapping = {
            "LIMA_1": 1,
            "SANAGUSTIN": 2,
            "ARGENTINA": 3,
        }

        return mapping.get(sede, "")
    
    
    ##
    def _build_ambitos_rows_from_gemini_results(self, gemini_results: list[dict]) -> list[dict]:
        rows = []
        added = set()

        for provider in gemini_results:
            proveedor_email = str(provider.get("proveedor_email") or "").strip().lower()
            proveedor_ruc = self._normalize_ruc(provider.get("proveedor_ruc"))

            if not proveedor_email or not proveedor_ruc:
                continue

            key = (proveedor_email, proveedor_ruc)

            if key in added:
                continue

            added.add(key)

            rows.append({
                "Email": proveedor_email,
                "Empresa": proveedor_ruc,
                "Todos los negocios": False,
                "Todas las sedes": False,
                "Sedes Nuevas": "",  # TODO: definir numero de sede segun logica de negocio
                "Sedes Eliminadas": "",
                "Estado": "",
                "Comentario": "",
            })

        return rows


    def _match_detected_client(self, detected: dict, clients_index: dict, input_clientes: str | None = None) -> dict:
        search_fields = [
            ("grupo_economico", detected.get("grupo_economico")),
            ("cliente_canonico_sugerido", detected.get("cliente_canonico_sugerido")),
            ("cliente_input", detected.get("cliente_input")),
            ("input_clientes", input_clientes),

        ]

        for field_name, value in search_fields:
            result = self._match_text_against_clients(value, clients_index)

            if result["ok"]:
                result["match_field"] = field_name
                result["match_value"] = value
                return result

        return {
            "ok": False,
            "client": None,
            "score": 0,
            "match_field": None,
            "match_value": None,
        }

    def _match_text_against_clients(self, value, clients_index: dict) -> dict:
        query = self._normalize_text(value)

        if not query:
            return {
                "ok": False,
                "client": None,
                "score": 0,
            }

        client_names = clients_index["names"]

        if not client_names:
            return {
                "ok": False,
                "client": None,
                "score": 0,
            }

        match = process.extractOne(
            query,
            client_names,
            scorer=fuzz.token_set_ratio
        )

        if not match:
            return {
                "ok": False,
                "client": None,
                "score": 0,
            }

        matched_name, score, _ = match

        if score < self.MIN_SCORE_CLIENT_MATCH:
            return {
                "ok": False,
                "client": None,
                "score": score,
            }

        return {
            "ok": True,
            "client": clients_index["by_name"][matched_name],
            "score": score,
        }

    def _assign_groups(self, matched_relations: list[dict]) -> dict:
        grouped_clients = {}
        group_counter = 1

        for relation in matched_relations:
            client = relation["cliente_bd"]
            client_ruc = self._normalize_ruc(client.get("document_number"))

            if not client_ruc:
                continue

            if client_ruc not in grouped_clients:
                grouped_clients[client_ruc] = {
                    "grupo": group_counter,
                    "client": client,
                    "relations": [],
                }
                group_counter += 1

            grouped_clients[client_ruc]["relations"].append(relation)

        return grouped_clients

    def _build_relacion_nueva_rows(self, grouped_clients: dict, persons_by_ruc: dict) -> list[dict]:
        rows = []
        added = set()

        for _, group_data in grouped_clients.items():
            grupo = group_data["grupo"]

            for relation in group_data["relations"]:
                proveedor_nombre = relation["proveedor_nombre"]
                proveedor_ruc = relation["proveedor_ruc"]

                if not proveedor_ruc:
                    continue

                key = (grupo, proveedor_ruc)

                if key in added:
                    continue

                added.add(key)

                # usar nombre de BD si existe, si no usar el del Excel
                nombre_final = persons_by_ruc.get(proveedor_ruc) or proveedor_nombre

                rows.append({
                    "Grupo": grupo,
                    "Razon Social": nombre_final,
                    "RUC": proveedor_ruc,
                })

        return rows



    def _build_entidades_rows(self, grouped_clients: dict, persons_by_ruc: dict) -> list[dict]:
        rows = []
        added_providers = set()
        added_clients = set()

        for _, group_data in grouped_clients.items():
            grupo = group_data["grupo"]
            client = group_data["client"]

            for relation in group_data["relations"]:
                proveedor_nombre = relation["proveedor_nombre"]
                proveedor_ruc = relation["proveedor_ruc"]

                if proveedor_ruc not in added_providers:
                    added_providers.add(proveedor_ruc)

                    # usar nombre de BD si existe, si no usar el del Excel
                    nombre_final = persons_by_ruc.get(proveedor_ruc) or proveedor_nombre

                    rows.append({
                        "Razon Social": nombre_final,
                        "Apellidos y nombres": nombre_final,
                        "Tipo": "RUC",
                        "RUC": proveedor_ruc,
                        "Email": "",
                        "Telefono": "",
                        "Direccion": "",
                        "Tipo Usuario": "PROVEEDOR",
                        "Tipo de negocio Nuevo": "",  # TODO: definir logica de tipo de negocio nuevo
                        "Tipo de negocio Eliminar": "",
                        "Relacion Nueva": "",
                        "Relacion Eliminada": "",
                        "Estado": "",
                        "Comentario": "",
                    })

            client_ruc = self._normalize_ruc(client.get("document_number"))
            client_name = client.get("name")

            if client_ruc and client_ruc not in added_clients:
                added_clients.add(client_ruc)

                rows.append({
                    "Razon Social": client_name,
                    "Apellidos y nombres": client_name,
                    "Tipo": "RUC",
                    "RUC": client_ruc,
                    "Email": "",
                    "Telefono": "",
                    "Direccion": "",
                    "Tipo Usuario": "CLIENTE",
                    "Tipo de negocio Nuevo": "",
                    "Tipo de negocio Eliminar": "",
                    "Relacion Nueva": grupo,
                    "Relacion Eliminada": "",
                    "Estado": "",
                    "Comentario": "",
                })

        return rows
    def _build_ambitos_rows(self, grouped_clients: dict) -> list[dict]:
        rows = []
        added = set()

        for _, group_data in grouped_clients.items():
            for relation in group_data["relations"]:
                proveedor_ruc = relation["proveedor_ruc"]
                proveedor_email = relation.get("proveedor_email")

                if not proveedor_email:
                    continue

                key = (proveedor_email, proveedor_ruc)

                if key in added:
                    continue

                added.add(key)

                rows.append({
                    "Email": proveedor_email,
                    "Empresa": proveedor_ruc,
                    "Todos los negocios": False,
                    "Todas las sedes": False,
                    "Sedes Nuevas": "",  # TODO: definir numero de sede segun logica de negocio
                    "Sedes Eliminadas": "",
                    "Estado": "",
                    "Comentario": "",
                })

        return rows

    def _normalize_text(self, value) -> str:
        if pd.isna(value):
            return ""

        text = str(value).strip().upper()
        text = " ".join(text.split())
        return text

    def _normalize_ruc(self, value) -> str:
        if pd.isna(value):
            return ""

        text = str(value).strip()
        digits = "".join(ch for ch in text if ch.isdigit())
        return digits

