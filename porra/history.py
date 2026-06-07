"""Evolucion del ranking por fases.

Para cada fase (jornadas de grupos y rondas eliminatorias) se calcula la
puntuacion ACUMULADA de cada participante usando solo los resultados reales
disponibles hasta esa fase, y de ahi su posicion en el ranking. Permite dibujar
la evolucion del ranking a lo largo del torneo.
"""

from . import wc_data as D
from .validate import parse_prediction
from .scoring import compute_score

# (etiqueta, jornada de grupos maxima incluida, rondas de eliminatoria incluidas)
_STAGES = [
    ("Jornada 1", 1, set()),
    ("Jornada 2", 2, set()),
    ("Jornada 3", 3, set()),
    ("Dieciseisavos", 3, {"R32"}),
    ("Octavos", 3, {"R32", "R16"}),
    ("Cuartos", 3, {"R32", "R16", "QF"}),
    ("Semis", 3, {"R32", "R16", "QF", "SF"}),
    ("Final", 3, {"R32", "R16", "QF", "SF", "TP", "F"}),
]


def _partial_real(real, max_md, ko_rounds):
    groups = {}
    for m in D.GROUP_MATCHES:
        if m["matchday"] <= max_md:
            v = (real.get("groups") or {}).get(m["id"])
            if v:
                groups[m["id"]] = v
    ko = {}
    for km in D.KNOCKOUT_MATCHES:
        if km["round"] in ko_rounds:
            v = (real.get("knockout") or {}).get(str(km["match"]))
            if v:
                ko[str(km["match"])] = v
    return {"groups": groups, "knockout": ko}


def _stage_has_new(real, idx):
    """True si en `real` hay algun resultado propio de la fase idx (no de anteriores)."""
    label, max_md, ko_rounds = _STAGES[idx]
    if not ko_rounds:  # fase de grupos: jornada == max_md
        return any(
            (real.get("groups") or {}).get(m["id"])
            for m in D.GROUP_MATCHES
            if m["matchday"] == max_md
        )
    prev_rounds = _STAGES[idx - 1][2] if idx > 0 else set()
    new_rounds = ko_rounds - prev_rounds
    return any(
        (real.get("knockout") or {}).get(str(km["match"]))
        for km in D.KNOCKOUT_MATCHES
        if km["round"] in new_rounds
    )


def ranking_history(real, user_rows):
    """user_rows: iterable de filas con .name y .data (predicciones)."""
    # ultima fase con resultados reales
    last = -1
    for i in range(len(_STAGES)):
        if _stage_has_new(real, i):
            last = i
    if last < 0:
        return {"hasData": False, "stages": [], "series": []}

    active = list(range(last + 1))
    partials = [_partial_real(real, _STAGES[i][1], _STAGES[i][2]) for i in active]

    preds = [(r["name"], parse_prediction(r["data"])) for r in user_rows]

    series = {name: {"name": name, "points": [], "positions": []} for name, _ in preds}
    for col, pr in enumerate(partials):
        scored = []
        for name, pred in preds:
            total = compute_score(pred, pr)["total"]
            series[name]["points"].append(total)
            scored.append((name, total))
        scored.sort(key=lambda x: (-x[1], x[0].lower()))
        pos_by_name = {name: i + 1 for i, (name, _) in enumerate(scored)}
        for name in series:
            series[name]["positions"].append(pos_by_name[name])

    out = list(series.values())
    # ordenar por posicion final (mejor primero)
    out.sort(key=lambda s: (s["positions"][-1], s["name"].lower()))
    return {
        "hasData": True,
        "stages": [_STAGES[i][0] for i in active],
        "series": out,
    }
