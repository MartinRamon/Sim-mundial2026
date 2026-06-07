"""Acceso a la base de datos SQLite (modulo sqlite3 de la biblioteca estandar)."""

import json
import sqlite3

from . import config


def get_conn():
    """Devuelve una conexion a la base de datos.

    - Si hay configurada una BD Turso (libSQL) -> conexion remota (produccion).
    - En caso contrario -> fichero SQLite local (desarrollo), como siempre.
    """
    if config.TURSO_DATABASE_URL:
        return _turso_connect()
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ---------------------------------------------------------------------------
# Adaptador Turso / libSQL
#
# libsql_client trabaja sobre HTTP con autocommit por sentencia y devuelve un
# ResultSet cuyas filas ya permiten acceso por nombre de columna (row["col"]),
# igual que sqlite3.Row. Estas dos clases envuelven ese cliente para que el
# resto de db.py siga usando la misma API que sqlite3 (conn.execute(...).fetchone(),
# cur.lastrowid, conn.commit(), conn.close(), conn.executescript(...)).
# La dependencia 'libsql-client' solo se importa aqui, asi que en local (SQLite)
# no hace falta instalar nada.
# ---------------------------------------------------------------------------

def _turso_url():
    """Normaliza la URL de Turso a transporte HTTP(S).

    libsql_client mapea el esquema "libsql://" a WebSocket (wss://), cuyo
    handshake falla con 400 en algunos entornos (p. ej. Render). Forzamos el
    transporte HTTP(S), mas compatible, que usa el mismo host de Turso.
    """
    url = config.TURSO_DATABASE_URL
    if url.startswith("libsql://"):
        return "https://" + url[len("libsql://"):]
    if url.startswith("wss://"):
        return "https://" + url[len("wss://"):]
    if url.startswith("ws://"):
        return "http://" + url[len("ws://"):]
    return url


def _turso_connect():
    import libsql_client  # dependencia necesaria solo en produccion (Turso)

    client = libsql_client.create_client_sync(
        url=_turso_url(),
        auth_token=config.TURSO_AUTH_TOKEN or None,
    )
    return _TursoConn(client)


class _TursoCursor:
    """Imita el cursor de sqlite3 sobre un ResultSet de libsql_client."""

    def __init__(self, result_set):
        self._rs = result_set
        self._rows = list(result_set.rows) if result_set is not None else []
        self._idx = 0

    @property
    def lastrowid(self):
        return getattr(self._rs, "last_insert_rowid", None) if self._rs is not None else None

    @property
    def rowcount(self):
        return getattr(self._rs, "rows_affected", -1) if self._rs is not None else -1

    def fetchone(self):
        if self._idx < len(self._rows):
            row = self._rows[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self):
        rows = self._rows[self._idx:]
        self._idx = len(self._rows)
        return rows

    def __iter__(self):
        return iter(self.fetchall())


class _TursoConn:
    """Conexion compatible-sqlite3 (el subconjunto que usa db.py) contra Turso."""

    def __init__(self, client):
        self._client = client

    def execute(self, sql, params=()):
        args = list(params) if params else []
        rs = self._client.execute(sql, args) if args else self._client.execute(sql)
        return _TursoCursor(rs)

    def executescript(self, script):
        for stmt in script.split(";"):
            stmt = stmt.strip()
            if stmt:
                self._client.execute(stmt)
        return _TursoCursor(None)

    def commit(self):
        pass  # autocommit por sentencia en modo HTTP

    def rollback(self):
        pass

    def close(self):
        try:
            self._client.close()
        except Exception:
            pass


def init_db():
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS predictions (
                user_id INTEGER PRIMARY KEY,
                data TEXT NOT NULL DEFAULT '{}',
                submitted INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS results (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO results (id, data) VALUES ('real', ?)",
            (json.dumps({"groups": {}, "knockout": {}}),),
        )
        conn.commit()
    finally:
        conn.close()


# ----- Usuarios -----

def get_user_by_name(name):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM users WHERE name = ?", (name,)).fetchone()
    finally:
        conn.close()


def get_user_by_id(uid):
    conn = get_conn()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    finally:
        conn.close()


def create_user(name, password_hash, is_admin=False):
    conn = get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, password_hash, is_admin) VALUES (?, ?, ?)",
            (name, password_hash, 1 if is_admin else 0),
        )
        uid = cur.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO predictions (user_id, data) VALUES (?, ?)",
            (uid, json.dumps({"groups": {}, "knockout": {}})),
        )
        conn.commit()
        return uid
    finally:
        conn.close()


def upsert_admin(name, password_hash):
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET password_hash = ?, is_admin = 1 WHERE name = ?",
                (password_hash, name),
            )
        else:
            conn.execute(
                "INSERT INTO users (name, password_hash, is_admin) VALUES (?, ?, 1)",
                (name, password_hash),
            )
        conn.commit()
    finally:
        conn.close()


# ----- Predicciones -----

def get_prediction(user_id):
    conn = get_conn()
    try:
        return conn.execute(
            "SELECT * FROM predictions WHERE user_id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def save_prediction(user_id, data_json, submitted=None):
    conn = get_conn()
    try:
        exists = conn.execute(
            "SELECT user_id FROM predictions WHERE user_id = ?", (user_id,)
        ).fetchone()
        if exists:
            if submitted is None:
                conn.execute(
                    "UPDATE predictions SET data = ?, updated_at = datetime('now') WHERE user_id = ?",
                    (data_json, user_id),
                )
            else:
                conn.execute(
                    "UPDATE predictions SET data = ?, submitted = ?, updated_at = datetime('now') WHERE user_id = ?",
                    (data_json, 1 if submitted else 0, user_id),
                )
        else:
            conn.execute(
                "INSERT INTO predictions (user_id, data, submitted) VALUES (?, ?, ?)",
                (user_id, data_json, 1 if submitted else 0),
            )
        conn.commit()
    finally:
        conn.close()


def all_user_predictions():
    conn = get_conn()
    try:
        return conn.execute(
            """
            SELECT u.name AS name, p.data AS data, p.submitted AS submitted
            FROM users u LEFT JOIN predictions p ON p.user_id = u.id
            WHERE u.is_admin = 0
            """
        ).fetchall()
    finally:
        conn.close()


def get_prediction_by_name(name):
    conn = get_conn()
    try:
        return conn.execute(
            """
            SELECT u.name AS name, u.is_admin AS is_admin,
                   p.data AS data, p.submitted AS submitted
            FROM users u LEFT JOIN predictions p ON p.user_id = u.id
            WHERE u.name = ?
            """,
            (name,),
        ).fetchone()
    finally:
        conn.close()


# ----- Resultados reales -----

def get_results():
    conn = get_conn()
    try:
        row = conn.execute("SELECT data FROM results WHERE id = 'real'").fetchone()
        return row["data"] if row else "{}"
    finally:
        conn.close()


def save_results(data_json):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO results (id, data, updated_at) VALUES ('real', ?, datetime('now')) "
            "ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = datetime('now')",
            (data_json,),
        )
        conn.commit()
    finally:
        conn.close()


# ----- Ajustes (clave/valor) -----

def get_setting(key, default=""):
    conn = get_conn()
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default
    finally:
        conn.close()


def set_setting(key, value):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = datetime('now')",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()
