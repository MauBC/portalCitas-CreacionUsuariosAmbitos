import re
import unicodedata

import pandas as pd
from rapidfuzz import process, fuzz

from app.services.client_assignment_service import ClientAssignmentService
from app.config.portal_template_config import COUNTRY_TEMPLATE_CONFIG
from app.services.ambitos_config_service import AmbitosConfigService


class AmbitosBuilderService:
    MIN_SCORE_CLIENT_MATCH = 90

    def __init__(self):
        self.client_assignment = ClientAssignmentService()
        self.ambitos_config = AmbitosConfigService()


    def build_from_dataframe(
        self,
        df: pd.DataFrame,
        db_clients: list[dict],
        persons_by_ruc: dict | None = None,
    ) -> dict:
        """
        Construye la informacion de ambitos desde un DataFrame
        limpio y validado para el pais de la ejecucion.
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

            # FASE 3 procesa relaciones de proveedores.

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
            )

            if not proveedor_ruc:
                proveedor_ruc = self._normalize_ruc(
                    row.get("ruc_proveedor")
                )

            cliente_original = str(
                row.get("nombre_cliente")
                or ""
            ).strip()

            item_id = str(
                row.get("_item_id")
                or ""
            ).strip()

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
                    "_item_id": item_id,
                    "email": email,
                    "proveedor_nombre": "",
                    "proveedor_ruc": proveedor_ruc,
                    "cliente_original": cliente_original,
                    "cliente_input": cliente_resuelto,
                    "cliente_sugerido": "",
                    "mensaje": "Proveedor sin nombre",
                    "match_score": 0,
                })
                continue

            if not proveedor_ruc:
                no_match_rows.append({
                    "_item_id": item_id,
                    "email": email,
                    "proveedor_nombre": proveedor_nombre,
                    "proveedor_ruc": "",
                    "cliente_original": cliente_original,
                    "cliente_input": cliente_resuelto,
                    "cliente_sugerido": "",
                    "mensaje": "Proveedor sin identificador tributario",
                    "match_score": 0,
                })
                continue

            if not cliente_resuelto:
                no_match_rows.append({
                    "_item_id": item_id,
                    "email": email,
                    "proveedor_nombre": proveedor_nombre,
                    "proveedor_ruc": proveedor_ruc,
                    "cliente_original": cliente_original,
                    "cliente_input": "",
                    "cliente_sugerido": "",
                    "mensaje": "No se pudo resolver cliente",
                    "match_score": 0,
                })
                continue

            # El cliente canonico debe existir en PostgreSQL.

            match_result = self._match_text_against_clients(
                cliente_resuelto,
                clients_index,
            )

            if not match_result["ok"]:

                no_match_rows.append({
                    "_item_id": item_id,
                    "email": email,
                    "proveedor_nombre": proveedor_nombre,
                    "proveedor_ruc": proveedor_ruc,
                    "cliente_original": cliente_original,
                    "cliente_input": cliente_resuelto,
                    "cliente_sugerido": "",
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

                "_item_id":
                    item_id,

                "pais":
                    pais,

                "cliente_original":
                    cliente_original,

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

        config_rows = self._build_config_rows(
            grouped_clients
        )

        return {
            "entidades": entidades_rows,
            "ambitos": ambitos_rows,
            "relacion_nueva": relacion_nueva_rows,
            "tipo_negocio_nuevo":
                config_rows["tipo_negocio_nuevo"],
            "sede_nueva":
                config_rows["sede_nueva"],
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

    def _assign_groups(
        self,
        matched_relations: list[dict],
    ) -> dict:
        grouped_clients = {}

        for relation in matched_relations:
            client = relation["cliente_bd"]

            client_ruc = self._normalize_ruc(
                client.get("document_number")
            )

            if not client_ruc:
                continue

            country = str(
                relation.get("pais")
                or "SLV"
            ).strip().upper()

            client_name = str(
                client.get("name")
                or ""
            ).strip()

            group = (
                self.ambitos_config
                .get_relation_group(
                    country,
                    client_name,
                )
            )

            if group is None:
                raise ValueError(
                    "No existe relation_group para "
                    f"{country} / {client_name}"
                )

            if client_ruc not in grouped_clients:
                grouped_clients[client_ruc] = {
                    "grupo": group,
                    "client": client,
                    "relations": [],
                }

            elif (
                grouped_clients[
                    client_ruc
                ]["grupo"]
                != group
            ):
                raise ValueError(
                    "El mismo cliente tiene grupos "
                    "de relacion inconsistentes: "
                    f"{client_name}"
                )

            grouped_clients[
                client_ruc
            ]["relations"].append(
                relation
            )

        return grouped_clients
    def _build_relacion_nueva_rows(
        self,
        grouped_clients: dict,
        persons_by_ruc: dict,
    ) -> list[dict]:
        rows = []
        added = set()

        for _, group_data in (
            grouped_clients.items()
        ):
            grupo = group_data["grupo"]

            for relation in group_data[
                "relations"
            ]:
                proveedor_nombre = (
                    relation[
                        "proveedor_nombre"
                    ]
                )

                proveedor_ruc = (
                    relation[
                        "proveedor_ruc"
                    ]
                )

                if not proveedor_ruc:
                    continue

                key = (
                    grupo,
                    proveedor_ruc,
                )

                if key in added:
                    continue

                added.add(key)

                nombre_final = (
                    persons_by_ruc.get(
                        proveedor_ruc
                    )
                    or proveedor_nombre
                )

                nombre_final = (
                    self._normalize_company_name(
                        nombre_final
                    )
                )

                rows.append({
                    "Grupo": grupo,
                    "Razon Social":
                        nombre_final,
                    "RUC": proveedor_ruc,
                })

        return rows
    def _build_entidades_rows(
        self,
        grouped_clients: dict,
        persons_by_ruc: dict,
    ) -> list[dict]:
        rows = []
        added_providers = set()
        added_clients = set()

        country_code = ""

        for group_data in grouped_clients.values():
            for relation in group_data.get(
                "relations",
                [],
            ):
                country_code = str(
                    relation.get("pais")
                    or ""
                ).strip().upper()

                if country_code:
                    break

            if country_code:
                break

        if not country_code:
            country_code = "SLV"

        document_type_by_country = {
            "SLV": "NIT",
            "PER": "RUC",
        }

        document_type = (
            document_type_by_country.get(
                country_code
            )
        )

        if not document_type:
            raise ValueError(
                "No existe Tipo de documento "
                f"para pais {country_code}"
            )

        for _, group_data in (
            grouped_clients.items()
        ):
            grupo = group_data["grupo"]
            client = group_data["client"]

            for relation in group_data[
                "relations"
            ]:
                proveedor_nombre = (
                    relation[
                        "proveedor_nombre"
                    ]
                )

                proveedor_ruc = (
                    relation[
                        "proveedor_ruc"
                    ]
                )

                if (
                    proveedor_ruc
                    in added_providers
                ):
                    continue

                added_providers.add(
                    proveedor_ruc
                )

                nombre_final = (
                    persons_by_ruc.get(
                        proveedor_ruc
                    )
                    or proveedor_nombre
                )

                nombre_final = (
                    self._normalize_company_name(
                        nombre_final
                    )
                )

                rows.append({
                    "_entity_type":
                        "PROVEEDOR",
                    "Razon Social":
                        nombre_final,
                    "Apellidos y nombres":
                        nombre_final,
                    "Tipo":
                        document_type,
                    "RUC":
                        proveedor_ruc,
                    "Email": "",
                    "Telefono": "",
                    "Direccion": "",
                    "Tipo Usuario": "PROVEEDOR",
                    "Tipo de negocio Nuevo":
                        "",
                    "Tipo de negocio Eliminar":
                        "",
                    "Relacion Nueva": "",
                    "Relacion Eliminada": "",
                    "Estado": "",
                    "Comentario": "",
                })

            client_ruc = self._normalize_ruc(
                client.get(
                    "document_number"
                )
            )

            client_name = (
                self._normalize_company_name(
                    client.get("name")
                )
            )

            if (
                client_ruc
                and client_ruc
                not in added_clients
            ):
                added_clients.add(
                    client_ruc
                )

                rows.append({
                    "_entity_type":
                        "CLIENTE",
                    "Razon Social":
                        client_name,
                    "Apellidos y nombres":
                        client_name,
                    "Tipo":
                        document_type,
                    "RUC":
                        client_ruc,
                    "Email": "",
                    "Telefono": "",
                    "Direccion": "",
                    "Tipo Usuario": "CLIENTE",
                    "Tipo de negocio Nuevo":
                        "",
                    "Tipo de negocio Eliminar":
                        "",
                    "Relacion Nueva":
                        grupo,
                    "Relacion Eliminada": "",
                    "Estado": "",
                    "Comentario": "",
                })

        return rows

    def _build_ambitos_rows(
        self,
        grouped_clients: dict,
    ) -> list[dict]:
        rows = []
        added = set()

        for _, group_data in (
            grouped_clients.items()
        ):
            for relation in group_data[
                "relations"
            ]:
                proveedor_ruc = (
                    relation[
                        "proveedor_ruc"
                    ]
                )

                proveedor_email = str(
                    relation.get(
                        "proveedor_email"
                    )
                    or ""
                ).strip().lower()

                if not proveedor_email:
                    continue

                key = (
                    proveedor_email,
                    proveedor_ruc,
                )

                if key in added:
                    continue

                added.add(key)

                rows.append({
                    "Email":
                        proveedor_email,
                    "Empresa":
                        proveedor_ruc,
                    "Todos los negocios":
                        "false",
                    "Todas las sedes":
                        "false",
                    "Sedes Nuevas": "",
                    "Sedes Eliminadas": "",
                    "Estado": "",
                    "Comentario": "",
                })

        return rows
    def _build_config_rows(
        self,
        grouped_clients: dict,
    ) -> dict:

        country_code = "SLV"

        # Intentar obtener el pais desde las relaciones.
        for group_data in grouped_clients.values():

            relations = group_data.get(
                "relations",
                [],
            )

            if not relations:
                continue

            relation_country = str(
                relations[0].get("pais")
                or ""
            ).strip().upper()

            if relation_country:
                country_code = relation_country
                break

        tipo_negocio_rows = (
            self.ambitos_config
            .get_tipo_negocio_rows()
        )

        sede_rows = (
            self.ambitos_config
            .get_sede_rows(
                country_code
            )
        )

        return {
            "tipo_negocio_nuevo":
                tipo_negocio_rows,
            "sede_nueva":
                sede_rows,
        }

    def _normalize_company_name(
        self,
        value,
    ) -> str:
        if value is None:
            return ""

        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass

        text = str(value).strip().upper()

        text = unicodedata.normalize(
            "NFC",
            text,
        )

        text = re.sub(
            r"[^0-9A-ZÁÉÍÓÚÜÑ&.,()/'\- ]+",
            " ",
            text,
        )

        text = " ".join(
            text.split()
        )

        return text

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

