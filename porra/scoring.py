"""Motor de puntuacion.

Reglas (Mundial 2026):
- Acertar el ganador del partido (o el empate en grupos): +1
- Acertar el resultado exacto (ademas del punto por ganador): +1
- Clausula de Espana:
    * +3 por acertar EXACTAMENTE en que ronda cae Espana (clausula realista).
    * -3 por cada ronda que Espana avance MAS alla de lo previsto (clausula
      antipatriotica). Si Espana cae ANTES de lo previsto, 0 (ni bonus ni
      penalizacion).
- Adivinar el campeon del Mundial: +3
- Acertar el Pichichi (maximo goleador): +1
- Acertar el MVP del torneo: +1

A partir de que el admin completa la fase de grupos, el cuadro de eliminatorias
se siembra con los grupos REALES (igual para todos). Por eso la puntuacion de
las eliminatorias se calcula sembrando tanto la prediccion del usuario como el
resultado real con los grupos reales.
"""

from . import wc_data as D
from .bracket import resolve_bracket, _num

POINTS = {
    "WINNER": 1,
    "EXACT_BONUS": 1,
    "SPAIN_EXACT": 3,
    "SPAIN_PENALTY_PER_ROUND": 3,
    "CHAMPION": 3,
    "PICHICHI": 1,
    "MVP": 1,
}


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


def _spain_pred_progress(prediction, real, real_prog):
    """Ronda en la que el usuario predice que cae Espana, coherente con el modelo
    de dos fases:

    - Si en la realidad Espana cae en grupos (real_prog == 0), premiamos a quien
      lo predijo en SU fase de grupos (cuadro auto-sembrado con sus grupos).
    - Si Espana paso de grupos (real_prog >= 1), el cuadro de eliminatorias se
      siembra con los grupos REALES y la prediccion del usuario sobre las
      eliminatorias decide hasta donde llega Espana.
    """
    if real_prog is None:
        return None
    if real_prog == 0:
        return _spain_progress(resolve_bracket(prediction))
    return _spain_progress(resolve_bracket({
        "groups": real.get("groups") or {},
        "knockout": prediction.get("knockout") or {},
    }))


def _award_hit(pred_value, real_value, points):
    """+points si la prediccion del premio (Pichichi/MVP) coincide con la real."""
    p = (pred_value or "").strip().lower()
    r = (real_value or "").strip().lower()
    return points if (p and r and p == r) else 0


def compute_score(prediction, real):
    real_groups = real.get("groups") or {}
    real_ko = real.get("knockout") or {}
    user_ko = prediction.get("knockout") or {}

    # Cuadros sembrados con los grupos REALES (mismo punto de partida para todos).
    pred = resolve_bracket({"groups": real_groups, "knockout": user_ko})
    actual = resolve_bracket({"groups": real_groups, "knockout": real_ko})

    group_winner = 0
    group_exact = 0
    ko_winner = 0
    ko_exact = 0

    # ----- Fase de grupos -----
    for gm in D.GROUP_MATCHES:
        rs = real_groups.get(gm["id"])
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

    # ----- Campeon del Mundo (+3) -----
    pred_champ = (pred["matches"].get(D.FINAL_MATCH) or {}).get("winner")
    real_champ = (actual["matches"].get(D.FINAL_MATCH) or {}).get("winner")
    champion_bonus = POINTS["CHAMPION"] if (pred_champ and real_champ and pred_champ == real_champ) else 0

    # ----- Clausula de Espana -----
    #   * Acertar la ronda exacta: +3 (clausula realista).
    #   * Espana avanza MAS de lo previsto: -3 por cada ronda de mas (antipatriotica).
    #   * Espana cae ANTES de lo previsto: 0.
    real_prog = _spain_progress(actual)
    pred_prog = _spain_pred_progress(prediction, real, real_prog)
    if real_prog is None or pred_prog is None:
        spain_bonus = 0
    elif pred_prog == real_prog:
        spain_bonus = POINTS["SPAIN_EXACT"]
    elif real_prog > pred_prog:
        spain_bonus = -POINTS["SPAIN_PENALTY_PER_ROUND"] * (real_prog - pred_prog)
    else:
        spain_bonus = 0

    # ----- Premios individuales (+1 cada uno) -----
    pichichi_bonus = _award_hit(prediction.get("pichichi"), real.get("pichichi"), POINTS["PICHICHI"])
    mvp_bonus = _award_hit(prediction.get("mvp"), real.get("mvp"), POINTS["MVP"])

    group_points = group_winner * POINTS["WINNER"] + group_exact * POINTS["EXACT_BONUS"]
    knockout_points = ko_winner * POINTS["WINNER"] + ko_exact * POINTS["EXACT_BONUS"]
    extra_points = champion_bonus + spain_bonus + pichichi_bonus + mvp_bonus
    total = group_points + knockout_points + extra_points

    return {
        "total": total,
        "groupPoints": group_points,
        "knockoutPoints": knockout_points,
        "extraPoints": extra_points,
        "spainBonus": spain_bonus,
        "championBonus": champion_bonus,
        "pichichiBonus": pichichi_bonus,
        "mvpBonus": mvp_bonus,
        "exactHits": group_exact + ko_exact,
        "winnerHits": group_winner + ko_winner,
        "details": {
            "groupWinner": group_winner,
            "groupExact": group_exact,
            "koWinner": ko_winner,
            "koExact": ko_exact,
        },
    }
