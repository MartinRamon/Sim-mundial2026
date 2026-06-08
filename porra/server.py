"""Servidor web en Python puro (http.server) para la porra del Mundial 2026."""

import json
import os
from datetime import datetime
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import auth, config, db, gating, views
from . import wc_data as D
from .bracket import ANNEX_C
from .history import ranking_history
from .scoring import compute_score
from .stats import compute_stats
from .validate import parse_prediction, sanitize_prediction

_STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
COOKIE_NAME = "porra_session"

_MIME = {".css": "text/css", ".js": "application/javascript", ".json": "application/json",
         ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon",
         ".html": "text/html", ".webp": "image/webp", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


def _bootstrap_data():
    return {
        "teams": {c: {"name": v[0], "emoji": v[2], "iso": v[1]} for c, v in D.TEAMS.items()},
        "groups": D.GROUPS,
        "groupLetters": D.GROUP_LETTERS,
        "groupMatches": D.GROUP_MATCHES,
        "knockoutMatches": D.KNOCKOUT_MATCHES,
        "thirdSlotToMatch": D.THIRD_SLOT_TO_MATCH,
        "roundLabels": D.ROUND_LABELS,
        "roundOrder": D.ROUND_ORDER,
        "annexC": ANNEX_C,
        "homeTeam": D.HOME_TEAM,
        "players": [{"name": n, "team": t} for n, t in D.STAR_PLAYERS],
    }


_BOOTSTRAP_JSON = None


def bootstrap_json():
    global _BOOTSTRAP_JSON
    if _BOOTSTRAP_JSON is None:
        _BOOTSTRAP_JSON = json.dumps(_bootstrap_data(), ensure_ascii=False)
    return _BOOTSTRAP_JSON


class Handler(BaseHTTPRequestHandler):
    server_version = "PorraMundial/1.0"

    def log_message(self, fmt, *args):  # silenciar logs ruidosos
        pass

    # ---------- helpers ----------
    def _user(self):
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        if COOKIE_NAME not in cookie:
            return None
        payload = auth.verify_token(cookie[COOKIE_NAME].value)
        if not payload:
            return None
        row = db.get_user_by_id(payload.get("sub"))
        if not row:
            return None
        return {"id": row["id"], "name": row["name"], "isAdmin": bool(row["is_admin"])}

    def _body_json(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (TypeError, ValueError):
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _send(self, code, body, ctype="text/html; charset=utf-8", set_cookie=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if set_cookie is not None:
            self.send_header("Set-Cookie", set_cookie)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, obj, set_cookie=None):
        self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8", set_cookie)

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _set_cookie(self, token, max_age=7 * 24 * 3600):
        attrs = "%s=%s; Path=/; HttpOnly; SameSite=Lax; Max-Age=%d" % (COOKIE_NAME, token, max_age)
        return attrs

    def _clear_cookie(self):
        return "%s=; Path=/; HttpOnly; Max-Age=0" % COOKIE_NAME

    # ---------- GET ----------
    def do_GET(self):
        path = urlparse(self.path).path
        if path.startswith("/static/"):
            return self._serve_static(path)
        user = self._user()

        if path == "/":
            return self._send(200, views.home_page(user))
        if path == "/login":
            if user:
                return self._redirect("/predict")
            return self._send(200, views.login_page())
        if path == "/predict":
            if not user:
                return self._redirect("/login")
            row = db.get_prediction(user["id"])
            data = parse_prediction(row["data"] if row else None)
            real = parse_prediction(db.get_results())
            score = compute_score(data, real)
            has_results = bool(real["groups"]) or bool(real["knockout"])
            return self._send(200, views.editor_page(
                user, "Mis predicciones", "/predict", "user", "/api/prediction",
                submitted=bool(row["submitted"]) if row else False,
                score=score if has_results else None))
        if path == "/admin":
            if not user:
                return self._redirect("/login")
            if not user["isAdmin"]:
                return self._redirect("/")
            return self._send(200, views.editor_page(
                user, "Panel de administracion", "/admin", "admin", "/api/admin/results",
                submitted=False, score=None, deadline=db.get_setting(gating.DEADLINE_KEY, "")))
        if path == "/ranking":
            return self._send(200, views.ranking_page(user))
        if path == "/stats":
            return self._send(200, views.stats_page(user))
        if path == "/ver":
            name = (parse_qs(urlparse(self.path).query).get("name") or [""])[0]
            return self._send(200, views.view_prediction_page(user, name))

        # ----- API GET -----
        if path == "/api/bootstrap":
            return self._send(200, bootstrap_json(), "application/json; charset=utf-8")
        if path == "/api/prediction":
            if not user:
                return self._json(401, {"error": "No autenticado."})
            row = db.get_prediction(user["id"])
            real = parse_prediction(db.get_results())
            state = gating.lock_state(real=real)
            return self._json(200, {"data": parse_prediction(row["data"] if row else None),
                                    "submitted": bool(row["submitted"]) if row else False,
                                    "locks": state,
                                    "realGroups": real["groups"] if state["knockoutOpen"] else {}})
        if path == "/api/user-prediction":
            return self._user_prediction(parse_qs(urlparse(self.path).query))
        if path == "/api/admin/results":
            if not user or not user["isAdmin"]:
                return self._json(403, {"error": "Solo administradores."})
            return self._json(200, {"data": parse_prediction(db.get_results())})
        if path == "/api/admin/users":
            if not user or not user["isAdmin"]:
                return self._json(403, {"error": "Solo administradores."})
            users = [{"id": u["id"], "name": u["name"], "isAdmin": bool(u["is_admin"]),
                      "createdAt": u["created_at"]} for u in db.list_users()]
            return self._json(200, {"users": users})
        if path == "/api/ranking":
            return self._json(200, self._ranking())
        if path == "/api/ranking-history":
            return self._json(200, ranking_history(parse_prediction(db.get_results()),
                                                    db.all_user_predictions()))
        if path == "/api/stats":
            return self._json(200, compute_stats(parse_prediction(db.get_results()),
                                                 db.all_user_predictions()))

        return self._send(404, "<h1>404</h1>")

    # ---------- POST ----------
    def do_POST(self):
        path = urlparse(self.path).path
        user = self._user()
        body = self._body_json()

        if path == "/api/auth/register":
            return self._register(body)
        if path == "/api/auth/login":
            return self._login(body)
        if path == "/api/auth/logout":
            return self._json(200, {"ok": True}, set_cookie=self._clear_cookie())
        if path == "/api/prediction":
            if not user:
                return self._json(401, {"error": "No autenticado."})
            state = gating.lock_state()
            clean = sanitize_prediction(body.get("data"))
            prev_row = db.get_prediction(user["id"])
            prev = parse_prediction(prev_row["data"] if prev_row else None)
            merged = gating.apply_locks(prev, clean, state)
            submitted = body.get("submitted") if isinstance(body.get("submitted"), bool) else None
            db.save_prediction(user["id"], json.dumps(merged, ensure_ascii=False), submitted)
            return self._json(200, {"ok": True, "data": merged, "locks": state})
        if path == "/api/admin/results":
            if not user or not user["isAdmin"]:
                return self._json(403, {"error": "Solo administradores."})
            clean = sanitize_prediction(body.get("data"))
            db.save_results(json.dumps(clean, ensure_ascii=False))
            return self._json(200, {"ok": True})
        if path == "/api/admin/users/delete":
            if not user or not user["isAdmin"]:
                return self._json(403, {"error": "Solo administradores."})
            try:
                uid = int(body.get("id"))
            except (TypeError, ValueError):
                return self._json(400, {"error": "Identificador no valido."})
            if uid == user["id"]:
                return self._json(400, {"error": "No puedes eliminar tu propia cuenta de administrador."})
            ok = db.delete_user(uid)
            if not ok:
                return self._json(400, {"error": "No se puede eliminar (no existe o es administrador)."})
            return self._json(200, {"ok": True})
        if path == "/api/admin/deadline":
            if not user or not user["isAdmin"]:
                return self._json(403, {"error": "Solo administradores."})
            raw = body.get("deadline")
            value = str(raw).strip() if raw else ""
            if value:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    return self._json(400, {"error": "Fecha no valida."})
            db.set_setting(gating.DEADLINE_KEY, value)
            return self._json(200, {"ok": True, "deadline": value or None})

        return self._json(404, {"error": "No encontrado."})

    # ---------- acciones ----------
    def _register(self, body):
        name = str(body.get("name", "")).strip()
        password = str(body.get("password", ""))
        if not (2 <= len(name) <= 30):
            return self._json(400, {"error": "El nombre debe tener entre 2 y 30 caracteres."})
        if len(password) < 4:
            return self._json(400, {"error": "La contrasena debe tener al menos 4 caracteres."})
        if db.get_user_by_name(name):
            return self._json(409, {"error": "Ese nombre ya esta en uso. Elige otro."})
        uid = db.create_user(name, auth.hash_password(password), is_admin=False)
        token = auth.create_token(uid, name, False)
        return self._json(200, {"ok": True, "user": {"name": name, "isAdmin": False}},
                          set_cookie=self._set_cookie(token))

    def _login(self, body):
        name = str(body.get("name", "")).strip()
        password = str(body.get("password", ""))
        if not name or not password:
            return self._json(400, {"error": "Introduce tu nombre y contrasena."})
        row = db.get_user_by_name(name)
        if not row or not auth.verify_password(password, row["password_hash"]):
            return self._json(401, {"error": "Nombre o contrasena incorrectos."})
        token = auth.create_token(row["id"], row["name"], bool(row["is_admin"]))
        return self._json(200, {"ok": True, "user": {"name": row["name"], "isAdmin": bool(row["is_admin"])}},
                          set_cookie=self._set_cookie(token))

    def _ranking(self):
        real = parse_prediction(db.get_results())
        rows = []
        for r in db.all_user_predictions():
            pred = parse_prediction(r["data"])
            score = compute_score(pred, real)
            row = {"name": r["name"], "submitted": bool(r["submitted"])}
            row.update(score)
            rows.append(row)
        rows.sort(key=lambda x: (-x["total"], -x["exactHits"], x["name"].lower()))
        state = gating.lock_state(real=real)
        return {"ranking": rows,
                "hasResults": bool(real["groups"]) or bool(real["knockout"]),
                "deadlinePassed": state["deadlinePassed"],
                "deadline": state["deadline"]}

    def _user_prediction(self, query):
        name = (query.get("name") or [""])[0].strip()
        if not name:
            return self._json(400, {"error": "Falta el nombre."})
        state = gating.lock_state()
        if not state["deadlinePassed"]:
            return self._json(403, {"error": "Las quinielas de otros se podran ver cuando se cierren las predicciones."})
        row = db.get_prediction_by_name(name)
        if not row or row["is_admin"]:
            return self._json(404, {"error": "Participante no encontrado."})
        real = parse_prediction(db.get_results())
        return self._json(200, {"owner": row["name"],
                                "data": parse_prediction(row["data"]),
                                "submitted": bool(row["submitted"]),
                                "locks": state,
                                "realGroups": real["groups"] if state["knockoutOpen"] else {}})

    def _serve_static(self, path):
        rel = path[len("/static/"):]
        base = os.path.abspath(_STATIC_DIR)
        full = os.path.abspath(os.path.join(base, rel))
        try:
            within = os.path.commonpath([base, full]) == base
        except ValueError:
            within = False  # rutas en unidades distintas (Windows): fuera de static
        if not within or not os.path.isfile(full):
            return self._send(404, "404")
        ext = os.path.splitext(full)[1]
        ctype = _MIME.get(ext, "application/octet-stream")
        with open(full, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype + ("; charset=utf-8" if ctype.startswith("text") or ext in (".js", ".json") else ""))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)


def _ensure_admin():
    """Crea el usuario administrador si todavia no existe.

    Solo lo crea cuando falta (no pisa la contrasena en cada reinicio). En
    produccion las credenciales se controlan con ADMIN_NAME / ADMIN_PASSWORD.
    Imprescindible en la nube: con una base de datos nueva no habria admin y
    nadie podria introducir los resultados.
    """
    if db.get_user_by_name(config.ADMIN_NAME) is None:
        db.upsert_admin(config.ADMIN_NAME, auth.hash_password(config.ADMIN_PASSWORD))
        print('Usuario admin "%s" creado.' % config.ADMIN_NAME)


def _security_warnings():
    if config.USING_DEFAULT_SECRET:
        print("  [SEGURIDAD] AUTH_SECRET usa el valor por defecto: define uno "
              "largo y aleatorio (variable de entorno AUTH_SECRET) en produccion.")
    if config.USING_DEFAULT_ADMIN_PW:
        print("  [SEGURIDAD] ADMIN_PASSWORD usa el valor por defecto ('admin1234'): "
              "cambialo con la variable de entorno ADMIN_PASSWORD.")


def serve():
    db.init_db()
    _ensure_admin()
    _security_warnings()
    httpd = ThreadingHTTPServer((config.HOST, config.PORT), Handler)
    print("Porra Mundial 2026 escuchando en http://%s:%d" % (config.HOST, config.PORT))
    print("(Ctrl+C para detener)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        httpd.server_close()
