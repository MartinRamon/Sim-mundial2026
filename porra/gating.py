"""Control de cierre de predicciones.

Dos mecanismos complementarios para proteger la integridad de la porra:

1. **Deadline global**: fecha/hora a partir de la cual nadie puede editar nada.
2. **Bloqueo por partido**: en cuanto el admin introduce el resultado real de un
   partido, ese partido queda congelado para todos (no se puede cambiar la
   prediccion de algo cuyo resultado ya se conoce).
"""

from datetime import datetime

from . import db
from . import wc_data as D
from .bracket import groups_are_complete
from .validate import parse_prediction

DEADLINE_KEY = "deadline"


def _deadline_passed(deadline):
    if not deadline:
        return False
    try:
        return datetime.now() >= datetime.fromisoformat(deadline)
    except ValueError:
        return False


def lock_state(real=None, deadline=None):
    """Estado de bloqueo actual, apto para enviar al cliente y para validar."""
    if real is None:
        real = parse_prediction(db.get_results())
    if deadline is None:
        deadline = db.get_setting(DEADLINE_KEY, "")
    passed = _deadline_passed(deadline)
    groups_complete = groups_are_complete(real.get("groups") or {})
    return {
        "deadline": deadline or None,
        "deadlinePassed": passed,
        # La fase de grupos esta cerrada por el admin -> se bloquean los grupos
        # y se abre (siembra desde los grupos REALES) el cuadro de eliminatorias.
        "groupStageComplete": groups_complete,
        "knockoutOpen": groups_complete,
        "lockedGroups": sorted((real.get("groups") or {}).keys()),
        "lockedKnockout": sorted((real.get("knockout") or {}).keys()),
    }


def is_group_locked(state, mid):
    return state["deadlinePassed"] or state["groupStageComplete"] or mid in state["lockedGroups"]


def is_ko_locked(state, num):
    # Las eliminatorias no se pueden tocar hasta que el admin completa los grupos.
    if not state["knockoutOpen"]:
        return True
    return state["deadlinePassed"] or str(num) in state["lockedKnockout"]


def _extras_locked(state):
    """Pichichi y MVP solo se bloquean con el cierre global de predicciones."""
    return state["deadlinePassed"]


def _any_lock(state):
    return bool(
        state["deadlinePassed"]
        or state["groupStageComplete"]
        or not state["knockoutOpen"]
        or state["lockedGroups"]
        or state["lockedKnockout"]
    )


def apply_locks(prev, new, state):
    """Devuelve la prediccion que SI se puede guardar: en los partidos bloqueados
    conserva el valor previo del usuario; en el resto toma el valor nuevo. Asi un
    cliente manipulado no puede cambiar partidos ya cerrados."""
    prev = prev or {"groups": {}, "knockout": {}}
    new = new or {"groups": {}, "knockout": {}}

    extras_src = prev if _extras_locked(state) else new
    pichichi = extras_src.get("pichichi", "") or ""
    mvp = extras_src.get("mvp", "") or ""

    if not _any_lock(state):
        out = {"groups": (new.get("groups") or {}), "knockout": (new.get("knockout") or {})}
        out["pichichi"] = pichichi
        out["mvp"] = mvp
        return out

    out_groups = {}
    for mid in D.GROUP_MATCH_IDS:
        src = prev if is_group_locked(state, mid) else new
        val = (src.get("groups") or {}).get(mid)
        if val is not None:
            out_groups[mid] = val

    out_ko = {}
    for num in D.KNOCKOUT_MATCH_IDS:
        src = prev if is_ko_locked(state, num) else new
        val = (src.get("knockout") or {}).get(num)
        if val is not None:
            out_ko[num] = val

    return {"groups": out_groups, "knockout": out_ko, "pichichi": pichichi, "mvp": mvp}
