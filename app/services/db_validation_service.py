from app.clients.postgres_client import (
    PostgresClient,
)


class DbValidationService:
    def __init__(
        self,
        db: PostgresClient | None = None,
        country_code: str | None = None,
    ):
        self.country_code = str(
            country_code or ""
        ).strip().upper()

        self.db = (
            db
            or PostgresClient(
                country_code=
                    self.country_code
            )
        )

    @property
    def database_name(self) -> str:
        return str(
            getattr(
                self.db,
                "database_name",
                "",
            )
            or ""
        )

    @staticmethod
    def _unique_normalized(
        values: list[str],
        transform,
    ) -> list[str]:
        result = []
        seen = set()

        for value in values:
            normalized = transform(
                value
            )

            if (
                not normalized
                or normalized in seen
            ):
                continue

            seen.add(
                normalized
            )
            result.append(
                normalized
            )

        return result

    def get_existing_emails(
        self,
        emails: list[str],
        chunk_size: int = 500,
    ) -> set[str]:
        normalized = (
            self._unique_normalized(
                emails,
                lambda value:
                    str(
                        value or ""
                    )
                    .strip()
                    .lower(),
            )
        )

        if not normalized:
            return set()

        existing = set()

        query = """
            SELECT LOWER("Email") AS email
            FROM "User"
            WHERE LOWER("Email") = ANY(%s)
        """

        for start in range(
            0,
            len(normalized),
            chunk_size,
        ):
            batch = normalized[
                start:
                start + chunk_size
            ]

            rows = self.db.fetch_all(
                query,
                (batch,),
            )

            existing.update(
                str(
                    row.get("email")
                    or ""
                )
                .strip()
                .lower()
                for row in rows
                if row.get("email")
            )

        return existing

    def get_persons_by_names(
        self,
        names: list[str],
    ) -> list[dict]:
        normalized_names = (
            self._unique_normalized(
                names,
                lambda value:
                    str(
                        value or ""
                    )
                    .strip()
                    .upper(),
            )
        )

        if not normalized_names:
            return []

        query = """
            SELECT
                p."Id" AS "ClientId",
                p."Name",
                p."DocumentNumber"
            FROM "Person" p
            WHERE p."State" = 1
              AND UPPER(TRIM(p."Name")) = ANY(%s)
            ORDER BY p."Name";
        """

        rows = self.db.fetch_all(
            query,
            (normalized_names,),
        )

        return [
            {
                "client_id":
                    row.get(
                        "ClientId"
                    ),
                "name":
                    row.get(
                        "Name"
                    ),
                "document_number":
                    row.get(
                        "DocumentNumber"
                    ),
            }
            for row in rows
        ]

    def get_distinct_clients(
        self,
    ) -> list[dict]:
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

        rows = self.db.fetch_all(
            query
        )

        return [
            {
                "client_id":
                    row.get(
                        "ClientId"
                    ),
                "name":
                    row.get(
                        "Name"
                    ),
                "document_number":
                    row.get(
                        "DocumentNumber"
                    ),
            }
            for row in rows
        ]

    def get_distinct_suppliers(
        self,
    ) -> list[dict]:
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

        rows = self.db.fetch_all(
            query
        )

        return [
            {
                "supplier_id":
                    row.get(
                        "SupplierId"
                    ),
                "name":
                    row.get(
                        "Name"
                    ),
                "document_number":
                    row.get(
                        "DocumentNumber"
                    ),
            }
            for row in rows
        ]
