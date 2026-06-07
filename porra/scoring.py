"""Motor de puntuacion: ganador (+1), resultado exacto (+2 extra) y la
clausula antipatriotica de Espana (-3 por ronda)."""

from . import wc_data as D
from .bracket import resolve_bracket, _num

POINTS = {"WINNER": 1, "EXACT_BONUS": 2, "PENALTY_PER_ROUND": 3}


def _sign(a, b):
    return 1 if a > b else (-1 if a < b else 0)


def _spain_progress(bracket):
    """Hasta que ronda llega Espana. None si la fase de grupos no esta completa."""
    if not bracket["groups_complete"]:
        return None

    advances = False
    for letter, lst in bracket["standings"].items():
        idx = next((i for i, s in enumerate(lst) if s["team"] == D.HOME_TEAM), -1)
        if idx in (0, 1):
            advances = True
    if not advances:
        for letter in bracket["qualified_thirds"]:
            lst = bracket["standings"].get(letter)
            if lst and len(lst) > 2 and lst[2]["team"] == D.HOME_TEAM:
                advances = True
    if not advances:
        return 0  # eliminada en fase de grupos

    deepest_round = None
    deepest_order = -1
    final_match = 0
    for km in D.KNOCKOUT_MATCHES:
        m = bracket["matches"].get(km["match"])
        if not m:
            continue
        if m["home"] == D.HOME_TEAM or m["away"] == D.HOME_TEAM:
            order = D.ROUND_ORDER.index(km["round"])
            if order > deepest_order:
                deepest_order = order
                deepest_round = km["round"]
                final_match = km["match"]
    if not deepest_round:
        return 0

    index = D.ELIM_ROUND_INDEX[deepest_round]
    if deepest_round == "F" and bracket["matches"].get(final_match, {}).get("winner") == D.HOME_TEAM:
        index = 6  # campeona
    return index


def compute_score(prediction, real):
    pred = resolve_bracket(prediction)
    actual = resolve_bracket(real)

    group_winner = 0
    group_exact = 0
    ko_winner = 0
    ko_exact = 0

    # ----- Fase de grupos -----
    for gm in D.GROUP_MATCHES:
        rs = (real.get("groups") or {}).get(gm["id"])
        ps = (prediction.get("groups") or {}).get(gm["id"])
        if not rs or not ps:
            continue
        rh, ra = _num(rs.get("h")), _num(rs.get("a"))
        ph, pa = _num(ps.get("h")), _num(ps.get("a"))
        if None in (rh, ra, ph, pa):
            continue
        if _sign(ph, pa) == _sign(rh, ra):
            group_winner += 1
            if ph == rh and pa == ra:
                group_exact += 1

    # ----- Eliminatorias -----
    for km in D.KNOCKOUT_MATCHES:
        rm = actual["matches"].get(km["match"])
        pm = pred["matches"].get(km["match"])
        if not rm or not pm or not rm["winner"]:
            continue
        if pm["winner"] and pm["winner"] == rm["winner"]:
            ko_winner += 1
            if (
                pm["home"] == rm["home"]
                and pm["away"] == rm["away"]
                and pm["homeGoals"] == rm["homeGoals"]
                and pm["awayGoals"] == rm["awayGoals"]
            ):
                ko_exact += 1

    # ----- Clausula antipatriotica (Espana) -----
    spain_penalty = 0
    pred_prog = _spain_progress(pred)
    real_prog = _spain_progress(actual)
    if pred_prog is not None and real_prog is not None and real_prog > pred_prog:
        spain_penalty = -POINTS["PENALTY_PER_ROUND"] * (real_prog - pred_prog)

    group_points = group_winner * POINTS["WINNER"] + group_exact * POINTS["EXACT_BONUS"]
    knockout_points = ko_winner * POINTS["WINNER"] + ko_exact * POINTS["EXACT_BONUS"]
    total = group_points + knockout_points + spain_penalty

    return {
        "total": total,
        "groupPoints": group_points,
        "knockoutPoints": knockout_points,
        "spainPenalty": spain_penalty,
        "exactHits": group_exact + ko_exact,
        "winnerHits": group_winner + ko_winner,
        "details": {
            "groupWinner": group_winner,
            "groupExact": group_exact,
            "koWinner": ko_winner,
            "koExact": ko_exact,
        },
    }
