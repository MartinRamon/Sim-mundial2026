/* Editor de predicciones: motor de cuadro en cliente + interfaz en vivo.
   Sin dependencias externas. */
(function () {
  "use strict";

  var DATA = null;
  var BOOT = JSON.parse(document.getElementById("boot").textContent);
  var state = { groups: {}, knockout: {}, pichichi: "", mvp: "" };
  var submitted = false;
  var tab = "groups";
  var saveTimer = null;
  var built = false;
  // Grupos REALES introducidos por el admin. Una vez completos, el cuadro de
  // eliminatorias se siembra con ellos (igual para todos los participantes).
  var REAL_GROUPS = {};
  var LOCKS = { deadlinePassed: false, lockedGroups: [], lockedKnockout: [], groupStageComplete: false, knockoutOpen: false };

  /* ---------- Modo y bloqueos ---------- */
  function isView() { return BOOT.mode === "view"; }
  function deadlineClosed() { return BOOT.mode === "user" && !!LOCKS.deadlinePassed; }
  function anyEditDisabled() { return isView() || deadlineClosed(); }
  function lockedGroup(id) {
    if (anyEditDisabled()) return true;
    if (BOOT.mode !== "user") return false;
    if (LOCKS.groupStageComplete) return true;  // grupos cerrados por el admin
    return LOCKS.lockedGroups.indexOf(id) >= 0;
  }
  function lockedKo(numMatch) {
    if (anyEditDisabled()) return true;
    if (BOOT.mode !== "user") return false;
    if (!LOCKS.knockoutOpen) return true;  // aun no abierto
    return LOCKS.lockedKnockout.indexOf(String(numMatch)) >= 0;
  }
  /* El cuadro de eliminatorias se siembra desde los grupos REALES (usuario/vista)
     o desde los grupos que el propio admin va introduciendo. */
  function koContext() {
    if (BOOT.mode === "admin") {
      return groupsComplete(state.groups)
        ? { open: true, groups: state.groups }
        : { open: false, reason: "admin-complete" };
    }
    var open = BOOT.mode === "user" ? !!LOCKS.knockoutOpen : groupsComplete(REAL_GROUPS);
    return open ? { open: true, groups: REAL_GROUPS } : { open: false, reason: "wait-admin" };
  }
  var LOCK_BADGE = '<span class="lock-badge" title="Bloqueado">🔒</span>';

  function num(x) {
    return typeof x === "number" && isFinite(x) ? x : null;
  }
  function tName(code) {
    return DATA.teams[code] ? DATA.teams[code].name : "Por definir";
  }
  // Banderas como SVG locales (/static/flags/<iso>.svg). Los emojis de bandera
  // no se renderizan en Windows (aparecen como letras), por eso usamos imagenes.
  function flagHtml(code) {
    if (!code || !DATA.teams[code]) return '<span class="emoji-flag">&#127937;</span>';
    var iso = DATA.teams[code].iso;
    return '<img class="flag" src="/static/flags/' + iso + '.svg" alt="" loading="lazy">';
  }
  function teamHtml(code, placeholder) {
    if (!code) return '<span class="emoji-flag">&#127937;</span> <span class="nm muted" style="font-style:italic">' + (placeholder || "Por definir") + "</span>";
    return flagHtml(code) + ' <span class="nm">' + tName(code) + "</span>";
  }

  /* ---------- Motor del cuadro (port de bracket.py) ---------- */
  function computeStandings(groups) {
    var result = {};
    DATA.groupLetters.forEach(function (letter) {
      var teams = DATA.groups[letter];
      var stats = {};
      teams.forEach(function (t, i) {
        stats[t] = { team: t, group: letter, played: 0, won: 0, drawn: 0, lost: 0, gf: 0, ga: 0, gd: 0, points: 0, seed: i };
      });
      DATA.groupMatches.forEach(function (m) {
        if (m.group !== letter) return;
        var sc = groups[m.id];
        if (!sc) return;
        var h = num(sc.h), a = num(sc.a);
        if (h === null || a === null) return;
        var hs = stats[m.home], as_ = stats[m.away];
        hs.played++; as_.played++;
        hs.gf += h; hs.ga += a; as_.gf += a; as_.ga += h;
        if (h > a) { hs.won++; as_.lost++; hs.points += 3; }
        else if (h < a) { as_.won++; hs.lost++; as_.points += 3; }
        else { hs.drawn++; as_.drawn++; hs.points++; as_.points++; }
      });
      var rows = teams.map(function (t) { return stats[t]; });
      rows.forEach(function (s) { s.gd = s.gf - s.ga; });
      rows.sort(function (a, b) {
        return (b.points - a.points) || (b.gd - a.gd) || (b.gf - a.gf) || (a.seed - b.seed);
      });
      result[letter] = rows;
    });
    return result;
  }

  function groupsComplete(groups) {
    return DATA.groupMatches.every(function (m) {
      var sc = groups[m.id];
      return sc && num(sc.h) !== null && num(sc.a) !== null;
    });
  }

  function rankThirds(standings) {
    var thirds = DATA.groupLetters.map(function (l) { return standings[l][2]; });
    thirds.sort(function (a, b) {
      return (b.points - a.points) || (b.gd - a.gd) || (b.gf - a.gf) || (a.group < b.group ? -1 : a.group > b.group ? 1 : 0);
    });
    return thirds;
  }

  function resolveSlot(ref, ctx) {
    if (ref.type === "group") { var l = ctx.standings[ref.group]; return l ? (l[ref.rank - 1] ? l[ref.rank - 1].team : null) : null; }
    if (ref.type === "third") return ctx.thirdSlotTeam[ref.slot] || null;
    if (ref.type === "winner") { var m = ctx.matches[ref.match]; return m ? m.winner : null; }
    if (ref.type === "loser") { var m2 = ctx.matches[ref.match]; return m2 ? m2.loser : null; }
    return null;
  }

  function decideMatch(home, away, score) {
    var h = score ? num(score.h) : null, a = score ? num(score.a) : null;
    var pen = score && (score.pen === "home" || score.pen === "away") ? score.pen : null;
    var winner = null, loser = null;
    if (home && away && h !== null && a !== null) {
      if (h > a) { winner = home; loser = away; }
      else if (a > h) { winner = away; loser = home; }
      else if (pen) { winner = pen === "home" ? home : away; loser = pen === "home" ? away : home; }
    }
    return { home: home, away: away, homeGoals: h, awayGoals: a, pen: pen, winner: winner, loser: loser };
  }

  function resolveBracket(d) {
    var groups = d.groups || {}, knockout = d.knockout || {};
    var standings = computeStandings(groups);
    var complete = groupsComplete(groups);
    var ranked = rankThirds(standings);
    var qualifiedThirds = ranked.slice(0, 8).map(function (s) { return s.group; }).sort();
    var thirdSlotTeam = {};
    Object.keys(DATA.thirdSlotToMatch).forEach(function (s) { thirdSlotTeam[s] = null; });
    if (complete) {
      var mapping = DATA.annexC[qualifiedThirds.join("")];
      if (mapping) {
        Object.keys(mapping).forEach(function (slot) {
          var gl = mapping[slot].slice(1);
          thirdSlotTeam[slot] = standings[gl] && standings[gl][2] ? standings[gl][2].team : null;
        });
      }
    }
    var matches = {};
    var ctx = { standings: standings, thirdSlotTeam: thirdSlotTeam, matches: matches };
    DATA.knockoutMatches.forEach(function (km) {
      var home = resolveSlot(km.home, ctx);
      var away = resolveSlot(km.away, ctx);
      matches[km.match] = decideMatch(home, away, knockout[String(km.match)]);
    });
    return { standings: standings, qualifiedThirds: qualifiedThirds, thirdSlotTeam: thirdSlotTeam, matches: matches, groupsComplete: complete };
  }

  /* ---------- Guardado ---------- */
  function setStatus(s) {
    var el = document.getElementById("save-text");
    if (!el) return;
    var map = { saving: ["Guardando\u2026", ""], saved: ["Guardado \u2713", "text-pitch"], error: ["Error al guardar", "text-red"], idle: ["Los cambios se guardan automaticamente", "muted"] };
    var m = map[s] || map.idle;
    el.textContent = (BOOT.mode === "admin" ? "\uD83D\uDEE0\uFE0F Resultados reales \u00b7 " : "") + m[0];
    el.className = "" + m[1];
    if (BOOT.mode === "user" && submitted && s !== "saving") {
      el.innerHTML += ' <span class="pill pill-pitch">Confirmada \u2713</span>';
    }
  }

  function save(extra) {
    if (isView()) return Promise.resolve(false);
    setStatus("saving");
    var payload = { data: state };
    if (extra) Object.assign(payload, extra);
    return fetch(BOOT.dataEndpoint, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
    }).then(function (r) {
      if (!r.ok) { setStatus("error"); return false; }
      return r.json().then(function (j) {
        if (j && j.locks) LOCKS = j.locks;
        setStatus("saved");
        return true;
      }).catch(function () { setStatus("saved"); return true; });
    }).catch(function () { setStatus("error"); return false; });
  }

  function scheduleSave() {
    if (isView()) return;
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(function () { save(); }, 900);
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  /* ---------- Confirmacion con aviso de partidos faltantes ---------- */
  function missingMatches() {
    var miss = { groups: [], ko: [] };
    var groupsEditable = !(BOOT.mode === "user" && LOCKS.groupStageComplete);
    if (groupsEditable) {
      DATA.groupMatches.forEach(function (m) {
        var s = state.groups[m.id];
        if (!(s && typeof s.h === "number" && typeof s.a === "number")) miss.groups.push(m);
      });
    }
    var ctx = koContext();
    if (ctx.open) {
      var resolved = resolveBracket({ groups: ctx.groups, knockout: state.knockout });
      DATA.knockoutMatches.forEach(function (km) {
        var rm = resolved.matches[km.match];
        if (rm && rm.home && rm.away && !rm.winner) miss.ko.push(km);
      });
    }
    return miss;
  }

  function doConfirm(confirmBtn) {
    if (saveTimer) clearTimeout(saveTimer);
    save({ submitted: true }).then(function (ok) {
      if (ok) { submitted = true; confirmBtn.textContent = "Actualizar confirmacion"; setStatus("saved"); }
    });
  }

  function onConfirmClick(confirmBtn) {
    var miss = missingMatches();
    if (miss.groups.length + miss.ko.length === 0) { doConfirm(confirmBtn); return; }
    showMissingModal(miss, function () { doConfirm(confirmBtn); });
  }

  function showMissingModal(miss, onConfirm) {
    var overlay = el("div", "modal-overlay");
    var lines = [];
    if (miss.groups.length) lines.push('<li><b>' + miss.groups.length + '</b> partido(s) de la fase de grupos sin marcador.</li>');
    if (miss.ko.length) lines.push('<li><b>' + miss.ko.length + '</b> eliminatoria(s) sin ganador (incluye empates sin penaltis decididos).</li>');
    overlay.innerHTML =
      '<div class="modal card" role="dialog" aria-modal="true">' +
      '<h3 style="margin-top:0">⚠️ Te faltan partidos</h3>' +
      '<p class="muted">Puedes confirmar ahora y seguir editando despues. Los partidos sin rellenar no sumaran puntos hasta que los completes:</p>' +
      '<ul class="muted" style="margin:0 0 16px;padding-left:18px">' + lines.join("") + '</ul>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap">' +
      '<button class="btn btn-ghost" id="modal-cancel">Seguir editando</button>' +
      '<button class="btn btn-primary" id="modal-confirm">Confirmar de todas formas</button>' +
      '</div></div>';
    document.body.appendChild(overlay);
    function close() { if (overlay.parentNode) overlay.parentNode.removeChild(overlay); }
    overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
    overlay.querySelector("#modal-cancel").addEventListener("click", close);
    overlay.querySelector("#modal-confirm").addEventListener("click", function () { close(); onConfirm(); });
  }

  /* ---------- Render ---------- */
  function filledGroups() {
    return DATA.groupMatches.filter(function (m) {
      var s = state.groups[m.id];
      return s && typeof s.h === "number" && typeof s.a === "number";
    }).length;
  }

  function el(tag, cls, html) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html !== undefined) e.innerHTML = html;
    return e;
  }

  function scoreInputs(getH, getA, onH, onA, locked) {
    var wrap = el("div", "score-mid");
    var h = el("input", "score-box"); h.type = "number"; h.min = 0; h.max = 30; h.inputMode = "numeric";
    var sep = el("span", "muted", "-");
    var a = el("input", "score-box"); a.type = "number"; a.min = 0; a.max = 30; a.inputMode = "numeric";
    if (getH() != null) h.value = getH();
    if (getA() != null) a.value = getA();
    if (locked) {
      h.disabled = true; a.disabled = true;
      wrap.className = "score-mid is-locked";
    } else {
      h.addEventListener("input", function () { onH(h.value); });
      a.addEventListener("input", function () { onA(a.value); });
    }
    wrap.appendChild(h); wrap.appendChild(sep); wrap.appendChild(a);
    return wrap;
  }

  function parseGoal(v) {
    if (v === "") return undefined;
    var n = parseInt(v, 10);
    if (isNaN(n) || n < 0) return undefined;
    return Math.min(n, 30);
  }

  function buildGroups(container) {
    var grid = el("div", "grid grid-2");
    DATA.groupLetters.forEach(function (letter) {
      var card = el("div", "card");
      card.style.padding = "16px";
      var head = el("div");
      head.style.cssText = "display:flex;align-items:center;justify-content:space-between;margin-bottom:12px";
      head.innerHTML = "<h3>Grupo " + letter + "</h3>" + (DATA.groups[letter].indexOf(DATA.homeTeam) >= 0 ? '<span class="pill pill-red">Grupo de Espana \uD83C\uDDEA\uD83C\uDDF8</span>' : "");
      card.appendChild(head);

      DATA.groupMatches.filter(function (m) { return m.group === letter; }).forEach(function (m) {
        var lk = lockedGroup(m.id);
        var row = el("div", "match-row" + (lk ? " is-locked" : ""));
        row.style.marginBottom = "8px";
        var left = el("div", "match-side right", teamHtml(m.home));
        var right = el("div", "match-side", (lk ? LOCK_BADGE : "") + teamHtml(m.away));
        var si = scoreInputs(
          function () { return state.groups[m.id] ? state.groups[m.id].h : null; },
          function () { return state.groups[m.id] ? state.groups[m.id].a : null; },
          function (v) { setGroup(m.id, "h", v); },
          function (v) { setGroup(m.id, "a", v); },
          lk
        );
        row.appendChild(left); row.appendChild(si); row.appendChild(right);
        card.appendChild(row);
      });

      var st = el("div");
      st.id = "stand-" + letter;
      card.appendChild(st);
      grid.appendChild(card);
    });
    container.appendChild(grid);
  }

  function updateStandings() {
    var resolved = resolveBracket(state);
    DATA.groupLetters.forEach(function (letter) {
      var rows = resolved.standings[letter];
      var html = '<table class="standings"><thead><tr><th></th><th class="l">Equipo</th><th>PJ</th><th>DG</th><th>Pts</th></tr></thead><tbody>';
      rows.forEach(function (r, i) {
        var rc = i < 2 ? "row-q" : i === 2 ? "row-3" : "row-x";
        var dc = i < 2 ? "dot-q" : i === 2 ? "dot-3" : "dot-x";
        html += '<tr class="' + rc + '"><td><span class="dot ' + dc + '"></span></td><td class="l">' + flagHtml(r.team) + " " + tName(r.team) + "</td><td style=\"text-align:center\">" + r.played + '</td><td style="text-align:center">' + (r.gd > 0 ? "+" + r.gd : r.gd) + '</td><td style="text-align:center"><b>' + r.points + "</b></td></tr>";
      });
      html += "</tbody></table>";
      var node = document.getElementById("stand-" + letter);
      if (node) node.innerHTML = html;
    });
  }

  function setGroup(id, side, v) {
    if (lockedGroup(id)) return;
    var n = parseGoal(v);
    if (!state.groups[id]) state.groups[id] = {};
    if (n === undefined) delete state.groups[id][side]; else state.groups[id][side] = n;
    if (state.groups[id].h === undefined && state.groups[id].a === undefined) delete state.groups[id];
    updateStandings();
    updateTabCount();
    scheduleSave();
  }

  function setKo(numMatch, side, v) {
    if (lockedKo(numMatch)) return;
    var key = String(numMatch);
    var n = parseGoal(v);
    if (!state.knockout[key]) state.knockout[key] = {};
    if (n === undefined) delete state.knockout[key][side]; else state.knockout[key][side] = n;
    var s = state.knockout[key];
    if (typeof s.h === "number" && typeof s.a === "number" && s.h !== s.a) delete s.pen;
    if (s.h === undefined && s.a === undefined && !s.pen) delete state.knockout[key];
    celebrateNext = true;
    updateKnock();
    scheduleSave();
  }

  function setPen(numMatch, pen) {
    if (lockedKo(numMatch)) return;
    var key = String(numMatch);
    if (!state.knockout[key]) state.knockout[key] = {};
    state.knockout[key].pen = pen;
    celebrateNext = true;
    updateKnock();
    scheduleSave();
  }

  var knockBuilt = false;
  var lastChampion = null;
  var celebrateNext = false;
  function buildKnock(container) {
    container.innerHTML = "";
    // banner de campeon (oculto hasta decidir la final)
    var champ = el("div", "champion hidden");
    champ.id = "champion";
    container.appendChild(champ);
    // banda de terceros
    var thirds = el("div", "card");
    thirds.id = "thirds-bar";
    thirds.style.cssText = "display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:12px;margin-bottom:24px";
    container.appendChild(thirds);

    DATA.roundOrder.forEach(function (round) {
      var block = el("div");
      block.style.marginBottom = "24px";
      block.innerHTML = '<h3 style="margin-bottom:12px"><span class="pill pill-brand">' + DATA.roundLabels[round] + "</span></h3>";
      var grid = el("div", "grid grid-2");
      DATA.knockoutMatches.filter(function (m) { return m.round === round; }).forEach(function (km) {
        var lk = lockedKo(km.match);
        var card = el("div", "card ko-card" + (lk ? " is-locked" : ""));
        card.id = "ko-" + km.match;
        card.innerHTML =
          '<div class="ko-meta"><span>Partido ' + km.match + (lk ? " " + LOCK_BADGE : "") + '</span><span id="ko-win-' + km.match + '"></span></div>' +
          '<div style="display:flex;align-items:center;gap:8px">' +
          '<div class="match-side right" id="ko-home-' + km.match + '"></div>' +
          '<div id="ko-score-' + km.match + '"></div>' +
          '<div class="match-side" id="ko-away-' + km.match + '"></div>' +
          "</div>" +
          '<div id="ko-pen-' + km.match + '"></div>';
        // score inputs
        var sc = card.querySelector("#ko-score-" + km.match);
        sc.appendChild(scoreInputs(
          function () { return state.knockout[km.match] ? state.knockout[km.match].h : null; },
          function () { return state.knockout[km.match] ? state.knockout[km.match].a : null; },
          function (v) { setKo(km.match, "h", v); },
          function (v) { setKo(km.match, "a", v); },
          lk
        ));
        grid.appendChild(card);
      });
      block.appendChild(grid);
      container.appendChild(block);
    });
    knockBuilt = true;
  }

  function renderChampion(elc, code) {
    var confetti = "";
    var colors = ["#f5c542", "#6d28d9", "#16a34a", "#ef4444", "#38bdf8", "#f97316"];
    for (var i = 0; i < 24; i++) {
      var left = Math.round(Math.random() * 100);
      var c = colors[i % colors.length];
      var delay = (Math.random() * 0.6).toFixed(2);
      var dur = (1.2 + Math.random() * 0.9).toFixed(2);
      confetti += '<span class="confetti" style="left:' + left + "%;background:" + c + ";animation-delay:" + delay + "s;animation-duration:" + dur + 's"></span>';
    }
    elc.innerHTML =
      confetti +
      '<div class="champ-inner">' +
      '<img class="champ-trophy" src="/static/trophy.svg" alt="Trofeo">' +
      '<div><div class="champ-label">CAMPEON DEL MUNDO</div>' +
      '<div class="champ-team">' + flagHtml(code) + " " + tName(code) + " \uD83C\uDF89</div></div>" +
      "</div>";
  }

  function updateChampion(resolved, scrollIntoView) {
    var elc = document.getElementById("champion");
    if (!elc) return;
    var champ = resolved.matches[104] ? resolved.matches[104].winner : null;
    if (champ) {
      if (lastChampion !== champ) {
        renderChampion(elc, champ);
        elc.classList.remove("hidden");
        // reinicia la animacion
        elc.classList.remove("celebrate");
        void elc.offsetWidth;
        elc.classList.add("celebrate");
        if (scrollIntoView) {
          try { elc.scrollIntoView({ behavior: "smooth", block: "center" }); } catch (e) {}
        }
      }
    } else {
      elc.classList.add("hidden");
      elc.innerHTML = "";
    }
    lastChampion = champ;
  }

  function koLockedHtml(reason) {
    if (reason === "admin-complete") {
      var fg = filledGroups(), total = DATA.groupMatches.length;
      return '<div class="card locked"><div style="font-size:48px">\uD83D\uDD12</div>' +
        "<h3>Completa la fase de grupos</h3>" +
        '<p class="muted" style="max-width:480px">Introduce los <b>' + total + "</b> resultados reales de la fase de grupos para abrir el cuadro de eliminatorias para todos. Llevas <b>" + fg + "</b>.</p>" +
        '<div class="progress" style="max-width:480px"><div style="width:' + (fg / total * 100) + '%"></div></div>' +
        '<button class="btn btn-primary" id="go-groups" type="button">Ir a la fase de grupos</button></div>';
    }
    return '<div class="card locked"><div style="font-size:48px">\uD83D\uDD12</div>' +
      "<h3>Eliminatorias todavia bloqueadas</h3>" +
      '<p class="muted" style="max-width:500px">El cuadro de eliminatorias se abrira cuando el administrador haya introducido todos los resultados de la fase de grupos. ' +
      "Sera el mismo para todos: a partir de ahi predices quien avanza en cada ronda hasta la final.</p>" +
      '<button class="btn btn-ghost" id="go-groups" type="button">Revisar mi fase de grupos</button></div>';
  }

  function updateKnock() {
    var pane = document.getElementById("knock-pane");
    if (!pane) return;
    var ctx = koContext();
    if (!ctx.open) {
      knockBuilt = false;
      pane.innerHTML = koLockedHtml(ctx.reason);
      var gb = pane.querySelector("#go-groups");
      if (gb) gb.addEventListener("click", function () { setTab("groups"); });
      return;
    }
    var resolved = resolveBracket({ groups: ctx.groups, knockout: state.knockout });
    if (!knockBuilt) buildKnock(pane);

    // banda de terceros
    var tb = document.getElementById("thirds-bar");
    if (tb) {
      var h = '<span class="pill pill-amber">8 mejores terceros</span>';
      resolved.qualifiedThirds.forEach(function (g) {
        var t = resolved.standings[g][2].team;
        h += '<span style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.05);padding:4px 8px;border-radius:8px">' + flagHtml(t) + tName(t) + "</span>";
      });
      tb.innerHTML = h;
    }

    DATA.knockoutMatches.forEach(function (km) {
      var m = resolved.matches[km.match];
      var card = document.getElementById("ko-" + km.match);
      if (!card) return;
      card.className = "card ko-card" + (m.winner ? " win" : "");
      var homeEl = document.getElementById("ko-home-" + km.match);
      var awayEl = document.getElementById("ko-away-" + km.match);
      homeEl.innerHTML = teamHtml(m.home);
      awayEl.innerHTML = teamHtml(m.away);
      homeEl.style.fontWeight = m.winner === m.home && m.home ? "700" : "400";
      awayEl.style.fontWeight = m.winner === m.away && m.away ? "700" : "400";
      var winEl = document.getElementById("ko-win-" + km.match);
      winEl.innerHTML = m.winner ? ('<span class="text-pitch">Pasa ' + flagHtml(m.winner) + " " + tName(m.winner) + "</span>") : "";

      // penaltis
      var penEl = document.getElementById("ko-pen-" + km.match);
      var sc = state.knockout[km.match];
      var isDraw = sc && typeof sc.h === "number" && typeof sc.a === "number" && sc.h === sc.a && m.home && m.away;
      if (isDraw) {
        var penLk = lockedKo(km.match);
        var dis = penLk ? " disabled" : "";
        penEl.innerHTML =
          '<div class="pen-box"><p style="text-align:center;font-size:12px;color:#fcd34d;margin:0 0 8px">\u26BD Empate \u2014 \u00bfquien gana en los penaltis?</p>' +
          '<div class="pen-btns">' +
          '<button class="pen-btn ' + (sc.pen === "home" ? "sel" : "") + '" data-m="' + km.match + '" data-s="home"' + dis + '>' + tName(m.home) + "</button>" +
          '<button class="pen-btn ' + (sc.pen === "away" ? "sel" : "") + '" data-m="' + km.match + '" data-s="away"' + dis + '>' + tName(m.away) + "</button>" +
          "</div></div>";
        if (!penLk) {
          penEl.querySelectorAll(".pen-btn").forEach(function (b) {
            b.addEventListener("click", function () { setPen(parseInt(b.getAttribute("data-m"), 10), b.getAttribute("data-s")); });
          });
        }
      } else {
        penEl.innerHTML = "";
      }
    });

    updateChampion(resolved, celebrateNext);
    celebrateNext = false;
  }

  function updateTabCount() {
    var c = document.getElementById("group-count");
    if (c) c.textContent = filledGroups() + "/" + DATA.groupMatches.length;
    var lock = document.getElementById("knock-lock");
    if (lock) lock.style.display = koContext().open ? "none" : "inline";
  }

  function setTab(t) {
    tab = t;
    document.getElementById("tab-groups").classList.toggle("active", t === "groups");
    document.getElementById("tab-knock").classList.toggle("active", t === "knock");
    var ta = document.getElementById("tab-awards");
    if (ta) ta.classList.toggle("active", t === "awards");
    document.getElementById("groups-pane").style.display = t === "groups" ? "" : "none";
    document.getElementById("knock-pane").style.display = t === "knock" ? "" : "none";
    var ap = document.getElementById("awards-pane");
    if (ap) ap.style.display = t === "awards" ? "" : "none";
    if (t === "knock") updateKnock();
  }

  function renderApp() {
    var app = document.getElementById("app");
    app.innerHTML = "";

    if (isView()) {
      var vb = el("div", "savebar");
      vb.innerHTML = '<span class="muted">🔒 Solo lectura — quiniela de <b style="color:#fff">' + (BOOT.owner ? esc(BOOT.owner) : "otro participante") + '</b>.</span>';
      app.appendChild(vb);
    } else if (deadlineClosed()) {
      var cb = el("div", "savebar");
      cb.innerHTML = '<span class="muted">🔒 Las predicciones estan cerradas. Ya no se pueden editar.</span>';
      app.appendChild(cb);
    } else {
      var bar = el("div", "savebar");
      var left = el("span", "muted", "");
      left.innerHTML = '<span id="save-text" class="muted"></span>';
      var right = el("div");
      right.style.cssText = "display:flex;gap:8px";
      var saveBtn = el("button", "btn btn-ghost", "Guardar ahora");
      saveBtn.addEventListener("click", function () { if (saveTimer) clearTimeout(saveTimer); save(); });
      right.appendChild(saveBtn);
      if (BOOT.mode === "user") {
        var confirmBtn = el("button", "btn btn-primary", submitted ? "Actualizar confirmacion" : "Confirmar predicciones");
        confirmBtn.addEventListener("click", function () { onConfirmClick(confirmBtn); });
        right.appendChild(confirmBtn);
      }
      bar.appendChild(left); bar.appendChild(right);
      app.appendChild(bar);
    }

    var tabs = el("div", "tabs");
    tabs.innerHTML =
      '<button class="tab active" id="tab-groups">Fase de grupos <span class="count" id="group-count"></span></button>' +
      '<button class="tab" id="tab-knock">Eliminatorias <span id="knock-lock">\uD83D\uDD12</span></button>' +
      '<button class="tab" id="tab-awards">Premios \u2B50</button>';
    app.appendChild(tabs);
    document.getElementById("tab-groups").addEventListener("click", function () { setTab("groups"); });
    document.getElementById("tab-knock").addEventListener("click", function () { setTab("knock"); });
    document.getElementById("tab-awards").addEventListener("click", function () { setTab("awards"); });

    var gp = el("div"); gp.id = "groups-pane"; app.appendChild(gp);
    var kp = el("div"); kp.id = "knock-pane"; kp.style.display = "none"; app.appendChild(kp);
    var ap = el("div"); ap.id = "awards-pane"; ap.style.display = "none"; app.appendChild(ap);

    buildGroups(gp);
    buildAwards(ap);
    updateStandings();
    updateTabCount();
    updateKnock();
    setStatus("idle");
  }

  /* ---------- Premios individuales: Pichichi y MVP ---------- */
  function awardsLocked() {
    // Editables hasta el cierre global; en vista, solo lectura.
    return anyEditDisabled();
  }

  // Quita acentos y mayusculas para filtrar por similitud.
  function normalize(s) {
    return String(s).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  var COMBO_GROUPS = null;
  function comboGroups() {
    if (COMBO_GROUPS) return COMBO_GROUPS;
    var map = {};
    DATA.players.forEach(function (p) { (map[p.team] = map[p.team] || []).push(p); });
    COMBO_GROUPS = Object.keys(map)
      .sort(function (a, b) { return tName(a).localeCompare(tName(b), "es"); })
      .map(function (c) { return { code: c, name: tName(c), players: map[c] }; });
    return COMBO_GROUPS;
  }

  function renderComboPanel(panel, query) {
    var nq = normalize(query.trim());
    var html = "";
    var any = false;
    comboGroups().forEach(function (g) {
      var countryMatch = nq && normalize(g.name).indexOf(nq) >= 0;
      var ps = g.players.filter(function (p) { return !nq || countryMatch || normalize(p.name).indexOf(nq) >= 0; });
      if (!ps.length) return;
      any = true;
      html += '<div class="combo-group">' + flagHtml(g.code) + "<span>" + esc(g.name) + "</span></div>";
      ps.forEach(function (p) {
        html += '<div class="combo-opt" data-name="' + esc(p.name) + '">' + flagHtml(g.code) + "<span>" + esc(p.name) + "</span></div>";
      });
    });
    var q = query.trim();
    var exact = DATA.players.some(function (p) { return normalize(p.name) === normalize(q); });
    if (q && !exact) {
      html = '<div class="combo-opt combo-custom" data-name="' + esc(q) + '">\u270f\ufe0f Usar \u00ab' + esc(q) + "\u00bb</div>" + html;
      any = true;
    }
    if (!any) html = '<div class="combo-empty muted">Escribe el nombre y se guardara.</div>';
    panel.innerHTML = html;
  }

  function commitAward(kind, field, value) {
    value = (value || "").trim();
    setAward(kind, value);
    field.input.value = value;
    var known = DATA.players.filter(function (p) { return p.name === value; })[0];
    field.flag.innerHTML = known ? flagHtml(known.team) : "";
  }

  function buildAwardField(grid, kind, label, emoji, helper) {
    var current = state[kind] || "";
    var locked = awardsLocked();
    var title = emoji ? (emoji + " " + esc(label)) : esc(label);
    var card = el("div", "card");
    card.style.padding = "20px";

    if (locked) {
      var k0 = DATA.players.filter(function (p) { return p.name === current; })[0];
      card.innerHTML =
        '<h3 style="margin:0 0 4px">' + title + "</h3>" +
        '<p class="muted" style="margin:0 0 12px;font-size:13px">' + esc(helper) + "</p>" +
        '<div class="combo-field combo-readonly">' +
        (current ? ((k0 ? flagHtml(k0.team) : "") + "<span>" + esc(current) + "</span>")
                 : '<span class="muted">Sin elegir</span>') + "</div>";
      grid.appendChild(card);
      return;
    }

    card.innerHTML =
      '<h3 style="margin:0 0 4px">' + title + "</h3>" +
      '<p class="muted" style="margin:0 0 12px;font-size:13px">' + esc(helper) + "</p>" +
      '<div class="combo">' +
        '<div class="combo-field">' +
          '<span class="combo-flag"></span>' +
          '<input class="combo-input" autocomplete="off" spellcheck="false" placeholder="Busca o escribe un jugador\u2026">' +
          '<span class="combo-caret">\u25be</span>' +
        "</div>" +
        '<div class="combo-panel" hidden></div>' +
      "</div>";
    grid.appendChild(card);

    var combo = card.querySelector(".combo");
    var input = combo.querySelector(".combo-input");
    var panel = combo.querySelector(".combo-panel");
    var flag = combo.querySelector(".combo-flag");
    var field = { input: input, flag: flag };

    input.value = current;
    var known = DATA.players.filter(function (p) { return p.name === current; })[0];
    flag.innerHTML = known ? flagHtml(known.team) : "";

    function open() { renderComboPanel(panel, input.value); panel.hidden = false; combo.classList.add("open"); }
    function close() { panel.hidden = true; combo.classList.remove("open"); }

    input.addEventListener("focus", open);
    input.addEventListener("input", open);
    input.addEventListener("keydown", function (e) { if (e.key === "Escape") { close(); input.blur(); } });
    input.addEventListener("blur", function () {
      setTimeout(function () { commitAward(kind, field, input.value); close(); }, 120);
    });
    panel.addEventListener("mousedown", function (e) {
      var opt = e.target.closest(".combo-opt");
      if (!opt) return;
      e.preventDefault();  // conserva el foco para que el blur no pise el valor
      commitAward(kind, field, opt.getAttribute("data-name"));
      close();
    });
  }

  function buildAwards(container) {
    container.innerHTML = "";
    var intro = el("div", "card");
    intro.style.cssText = "padding:16px 20px;margin-bottom:16px";
    var pichichiLabel = BOOT.mode === "admin" ? "Pichichi" : "Mi Pichichi";
    var mvpLabel = BOOT.mode === "admin" ? "MVP" : "Mi MVP";
    intro.innerHTML =
      '<div style="font-weight:700;color:#fff">\uD83C\uDFC5 Premios individuales</div>' +
      '<p class="muted" style="margin:4px 0 0;font-size:13px">' +
      (BOOT.mode === "admin"
        ? "Fija el Pichichi (maximo goleador) y el MVP reales del torneo. Se usan para puntuar a los participantes."
        : "Elige al <b>Pichichi</b> (maximo goleador) y al <b>MVP</b> del torneo. Aciertas = <b>+1 punto</b> cada uno. " +
          "Puedes elegir un candidato de la lista o escribir \"Otro\".") +
      "</p>";
    container.appendChild(intro);
    var grid = el("div", "grid grid-2");
    container.appendChild(grid);
    buildAwardField(grid, "pichichi", pichichiLabel, "⚽", "Maximo goleador del Mundial.");
    buildAwardField(grid, "mvp", mvpLabel, "\u2B50", "Mejor jugador (MVP) del torneo.");
  }

  function setAward(kind, value) {
    if (awardsLocked()) return;
    state[kind] = value || "";
    scheduleSave();
  }

  /* ---------- Control de cierre (admin) ---------- */
  function wireDeadline() {
    var input = document.getElementById("deadline-input");
    if (!input) return;
    var msg = document.getElementById("deadline-msg");
    function post(value) {
      msg.textContent = "Guardando…"; msg.className = "muted";
      fetch("/api/admin/deadline", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ deadline: value })
      }).then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
        .then(function (res) {
          if (!res.ok) { msg.textContent = (res.j && res.j.error) || "No se pudo guardar."; msg.className = "text-red"; return; }
          msg.className = "muted";
          if (res.j.deadline) { msg.textContent = "✓ Cierre fijado para " + res.j.deadline.replace("T", " ") + "."; }
          else { msg.textContent = "Sin cierre programado. Solo se bloquean los partidos con resultado real."; input.value = ""; }
        }).catch(function () { msg.textContent = "No se pudo conectar."; msg.className = "text-red"; });
    }
    document.getElementById("deadline-save").addEventListener("click", function () { post(input.value); });
    document.getElementById("deadline-clear").addEventListener("click", function () { input.value = ""; post(""); });
  }

  /* ---------- Gestion de participantes (admin) ---------- */
  function renderUsers(list, users, reload) {
    if (!users.length) { list.textContent = "No hay participantes todavia."; return; }
    var html = '<table class="rank-table"><thead><tr><th class="l">Participante</th><th class="l">Alta</th><th></th></tr></thead><tbody>';
    users.forEach(function (u) {
      var tag = u.isAdmin ? ' <span class="pill pill-brand" style="font-size:10px">admin</span>' : "";
      var when = u.createdAt ? esc(String(u.createdAt).slice(0, 10)) : "";
      var act = u.isAdmin
        ? '<span class="muted" style="font-size:12px">—</span>'
        : '<button class="btn btn-ghost btn-del" data-id="' + u.id + '" data-name="' + esc(u.name) + '" style="padding:4px 10px;font-size:13px;color:#fca5a5">Eliminar</button>';
      html += "<tr><td><b>" + esc(u.name) + "</b>" + tag + '</td><td class="muted" style="font-size:12px">' + when + '</td><td style="text-align:right">' + act + "</td></tr>";
    });
    html += "</tbody></table>";
    list.innerHTML = html;
    list.querySelectorAll(".btn-del").forEach(function (b) {
      b.addEventListener("click", function () {
        var id = b.getAttribute("data-id"), name = b.getAttribute("data-name");
        if (!window.confirm('¿Eliminar a "' + name + '" y todas sus predicciones? Esta accion no se puede deshacer.')) return;
        b.disabled = true; b.textContent = "Eliminando…";
        fetch("/api/admin/users/delete", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: parseInt(id, 10) }) })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            if (!res.ok) { window.alert((res.j && res.j.error) || "No se pudo eliminar."); b.disabled = false; b.textContent = "Eliminar"; return; }
            reload();
          }).catch(function () { window.alert("No se pudo conectar."); b.disabled = false; b.textContent = "Eliminar"; });
      });
    });
  }

  function wireUsers() {
    var list = document.getElementById("users-list");
    if (!list) return;
    function load() {
      list.textContent = "Cargando…";
      fetch("/api/admin/users", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (j) {
        renderUsers(list, (j && j.users) || [], load);
      }).catch(function () { list.textContent = "No se pudo cargar la lista de participantes."; });
    }
    var reload = document.getElementById("users-reload");
    if (reload) reload.addEventListener("click", load);
    load();
  }

  /* ---------- Init ---------- */
  if (BOOT.mode === "admin") { wireDeadline(); wireUsers(); }

  Promise.all([
    fetch("/api/bootstrap").then(function (r) { return r.json(); }),
    fetch(BOOT.dataEndpoint).then(function (r) { return r.json(); })
  ]).then(function (res) {
    DATA = res[0];
    var init = res[1] || {};
    if (init.error) {
      document.getElementById("app").innerHTML =
        '<div class="card" style="padding:24px"><p class="muted" style="margin:0">' + esc(init.error) + "</p></div>";
      return;
    }
    state = init.data || { groups: {}, knockout: {}, pichichi: "", mvp: "" };
    if (!state.groups) state.groups = {};
    if (!state.knockout) state.knockout = {};
    if (typeof state.pichichi !== "string") state.pichichi = "";
    if (typeof state.mvp !== "string") state.mvp = "";
    REAL_GROUPS = init.realGroups || {};
    submitted = !!init.submitted;
    if (init.locks) LOCKS = init.locks;
    renderApp();
  }).catch(function () {
    document.getElementById("app").innerHTML = '<div class="card muted" style="padding:24px">No se pudieron cargar los datos. Recarga la pagina.</div>';
  });
})();
