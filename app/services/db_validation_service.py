from app.clients.postgres_client import PostgresClient


class DbValidationService:
    def __init__(self):
        self.db = PostgresClient()

    def get_existing_emails(self, emails: list[str], chunk_size: int = 500) -> set[str]:
        normalized = []
        seen = set()

        for email in emails:
            if email is None:
                continue

            value = str(email).strip().lower()
            if not value:
                continue

            if value not in seen:
                seen.add(value)
                normalized.append(value)

        if not normalized:
            return set()

        existing = set()

        for i in range(0, len(normalized), chunk_size):
            batch = normalized[i:i + chunk_size]

            query = """
                SELECT LOWER("Email") AS email
                FROM "User"
                WHERE LOWER("Email") = ANY(%s)
            """

            rows = self.db.fetch_all(query, (batch,))

            for row in rows:
                value = row.get("email")
                if value:
                    existing.add(str(value).strip().lower())

        return existing


    def get_persons_by_names(self, names: list[str]) -> list[dict]:
        """
        Busca entidades directamente en Person por nombre.

        IMPORTANTE:
        Este metodo se utiliza para FASE 3.

        Un cliente puede existir en Person pero todavia no aparecer
        como ClientId en ClientSupplier porque aun no tiene proveedores
        relacionados.

        Por eso NO debemos depender de ClientSupplier para determinar
        si un cliente configurado existe antes de crear nuevas relaciones.
        """

        if not names:
            return []

        normalized_names = sorted({
            str(name).strip().upper()
            for name in names
            if str(name).strip()
        })

        escaped_names = [
            name.replace("'", "''")
            for name in normalized_names
        ]

        in_clause = ", ".join(
            f"'{name}'"
            for name in escaped_names
        )

        query = f"""
            SELECT
                p."Id" AS "ClientId",
                p."Name",
                p."DocumentNumber"
            FROM "Person" p
            WHERE p."State" = 1
              AND UPPER(TRIM(p."Name")) IN ({in_clause})
            ORDER BY p."Name";
        """

        rows = self.db.fetch_all(query)

        return [
            {
                "client_id": row.get("ClientId"),
                "name": row.get("Name"),
                "document_number": row.get("DocumentNumber"),
            }
            for row in rows
        ]
    def get_distinct_clients(self) -> list[dict]:
        """
        Obtiene clientes reales a partir de ClientSupplier.

        Regla confirmada:
        - ClientSupplier.ClientId   -> CLIENTE
        - ClientSupplier.SupplierId -> PROVEEDOR

        PersonBusinessType NO se utiliza para determinar este rol.
        """

        query = """
            SELECT DISTINCT
                cs."ClientId",
                p."Name",
                p."DocumentNumber"
            FROM "ClientSupplier" cs
            JOIN "Person" p
                ON p."Id" = cs."ClientId"
            WHERE p."State" = 1
            ORDER BY p."Name";
        """

        rows = self.db.fetch_all(query)

        clients = []

        for row in rows:
            clients.append({
                "client_id": row.get("ClientId"),
                "name": row.get("Name"),
                "document_number": row.get("DocumentNumber"),
            })

        return clients
    
    def get_distinct_suppliers(self) -> list[dict]:
        """
        Obtiene proveedores reales a partir de ClientSupplier.

        Regla confirmada:
        ClientSupplier.SupplierId -> PROVEEDOR
        """

        query = """
            SELECT DISTINCT
                cs."SupplierId",
                p."Name",
                p."DocumentNumber"
            FROM "ClientSupplier" cs
            JOIN "Person" p
                ON p."Id" = cs."SupplierId"
            WHERE p."State" = 1
            ORDER BY p."Name";
        """

        rows = self.db.fetch_all(query)

        suppliers = []

        for row in rows:
            suppliers.append({
                "supplier_id": row.get("SupplierId"),
                "name": row.get("Name"),
                "document_number": row.get("DocumentNumber"),
            })

        return suppliers


    def get_persons_with_roles(self) -> list[dict]:
        """
        Detecta si una persona/empresa participa como:

        - CLIENTE
        - PROVEEDOR
        - CLIENTE y PROVEEDOR

        Se utilizan EXISTS para evitar filas duplicadas cuando
        una empresa tiene muchas relaciones ClientSupplier.

        IMPORTANTE:
        TRANSPORTISTA / CONDUCTOR / EMPLEADO todavia no se
        determinan aqui porque aun no conocemos su relacion
        exacta dentro del modelo de datos.
        """

        query = """
            SELECT
                p."Id" AS person_id,
                p."Name" AS name,
                p."DocumentNumber" AS document_number,

                EXISTS (
                    SELECT 1
                    FROM "ClientSupplier" cs
                    WHERE cs."ClientId" = p."Id"
                ) AS is_client,

                EXISTS (
                    SELECT 1
                    FROM "ClientSupplier" cs
                    WHERE cs."SupplierId" = p."Id"
                ) AS is_supplier

            FROM "Person" p

            WHERE p."State" = 1

              AND (
                    EXISTS (
                        SELECT 1
                        FROM "ClientSupplier" cs
                        WHERE cs."ClientId" = p."Id"
                    )

                    OR

                    EXISTS (
                        SELECT 1
                        FROM "ClientSupplier" cs
                        WHERE cs."SupplierId" = p."Id"
                    )
              )

            ORDER BY p."Name";
        """

        rows = self.db.fetch_all(query)

        result = []

        for row in rows:

            roles = []

            if row.get("is_client"):
                roles.append("CLIENTE")

            if row.get("is_supplier"):
                roles.append("PROVEEDOR")

            result.append({
                "person_id": row.get("person_id"),
                "name": row.get("name"),
                "document_number": row.get("document_number"),
                "is_client": bool(row.get("is_client")),
                "is_supplier": bool(row.get("is_supplier")),
                "roles": roles,
            })

        return result

    def get_persons_by_document_numbers(self, document_numbers: list[str]) -> dict:
        clean_docs = []

        for value in document_numbers:
            if not value:
                continue

            doc = "".join(ch for ch in str(value) if ch.isdigit())

            if doc and doc not in clean_docs:
                clean_docs.append(doc)

        if not clean_docs:
            return {}

        query = """
            SELECT
                "DocumentNumber",
                "Name"
            FROM "Person"
            WHERE "DocumentNumber" = ANY(%s)
        """

        rows = self.db.fetch_all(query, (clean_docs,))

        result = {}
        for row in rows:
            doc = str(row.get("DocumentNumber") or "").strip()
            name = str(row.get("Name") or "").strip()

            if doc:
                result[doc] = name

        return result



