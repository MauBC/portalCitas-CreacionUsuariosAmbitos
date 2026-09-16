from contextlib import closing

import psycopg2

from app.config.settings import settings


class PostgresClient:
    def __init__(
        self,
        country_code: str | None = None,
        database_name: str | None = None,
    ):
        self.country_code = str(
            country_code or ""
        ).strip().upper()

        self.database_name = (
            str(
                database_name or ""
            ).strip()
            or settings.get_db_name(
                self.country_code
            )
        )

        try:
            connect_timeout = int(settings.DB_CONNECT_TIMEOUT)
        except (TypeError, ValueError):
            raise ValueError("DB_CONNECT_TIMEOUT debe ser un entero de al menos 2 segundos.") from None
        if connect_timeout < 2:
            raise ValueError("DB_CONNECT_TIMEOUT debe ser un entero de al menos 2 segundos.")

        self.conn_params = {
            "connect_timeout": connect_timeout,
            "host":
                settings.DB_HOST,
            "port":
                settings.DB_PORT,
            "dbname":
                self.database_name,
            "user":
                settings.DB_USER,
            "password":
                settings.DB_PASSWORD,
            "sslmode":
                settings.DB_SSLMODE,
        }

    def get_connection(self):
        """Return a new connection; callers are responsible for closing it."""
        return psycopg2.connect(
            **self.conn_params
        )

    def fetch_all(
        self,
        query: str,
        params: tuple | None = None,
    ):
        # The psycopg2 transaction context commits/rolls back but does not close.
        with closing(self.get_connection()) as conn, conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    params or (),
                )

                columns = [
                    desc[0]
                    for desc in cur.description
                ]

                rows = cur.fetchall()

                return [
                    dict(
                        zip(
                            columns,
                            row,
                        )
                    )
                    for row in rows
                ]
