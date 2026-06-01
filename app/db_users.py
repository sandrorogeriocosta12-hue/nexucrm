"""
Persistência de usuários via PostgreSQL.
Usado por api_main.py no lugar de mock_users (dict em memória).
"""
import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager

_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vexus:vexus_password_123@localhost/vexus_crm"
)

_SCHEMA = "nexus"


@contextmanager
def _conn():
    con = psycopg2.connect(_DB_URL)
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db():
    """Cria schema e tabelas se não existirem."""
    con = psycopg2.connect(_DB_URL)
    try:
        con.autocommit = True
        cur = con.cursor()
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {_SCHEMA}")
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {_SCHEMA}.users (
                id          SERIAL PRIMARY KEY,
                email       VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                name        VARCHAR(255) NOT NULL DEFAULT '',
                company     VARCHAR(255) DEFAULT '',
                phone       VARCHAR(50)  DEFAULT '',
                plan        VARCHAR(50)  DEFAULT 'trial',
                role        VARCHAR(50)  DEFAULT 'user',
                is_active   BOOLEAN      DEFAULT TRUE,
                email_verified BOOLEAN  DEFAULT FALSE,
                company_id  VARCHAR(100) DEFAULT '',
                created_at  TIMESTAMP    DEFAULT NOW()
            )
        """)
    finally:
        con.close()


def get_user(email: str) -> dict | None:
    with _conn() as con:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM {_SCHEMA}.users WHERE email = %s", (email,))
        row = cur.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    with _conn() as con:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"SELECT * FROM {_SCHEMA}.users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def create_user(email: str, password_hash: str, name: str = "",
                company: str = "", phone: str = "", role: str = "user",
                ramo_empresa: str = "", objetivo_ia: str = "",
                tom_de_voz: str = "", plan: str = "trial") -> dict:
    with _conn() as con:
        cur = con.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(f"""
            INSERT INTO {_SCHEMA}.users
                (email, password_hash, name, company, phone, role,
                 ramo_empresa, objetivo_ia, tom_de_voz, plan,
                 trial_ends_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() + INTERVAL '15 days')
            RETURNING *
        """, (email, password_hash, name, company, phone, role,
              ramo_empresa, objetivo_ia, tom_de_voz, plan))
        row = cur.fetchone()
        return dict(row)


def update_password(email: str, new_hash: str) -> bool:
    with _conn() as con:
        cur = con.cursor()
        cur.execute(
            f"UPDATE {_SCHEMA}.users SET password_hash = %s WHERE email = %s",
            (new_hash, email)
        )
        return cur.rowcount > 0


def user_exists(email: str) -> bool:
    with _conn() as con:
        cur = con.cursor()
        cur.execute(f"SELECT 1 FROM {_SCHEMA}.users WHERE email = %s", (email,))
        return cur.fetchone() is not None


def count_users() -> int:
    with _conn() as con:
        cur = con.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {_SCHEMA}.users")
        return cur.fetchone()[0]
