"""Estadisticas agregadas del grupo de participantes."""

from . import wc_data as D
from .validate import parse_prediction
from .bracket import resolve_bracket, _num
from .scoring import _spain_progress, _sign

SPAIN_FATE_LABELS = {
    0: "Fase de grupos",
    1: "Dieciseisavos",
    2: "Octavos",
    3: "Cuartos",
    4: "Semifinales",
    5: "Subcampeona",
    6: "Campeona",
}


def _toplist(counter, limit=8):
    items = sorted(counter.items(), key=lambda x: (-x[1], D.team_name(x[0]).lower()))
    return [{"team": t, "name": D.team_name(t), "count": c} for t, c in items[:limit]]


def compute_stats(real, user_rows):
    preds = []
    for r in user_rows:
        pred = parse_prediction(r["data"])
        preds.append((r["name"], pred, resolve_bracket(pred)))
    total_users = len(preds)

    # ----- Campeon mas elegido y finalistas -----
    champ_count = {}
    finalist_count = {}
    for _name, _pred, br in preds:
        fm = br["matches"].get(D.FINAL_MATCH)
        if not fm:
            continue
        if fm["winner"]:
            champ_count[fm["winner"]] = champ_count.get(fm["winner"], 0) + 1
        for side in (fm["home"], fm["away"]):
            if side:
                finalist_count[side] = finalist_count.get(side, 0) + 1

    # ----- Destino predicho para Espana -----
    fate_count = {}
    for _name, _pred, br in preds:
        prog = _spain_progress(br)
        if prog is not None:
            fate_count[prog] = fate_count.get(prog, 0) + 1
    spain_fate = [
        {"index": k, "label": SPAIN_FATE_LABELS.get(k, str(k)), "count": fate_count[k]}
        for k in sorted(fate_count)
    ]

    # ----- Aciertos por partido de grupos (con resultado real) -----
    per_match = []
    md_agg = {}  # matchday -> [aciertos_ganador, n]
    for gm in D.GROUP_MATCHES:
        rs = (real.get("groups") or {}).get(gm["id"])
        if not rs:
            continue
        rh, ra = _num(rs.get("h")), _num(rs.get("a"))
        if rh is None or ra is None:
            continue
        rsign = _sign(rh, ra)
        n = winner = exact = 0
        for _name, pred, _br in preds:
            ps = (pred.get("groups") or {}).get(gm["id"])
            if not ps:
                continue
            ph, pa = _num(ps.get("h")), _num(ps.get("a"))
            if ph is None or pa is None:
                continue
            n += 1
            if _sign(ph, pa) == rsign:
                winner += 1
                if ph == rh and pa == ra:
                    exact += 1
        if n == 0:
            continue
        per_match.append({
            "id": gm["id"], "group": gm["group"], "matchday": gm["matchday"],
            "homeName": D.team_name(gm["home"]), "awayName": D.team_name(gm["away"]),
            "real": {"h": rh, "a": ra},
            "n": n, "winner": winner, "exact": exact,
            "winnerPct": round(winner * 100 / n), "exactPct": round(exact * 100 / n),
        })
        agg = md_agg.setdefault(gm["matchday"], [0, 0])
        agg[0] += winner
        agg[1] += n

    per_matchday = [
        {"matchday": md, "winnerPct": round(h * 100 / t) if t else 0, "n": t}
        for md, (h, t) in sorted(md_agg.items())
    ]

    easiest = max(per_match, key=lambda m: m["winnerPct"], default=None)
    hardest = min(per_match, key=lambda m: m["winnerPct"], default=None)

    return {
        "totalUsers": total_users,
        "champions": _toplist(champ_count),
        "finalists": _toplist(finalist_count),
        "spainFate": spain_fate,
        "perMatch": per_match,
        "perMatchday": per_matchday,
        "easiest": easiest,
        "hardest": hardest,
        "ratedMatches": len(per_match),
    }
