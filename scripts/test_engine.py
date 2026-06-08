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

# Premios reales (Pichichi y MVP).
real["pichichi"] = "Lamine Yamal"
real["mvp"] = "Pedri"

# ----- Clausula antipatriotica: Espana avanza MAS de lo previsto -> -3 por ronda -----
# Usuario predice octavos (R16), Espana llega a semis (SF) = 2 rondas de mas = -6.
score = compute_score(user, real)
print("  Bonus Espana (octavos vs semis):", score["spainBonus"])
check(score["spainBonus"] == -6, "clausula antipatriotica = -6 (octavos vs semis, -3 por ronda)")

# Si Espana cae ANTES de lo previsto, ni bonus ni penalizacion (0).
user_over = fill_path(pred["groups"], spain_loses_round=None)  # usuario: Espana campeona
user_over["pichichi"] = ""
user_over["mvp"] = ""
score_over = compute_score(user_over, real)  # predice campeona, real semis
print("  Bonus Espana (sobreestimada):", score_over["spainBonus"])
check(score_over["spainBonus"] == 0, "sin penalizacion si Espana cae antes de lo previsto")

# Acertar la ronda exacta de Espana -> +3 (clausula realista).
user_spain_ok = fill_path(pred["groups"], spain_loses_round="SF")
user_spain_ok["pichichi"] = ""
user_spain_ok["mvp"] = ""
score_spain = compute_score(user_spain_ok, real)
print("  Bonus Espana (ronda correcta):", score_spain["spainBonus"])
check(score_spain["spainBonus"] == 3, "clausula Espana = +3 al acertar la ronda exacta (semis)")
check(score_spain["championBonus"] == 3, "campeon del Mundo = +3 al acertarlo")

# ----- Premios individuales (Pichichi/MVP, +1 cada uno) -----
award_user = {"groups": pred["groups"], "knockout": {}, "pichichi": "lamine yamal", "mvp": "Nadie"}
award = compute_score(award_user, real)
check(award["pichichiBonus"] == 1, "Pichichi = +1 al acertarlo (sin distinguir mayusculas)")
check(award["mvpBonus"] == 0, "MVP = 0 si no se acierta")

# ----- Prediccion identica a la realidad -> maximo de puntos -----
perfect = compute_score(real, real)
check(perfect["spainBonus"] == 3, "clausula Espana = +3 si se acierta el recorrido exacto")
check(perfect["championBonus"] == 3, "campeon = +3 en la prediccion perfecta")
check(perfect["pichichiBonus"] == 1, "Pichichi = +1 en la prediccion perfecta")
check(perfect["mvpBonus"] == 1, "MVP = +1 en la prediccion perfecta")
check(perfect["extraPoints"] == 8, "puntos extra = 8 (3+3+1+1) en la prediccion perfecta")
check(perfect["details"]["groupExact"] == 72, "72 resultados exactos de grupos")
print("  Puntuacion perfecta total:", perfect["total"])

sys.exit(0 if ok else 1)
