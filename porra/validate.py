"""Saneamiento de los datos de prediccion entrantes."""

import json

from . import wc_data as D


def _clamp_goal(x):
    try:
        n = int(round(float(x)))
    except (TypeError, ValueError):
        return None
    if n < 0:
        return 0
    if n > 30:
        return 30
    return n


def _clean_player(x):
    """Nombre de jugador (Pichichi / MVP): texto libre saneado y acotado."""
    if not isinstance(x, str):
        return ""
    s = x.strip()
    if len(s) > 60:
        s = s[:60]
    return s


def sanitize_prediction(raw):
    if not isinstance(raw, dict):
        raw = {}
    groups_in = raw.get("groups") or {}
    ko_in = raw.get("knockout") or {}

    groups = {}
    if isinstance(groups_in, dict):
        for mid, val in groups_in.items():
            if mid not in D.GROUP_MATCH_IDS or not isinstance(val, dict):
                continue
            h = _clamp_goal(val.get("h"))
            a = _clamp_goal(val.get("a"))
            if h is None or a is None:
                continue
            groups[mid] = {"h": h, "a": a}

    knockout = {}
    if isinstance(ko_in, dict):
        for num, val in ko_in.items():
            if str(num) not in D.KNOCKOUT_MATCH_IDS or not isinstance(val, dict):
                continue
            h = _clamp_goal(val.get("h"))
            a = _clamp_goal(val.get("a"))
            if h is None or a is None:
                continue
            entry = {"h": h, "a": a}
            if val.get("pen") in ("home", "away"):
                entry["pen"] = val["pen"]
            knockout[str(num)] = entry

    return {
        "groups": groups,
        "knockout": knockout,
        "pichichi": _clean_player(raw.get("pichichi")),
        "mvp": _clean_player(raw.get("mvp")),
    }


def parse_prediction(json_str):
    if not json_str:
        return {"groups": {}, "knockout": {}, "pichichi": "", "mvp": ""}
    try:
        return sanitize_prediction(json.loads(json_str))
    except Exception:
        return {"groups": {}, "knockout": {}, "pichichi": "", "mvp": ""}
