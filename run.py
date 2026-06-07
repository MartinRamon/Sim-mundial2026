#!/usr/bin/env python3
"""Punto de entrada de la Porra del Mundial 2026.

Uso:
    python run.py setup    # crea la base de datos y el usuario admin
    python run.py          # arranca el servidor web
"""

import sys

from porra import auth, config, db
from porra.server import serve


def setup():
    db.init_db()
    db.upsert_admin(config.ADMIN_NAME, auth.hash_password(config.ADMIN_PASSWORD))
    print("Base de datos lista en: %s" % config.DB_PATH)
    print('Usuario admin "%s" creado/actualizado.' % config.ADMIN_NAME)
    print("Ahora ejecuta:  python run.py")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup()
    else:
        db.init_db()
        serve()


if __name__ == "__main__":
    main()
