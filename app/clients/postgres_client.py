import psycopg2
from app.config.settings import settings


class PostgresClient:
    def __init__(self):
        self.conn_params = {
            "host": settings.DB_HOST,
            "port": settings.DB_PORT,
            "dbname": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "sslmode": settings.DB_SSLMODE,
        }

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def fetch_all(self, query: str, params: tuple | None = None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                return [dict(zip(columns, row)) for row in rows]

    def fetch_one(self, query: str, params: tuple | None = None):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                row = cur.fetchone()

                if row is None:
                    return None

                columns = [desc[0] for desc in cur.description]
                return dict(zip(columns, row))