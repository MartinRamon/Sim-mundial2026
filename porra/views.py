"""Generacion de HTML (sin motores de plantillas externos)."""

import html
import json
from urllib.parse import quote

from .scoring import POINTS


def esc(s):
    return html.escape(str(s), quote=True)


def _nav(user, active):
    links = [("/predict", "Mis predicciones", bool(user)),
             ("/ranking", "Ranking", True),
             ("/stats", "Estadisticas", True),
             ("/admin", "Admin", bool(user and user.get("isAdmin")))]
    items = []
    for href, label, show in links:
        if not show:
            continue
        cls = "nav-link active" if active == href else "nav-link"
        items.append('<a class="%s" href="%s">%s</a>' % (cls, href, esc(label)))
    if user:
        admin = '<span class="admintag">(admin)</span>' if user.get("isAdmin") else ""
        items.append('<span class="nav-user">&#128100; %s%s</span>' % (esc(user["name"]), admin))
        items.append('<button class="btn btn-ghost" onclick="logout()">Salir</button>')
    else:
        items.append('<a class="btn btn-primary" href="/login">Entrar</a>')
    return (
        '<header class="nav"><div class="nav-inner">'
        '<a class="brand" href="/" aria-label="AMFRESH - Porra Mundial 2026">'
        '<span class="brand-logo-wrap"><img class="brand-logo" src="/static/amfresh-logo.png" alt="AMFRESH Group"></span>'
        '<span class="brand-sep" aria-hidden="true"></span>'
        '<span class="brand-app">Porra <span class="accent">Mundial 2026</span></span>'
        '</a>'
        '<nav class="nav-links">%s</nav>'
        '</div></header>' % "".join(items)
    )


def layout(user, title, active, content, scripts=""):
    return (
        "<!DOCTYPE html><html lang=\"es\"><head>"
        "<meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<meta name=\"description\" content=\"Predicciones del Mundial de Futbol 2026 y ranking en directo de AMFRESH.\">"
        "<title>%s</title>"
        "<link rel=\"icon\" type=\"image/svg+xml\" href=\"/static/favicon.svg\">"
        "<link rel=\"stylesheet\" href=\"/static/styles.css\">"
        "</head><body>"
        "%s"
        "<main class=\"container fade-in\">%s</main>"
        "<footer>Porra Mundial 2026 &middot; Hecho para AMFRESH &middot; Datos del sorteo oficial de la FIFA</footer>"
        "<script>"
        "async function logout(){await fetch('/api/auth/logout',{method:'POST'});location.href='/login';}"
        "</script>"
        "%s"
        "</body></html>"
    ) % (esc(title), _nav(user, active), content, scripts)


def home_page(user):
    if user:
        cta = ('<a class="btn btn-primary" href="/predict" style="padding:12px 24px;font-size:16px">Hacer mis predicciones</a>'
               '<a class="btn btn-ghost" href="/ranking" style="padding:12px 24px;font-size:16px">Ver ranking</a>')
    else:
        cta = ('<a class="btn btn-primary" href="/login" style="padding:12px 24px;font-size:16px">Entrar y empezar</a>'
               '<a class="btn btn-ghost" href="/ranking" style="padding:12px 24px;font-size:16px">Ver ranking</a>')

    steps = [
        ("1", "Entra con tu nombre", "Registrate con tu nombre y una contrasena. En segundos estas dentro y puedes empezar a predecir."),
        ("2", "Predice el grupo de Espana y los premios", "Pon el marcador de los partidos del grupo de Espana y elige tu Pichichi y tu MVP del torneo."),
        ("3", "Acierta las eliminatorias", "Cuando el admin cierre la fase de grupos con los resultados reales, se abre el cuadro de eliminatorias (igual para todos) y predices ronda a ronda."),
    ]
    steps_html = "".join(
        '<div class="card" style="padding:20px"><div class="step-num">%s</div>'
        '<h3 style="margin-bottom:4px">%s</h3><p class="muted" style="margin:0;font-size:14px">%s</p></div>'
        % (n, esc(t), esc(d)) for n, t, d in steps
    )

    rules = [
        ("&#9989;", "+%d punto &middot; Ganador" % POINTS["WINNER"],
         "Por acertar el ganador (o el empate) en cada partido del grupo de Espana y de las eliminatorias."),
        ("&#127919;", "+%d punto exacto" % POINTS["EXACT_BONUS"],
         "Por acertar el resultado exacto del partido (se suma al punto por el ganador)."),
        ("&#127466;&#127480;", "+%d puntos &middot; Clausula de Espana" % POINTS["SPAIN_EXACT"],
         "+%d por acertar EXACTAMENTE en que ronda cae Espana. Pero -%d por cada ronda que Espana avance MAS alla de lo que predijiste (clausula antipatriotica)."
         % (POINTS["SPAIN_EXACT"], POINTS["SPAIN_PENALTY_PER_ROUND"])),
        ("&#127942;", "+%d puntos &middot; Campeon" % POINTS["CHAMPION"], "Por adivinar el campeon del Mundial."),
        ("&#128094;", "+%d punto &middot; Pichichi" % POINTS["PICHICHI"], "Por acertar el maximo goleador del torneo."),
        ("&#11088;", "+%d punto &middot; MVP" % POINTS["MVP"], "Por acertar el mejor jugador (MVP) del torneo."),
    ]
    rules_html = "".join(
        '<div class="rule"><div class="em">%s</div><div><div style="font-weight:700;color:#fff">%s</div>'
        '<div class="muted" style="font-size:14px">%s</div></div></div>' % (e, t, esc(d))
        for e, t, d in rules
    )

    pot_html = (
        '<section class="card" style="padding:28px;margin-top:16px;border:1px solid rgba(245,197,66,0.35);'
        'background:linear-gradient(135deg,rgba(245,197,66,0.10),rgba(255,255,255,0.02))">'
        '<h2 style="margin-top:0">&#128176; Funcionamiento del bote</h2>'
        '<div class="grid grid-3" style="gap:12px">'
        '<div class="rule"><div class="em">&#129351;</div><div><div style="font-weight:700;color:#fff">1&ordm; clasificado</div>'
        '<div class="muted" style="font-size:14px"><b>50% del bote</b>.</div></div></div>'
        '<div class="rule"><div class="em">&#129352;</div><div><div style="font-weight:700;color:#fff">2&ordm; clasificado</div>'
        '<div class="muted" style="font-size:14px"><b>30% del bote</b>.</div></div></div>'
        '<div class="rule"><div class="em">&#129353;</div><div><div style="font-weight:700;color:#fff">3&ordm; clasificado</div>'
        '<div class="muted" style="font-size:14px"><b>20% del bote</b>.</div></div></div>'
        '</div>'
        '<p class="muted" style="margin-top:16px;background:rgba(255,255,255,0.05);padding:12px;border-radius:12px;font-size:14px">'
        '<b>Metodo de pago:</b> a Amesty &mdash; <b>20&euro; en efectivo</b>.</p>'
        '</section>'
    )

    content = (
        '<section class="card" style="padding:40px">'
        '<span class="pill pill-pitch">Canada &middot; Mexico &middot; EE. UU. 2026</span>'
        '<h1 style="font-size:42px;max-width:720px;margin-top:16px">La porra del <span class="text-pitch">Mundial 2026</span> de AMFRESH</h1>'
        '<p class="muted" style="font-size:18px;max-width:640px">Predice el grupo de Espana y elige tu Pichichi y tu MVP. '
        'Cuando el admin cierre los grupos, el cuadro de eliminatorias se abre igual para todos y compites en un ranking en directo.</p>'
        '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px">%s</div>'
        '</section>'
        '<section class="grid grid-3" style="margin-top:16px">%s</section>'
        '%s'
        '<section class="card" style="padding:28px;margin-top:16px">'
        '<h2 style="margin-top:0">&#128203; Normas de puntuacion</h2>'
        '<div class="grid grid-2">%s</div>'
        '</section>'
    ) % (cta, steps_html, pot_html, rules_html)
    return layout(user, "Porra Mundial 2026", "/", content)


def login_page():
    content = '''
<div style="max-width:420px;margin:24px auto">
  <div class="card" style="padding:28px">
    <div style="text-align:center;margin-bottom:24px">
      <span class="brand-logo-wrap" style="display:inline-block;margin-bottom:12px"><img src="/static/amfresh-logo.png" alt="AMFRESH Group" style="height:56px;display:block"></span>
      <h1 id="title">Bienvenido</h1>
      <p class="muted" id="subtitle" style="margin:4px 0 0">Entra con tu nombre y contrasena.</p>
    </div>
    <div class="tabs" style="margin-bottom:20px">
      <button class="tab active" id="tab-login" onclick="setMode('login')">Entrar</button>
      <button class="tab" id="tab-register" onclick="setMode('register')">Crear cuenta</button>
    </div>
    <form id="form" onsubmit="return submitForm(event)">
      <label class="muted" style="font-size:14px">Nombre</label>
      <input class="input" id="name" autocomplete="username" required style="margin:4px 0 14px">
      <label class="muted" style="font-size:14px">Contrasena</label>
      <input class="input" id="password" type="password" autocomplete="current-password" required style="margin:4px 0 14px">
      <div id="error" class="notice hidden" style="margin-bottom:14px"></div>
      <button class="btn btn-primary" style="width:100%;padding:12px" id="submit" type="submit">Entrar</button>
    </form>
  </div>
</div>
<script>
let mode='login';
function setMode(m){mode=m;
  document.getElementById('tab-login').classList.toggle('active',m==='login');
  document.getElementById('tab-register').classList.toggle('active',m==='register');
  document.getElementById('title').textContent = m==='login'?'Bienvenido de nuevo':'Unete a la porra';
  document.getElementById('subtitle').textContent = m==='login'?'Entra con tu nombre y contrasena.':'Elige un nombre y una contrasena para empezar a predecir.';
  document.getElementById('submit').textContent = m==='login'?'Entrar':'Crear cuenta y entrar';
}
async function submitForm(e){
  e.preventDefault();
  const err=document.getElementById('error'); err.classList.add('hidden');
  const name=document.getElementById('name').value.trim();
  const password=document.getElementById('password').value;
  const ep = mode==='login'?'/api/auth/login':'/api/auth/register';
  try{
    const res=await fetch(ep,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,password})});
    const j=await res.json();
    if(!res.ok){err.textContent=j.error||'Algo ha ido mal.';err.classList.remove('hidden');return false;}
    location.href='/predict';
  }catch(_){err.textContent='No se pudo conectar.';err.classList.remove('hidden');}
  return false;
}
</script>'''
    return layout(None, "Entrar - Porra Mundial 2026", "/login", content)


def editor_page(user, title, active, mode, data_endpoint, submitted, score=None, deadline=None, owner=None):
    score_html = ""
    if score is not None:
        extra = score.get("extraPoints", 0)
        if extra > 0:
            extra_html = '<div class="text-pitch">&#11088; +%d extra</div>' % extra
        elif extra < 0:
            extra_html = '<div class="text-red">&#11088; %d extra</div>' % extra
        else:
            extra_html = ""
        score_html = (
            '<div class="card" style="display:flex;align-items:center;gap:16px;padding:12px 20px">'
            '<div style="text-align:center"><div style="font-size:24px;font-weight:800" class="text-pitch">%d</div>'
            '<div class="muted" style="font-size:12px">puntos</div></div>'
            '<div style="width:1px;height:32px;background:rgba(255,255,255,0.1)"></div>'
            '<div style="font-size:14px">&#127919; %d exactos<br>&#9989; %d ganadores%s</div></div>'
            % (score["total"], score["exactHits"], score["winnerHits"], extra_html)
        )

    boot = {"mode": mode, "dataEndpoint": data_endpoint, "submitted": bool(submitted)}
    if owner:
        boot["owner"] = owner
    header_extra = score_html

    if mode == "admin":
        intro = "Introduce los resultados reales a medida que avanza el Mundial. El cuadro real se construye con lo que pongas."
    elif mode == "view":
        intro = "Prediccion de %s (solo lectura). Visible porque las predicciones ya estan cerradas." % owner
    else:
        intro = "Rellena todos los partidos. El cuadro de eliminatorias se genera con tus resultados."

    admin_controls = ""
    if mode == "admin":
        admin_controls = (
            '<div class="card" id="deadline-card" style="padding:16px 20px;margin-bottom:16px">'
            '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:12px">'
            '<div style="flex:1;min-width:220px">'
            '<div style="font-weight:700;color:#fff">&#128274; Cierre de predicciones</div>'
            '<div class="muted" style="font-size:13px">A partir de esta fecha y hora nadie podra editar su quiniela. '
            'Los partidos con resultado real se bloquean automaticamente aunque no haya llegado el cierre.</div></div>'
            '<input class="input" id="deadline-input" type="datetime-local" value="%s" style="max-width:230px">'
            '<button class="btn btn-primary" id="deadline-save" type="button">Guardar cierre</button>'
            '<button class="btn btn-ghost" id="deadline-clear" type="button">Quitar</button>'
            '</div>'
            '<div id="deadline-msg" class="muted" style="font-size:13px;margin-top:8px"></div>'
            '</div>'
        ) % esc(_to_datetime_local(deadline))
        admin_controls += (
            '<div class="card" id="users-card" style="padding:16px 20px;margin-bottom:16px">'
            '<div style="display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:12px">'
            '<div><div style="font-weight:700;color:#fff">&#128101; Gestion de participantes</div>'
            '<div class="muted" style="font-size:13px">Elimina cuentas (por ejemplo duplicadas o de prueba). '
            'Se borran tambien sus predicciones. Esta accion no se puede deshacer.</div></div>'
            '<button class="btn btn-ghost" id="users-reload" type="button">&#8635; Actualizar lista</button>'
            '</div>'
            '<div id="users-list" class="muted" style="font-size:14px;margin-top:12px">Cargando&hellip;</div>'
            '</div>'
        )

    content = (
        '<div style="display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:24px">'
        '<div><h1>%s</h1><p class="muted" style="margin:0">%s</p></div>%s</div>'
        '%s'
        '<div id="app"><p class="muted">Cargando&hellip;</p></div>'
    ) % (esc(title), esc(intro), header_extra, admin_controls)
    scripts = (
        '<script id="boot" type="application/json">%s</script>'
        '<script src="/static/predict.js"></script>'
    ) % json.dumps(boot)
    return layout(user, title + " - Porra Mundial 2026", active, content, scripts)


def _to_datetime_local(deadline):
    """Convierte un ISO (con o sin segundos) a valor apto para input datetime-local."""
    if not deadline:
        return ""
    return deadline[:16]


def stats_page(user):
    content = (
        '<div style="margin-bottom:24px">'
        '<h1>&#128202; Estadisticas del grupo</h1>'
        '<p class="muted" id="st-sub" style="margin:0">Cargando&hellip;</p></div>'
        '<div id="stats"><div class="card" style="padding:40px;text-align:center" class="muted">Cargando estadisticas&hellip;</div></div>'
    )
    scripts = '<script src="/static/stats.js"></script>'
    return layout(user, "Estadisticas - Porra Mundial 2026", "/stats", content, scripts)


def view_prediction_page(user, name):
    name = (name or "").strip()
    if not name:
        content = '<div class="card" style="padding:40px;text-align:center" class="muted">Falta indicar el participante.</div>'
        return layout(user, "Ver quiniela - Porra Mundial 2026", "/ranking", content)
    endpoint = "/api/user-prediction?name=" + quote(name)
    return editor_page(user, "Quiniela de " + name, "/ranking", "view", endpoint,
                       submitted=False, score=None, owner=name)


def ranking_page(user):
    content = (
        '<div style="display:flex;flex-wrap:wrap;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:24px">'
        '<div><h1><img src="/static/trophy.svg" alt="" style="height:30px;vertical-align:-5px"> Ranking</h1><p class="muted" id="rk-sub" style="margin:0">Cargando&hellip;</p></div>'
        '<div style="display:flex;align-items:center;gap:12px">'
        '<span id="rk-updated" class="muted" style="font-size:12px"></span>'
        '<button class="btn btn-ghost" onclick="loadRanking()">&#8635; Actualizar</button></div></div>'
        '<div id="rk-podium"></div>'
        '<div id="rk-history"></div>'
        '<div id="rk-table" class="card" style="overflow:hidden"><div style="padding:40px;text-align:center" class="muted">Cargando ranking&hellip;</div></div>'
    )
    me = json.dumps(user["name"] if user else None)
    scripts = '<script>window.__ME__=%s;</script><script src="/static/ranking.js"></script>' % me
    return layout(user, "Ranking - Porra Mundial 2026", "/ranking", content, scripts)
