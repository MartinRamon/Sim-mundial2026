"""Comprobaciones del motor de cuadro y puntuacion."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from porra import wc_data as D
from porra.bracket import resolve_bracket
from porra.scoring import compute_score

ok = True


def check(cond, msg):
    global ok
    print(("OK: " if cond else "FALLO: ") + msg)
    if not cond:
        ok = False


def build_deterministic():
    groups = {}
    for m in D.GROUP_MATCHES:
        teams = D.GROUPS[m["group"]]
        hi = teams.index(m["home"])
        ai = teams.index(m["away"])
        if hi < ai:
            groups[m["id"]] = {"h": 3 - hi, "a": 0}
        else:
            groups[m["id"]] = {"h": 0, "a": 3 - ai}
    return {"groups": groups, "knockout": {}}


pred = build_deterministic()
res = resolve_bracket(pred)
check(res["groups_complete"], "fase de grupos completa")
for l in D.GROUP_LETTERS:
    check(res["standings"][l][0]["team"] == D.GROUPS[l][0], "1o del grupo %s correcto" % l)
check(len(res["qualified_thirds"]) == 8, "hay 8 mejores terceros")
assigned = len([v for v in res["third_slot_team"].values() if v])
check(assigned == 8, "8 terceros asignados (Annex C) = %d" % assigned)

r32_ok = all(res["matches"][n]["home"] and res["matches"][n]["away"] for n in range(73, 89))
check(r32_ok, "todos los R32 con ambos equipos")

# rellenar eliminatorias (gana local 1-0) y comprobar campeon
ROUND_OF = {m["match"]: m["round"] for m in D.KNOCKOUT_MATCHES}


def fill_path(groups, spain_loses_round=None):
    ko = {}
    data = {"groups": groups, "knockout": ko}
    for _ in range(6):
        r = resolve_bracket(data)
        for n in range(73, 105):
            m = r["matches"][n]
            if not m["home"] or not m["away"] or str(n) in ko:
                continue
            spain_here = m["home"] == "ESP" or m["away"] == "ESP"
            if spain_here and spain_loses_round and ROUND_OF[n] == spain_loses_round:
                ko[str(n)] = {"h": 0, "a": 1} if m["home"] == "ESP" else {"h": 1, "a": 0}
            elif spain_here:
                ko[str(n)] = {"h": 1, "a": 0} if m["home"] == "ESP" else {"h": 0, "a": 1}
            else:
                ko[str(n)] = {"h": 1, "a": 0}
        data = {"groups": groups, "knockout": ko}
    return data


real = fill_path(pred["groups"], spain_loses_round="SF")   # Espana llega a semis
user = fill_path(pred["groups"], spain_loses_round="R16")  # usuario: Espana cae en octavos
score = compute_score(user, real)
print("  Penalizacion Espana:", score["spainPenalty"])
check(score["spainPenalty"] == -6, "clausula Espana = -6 (octavos vs semifinales)")

# prediccion identica a la realidad -> max puntos, sin penalizacion
perfect = compute_score(real, real)
check(perfect["spainPenalty"] == 0, "sin penalizacion si se acierta el recorrido de Espana")
check(perfect["details"]["groupExact"] == 72, "72 resultados exactos de grupos")
print("  Puntuacion perfecta total:", perfect["total"])

sys.exit(0 if ok else 1)
