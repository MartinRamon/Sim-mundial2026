"""Carga de configuracion desde variables de entorno y/o fichero .env
(sin dependencias externas)."""

import os

_ROOT = os.path.dirname(os.path.dirname(__file__))


def _load_env_file():
    path = os.path.join(_ROOT, ".env")
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            os.environ.setdefault(key, val)


_load_env_file()

_DEFAULT_AUTH_SECRET = "dev-secret-insecure-change-me-please"
_DEFAULT_ADMIN_PASSWORD = "admin1234"

DB_PATH = os.environ.get("DB_PATH", os.path.join(_ROOT, "porra.db"))
AUTH_SECRET = os.environ.get("AUTH_SECRET", _DEFAULT_AUTH_SECRET)
ADMIN_NAME = os.environ.get("ADMIN_NAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", _DEFAULT_ADMIN_PASSWORD)
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))

# Base de datos Turso (libSQL) para el despliegue en la nube.
# Si TURSO_DATABASE_URL esta definida, la app usa Turso en lugar del fichero
# SQLite local; asi los datos persisten aunque el hosting reinicie el contenedor.
# En local, deja estas variables vacias y se usa SQLite (DB_PATH) como siempre.
TURSO_DATABASE_URL = os.environ.get("TURSO_DATABASE_URL", "").strip()
TURSO_AUTH_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "").strip()

# Avisos de seguridad: detecta si seguimos con los valores por defecto (inseguros).
USING_DEFAULT_SECRET = AUTH_SECRET == _DEFAULT_AUTH_SECRET
USING_DEFAULT_ADMIN_PW = ADMIN_PASSWORD == _DEFAULT_ADMIN_PASSWORD
