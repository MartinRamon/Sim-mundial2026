"""Autenticacion sin dependencias externas: contrasenas con PBKDF2 (hashlib) y
sesiones en cookie firmada con HMAC."""

import base64
import hashlib
import hmac
import json
import os
import time

from . import config

_PBKDF2_ROUNDS = 200_000


def hash_password(password):
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS)
    return "pbkdf2_sha256$%d$%s$%s" % (
        _PBKDF2_ROUNDS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password, stored):
    try:
        algo, rounds, salt_b64, hash_b64 = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        rounds = int(rounds)
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def _b64e(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64d(s):
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def create_token(user_id, name, is_admin, max_age=7 * 24 * 3600):
    payload = {
        "sub": user_id,
        "name": name,
        "isAdmin": bool(is_admin),
        "exp": int(time.time()) + max_age,
    }
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = _b64e(hmac.new(config.AUTH_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest())
    return "%s.%s" % (body, sig)


def verify_token(token):
    if not token or "." not in token:
        return None
    try:
        body, sig = token.rsplit(".", 1)
        expected = _b64e(
            hmac.new(config.AUTH_SECRET.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64d(body))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
