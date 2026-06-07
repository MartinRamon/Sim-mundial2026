"""Motor del cuadro: clasificaciones de grupos, mejores terceros (Anexo C) y
propagacion de las eliminatorias a partir de los resultados predichos."""

import json
import os

from . import wc_data as D

_ANNEX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "annexC.json")
with open(_ANNEX_PATH, "r", encoding="utf-8") as _f:
    ANNEX_C = json.load(_f)


def _num(x):
    if isinstance(x, bool):
        return None
    if isinstance(x, (int, float)) and x == x and x not in (float("inf"), float("-inf")):
        return int(x)
    return None


def empty_prediction():
    return {"groups": {}, "knockout": {}}


def compute_standings(groups):
    result = {}
    for letter in D.GROUP_LETTERS:
        teams = D.GROUPS[letter]
        stats = {}
        for i, t in enumerate(teams):
            stats[t] = {
                "team": t,
                "group": letter,
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "gf": 0,
                "ga": 0,
                "gd": 0,
                "points": 0,
                "seed": i,
            }
        for m in D.GROUP_MATCHES:
            if m["group"] != letter:
                continue
            sc = groups.get(m["id"])
            if not sc:
                continue
            h = _num(sc.get("h"))
            a = _num(sc.get("a"))
            if h is None or a is None:
                continue
            hs = stats[m["home"]]
            as_ = stats[m["away"]]
            hs["played"] += 1
            as_["played"] += 1
            hs["gf"] += h
            hs["ga"] += a
            as_["gf"] += a
            as_["ga"] += h
            if h > a:
                hs["won"] += 1
                as_["lost"] += 1
                hs["points"] += 3
            elif h < a:
                as_["won"] += 1
                hs["lost"] += 1
                as_["points"] += 3
            else:
                hs["drawn"] += 1
                as_["drawn"] += 1
                hs["points"] += 1
                as_["points"] += 1
        rows = [stats[t] for t in teams]
        for s in rows:
            s["gd"] = s["gf"] - s["ga"]
        rows.sort(key=lambda s: (-s["points"], -s["gd"], -s["gf"], s["seed"]))
        result[letter] = rows
    return result


def groups_are_complete(groups):
    for m in D.GROUP_MATCHES:
        sc = groups.get(m["id"])
        if not sc or _num(sc.get("h")) is None or _num(sc.get("a")) is None:
            return False
    return True


def _rank_thirds(standings):
    thirds = [standings[l][2] for l in D.GROUP_LETTERS]
    thirds.sort(key=lambda s: (-s["points"], -s["gd"], -s["gf"], s["group"]))
    return thirds


def _resolve_slot(ref, ctx):
    t = ref["type"]
    if t == "group":
        lst = ctx["standings"].get(ref["group"])
        if not lst:
            return None
        idx = ref["rank"] - 1
        return lst[idx]["team"] if 0 <= idx < len(lst) else None
    if t == "third":
        return ctx["third_slot_team"].get(ref["slot"])
    if t == "winner":
        m = ctx["matches"].get(ref["match"])
        return m["winner"] if m else None
    if t == "loser":
        m = ctx["matches"].get(ref["match"])
        return m["loser"] if m else None
    return None


def _decide_match(home, away, score):
    h = _num(score.get("h")) if score else None
    a = _num(score.get("a")) if score else None
    pen = None
    if score and score.get("pen") in ("home", "away"):
        pen = score["pen"]
    winner = None
    loser = None
    if home and away and h is not None and a is not None:
        if h > a:
            winner, loser = home, away
        elif a > h:
            winner, loser = away, home
        elif pen:
            if pen == "home":
                winner, loser = home, away
            else:
                winner, loser = away, home
    return {
        "home": home,
        "away": away,
        "homeGoals": h,
        "awayGoals": a,
        "pen": pen,
        "winner": winner,
        "loser": loser,
    }


def resolve_bracket(data):
    groups = data.get("groups") or {}
    knockout = data.get("knockout") or {}
    standings = compute_standings(groups)
    complete = groups_are_complete(groups)

    ranked = _rank_thirds(standings)
    qualified_thirds = sorted(s["group"] for s in ranked[:8])

    third_slot_team = {slot: None for slot in D.THIRD_SLOT_TO_MATCH}

    if complete:
        key = "".join(qualified_thirds)
        mapping = ANNEX_C.get(key)
        if mapping:
            for slot, group_code in mapping.items():
                group_letter = group_code[1:]  # "3H" -> "H"
                lst = standings.get(group_letter)
                third_slot_team[slot] = lst[2]["team"] if lst and len(lst) > 2 else None

    matches = {}
    ctx = {"standings": standings, "third_slot_team": third_slot_team, "matches": matches}
    for km in D.KNOCKOUT_MATCHES:
        home = _resolve_slot(km["home"], ctx)
        away = _resolve_slot(km["away"], ctx)
        matches[km["match"]] = _decide_match(home, away, knockout.get(str(km["match"])))

    return {
        "standings": standings,
        "qualified_thirds": qualified_thirds,
        "third_slot_team": third_slot_team,
        "matches": matches,
        "groups_complete": complete,
    }
