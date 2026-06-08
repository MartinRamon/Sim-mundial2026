/* Estadisticas agregadas del grupo. Sin dependencias externas. */
(function () {
  "use strict";
  var DATA = null;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function flag(code) {
    if (!DATA || !DATA.teams[code]) return "";
    return '<img class="flag" src="/static/flags/' + DATA.teams[code].iso + '.svg" alt="" loading="lazy"> ';
  }

  function card(title, inner) {
    return '<div class="card stat-card" style="padding:20px"><h3 style="margin:0 0 12px">' + title + "</h3>" + inner + "</div>";
  }

  function statRow(label, pct, count, total, cls) {
    var pctTxt = total ? ' <span class="muted">(' + Math.round(count * 100 / total) + "%)</span>" : "";
    return '<div class="stat-row">' +
      '<div class="stat-label">' + label + "</div>" +
      '<div class="stat-bar"><div class="stat-bar-fill ' + (cls || "") + '" style="width:' + pct + '%"></div></div>' +
      '<div class="stat-val">' + (count != null ? count + pctTxt : pct + "%") + "</div>" +
      "</div>";
  }

  function toplistCard(title, items, total) {
    if (!items || !items.length) return card(title, '<p class="muted" style="margin:0">Sin datos todavia.</p>');
    var rows = items.map(function (it) {
      var pct = total ? Math.round(it.count * 100 / total) : 0;
      return statRow(flag(it.team) + esc(it.name), pct, it.count, total);
    }).join("");
    return card(title, rows);
  }

  function spainCard(fate, total) {
    if (!fate || !fate.length) return "";
    var rows = fate.map(function (f) {
      var pct = total ? Math.round(f.count * 100 / total) : 0;
      return statRow(esc(f.label), pct, f.count, total, "red");
    }).join("");
    return card("🇪🇸 ¿Hasta donde llega Espana? (segun la fase de grupos prevista)", rows);
  }

  function extremesCard(s) {
    function box(label, m, cls) {
      if (!m) return "";
      return '<div class="extreme ' + cls + '">' +
        '<div class="muted" style="font-size:12px">' + label + "</div>" +
        '<div style="font-weight:700;color:#fff">' + esc(m.homeName) + " " + m.real.h + "–" + m.real.a + " " + esc(m.awayName) + "</div>" +
        '<div class="muted" style="font-size:13px">Grupo ' + m.group + " · J" + m.matchday + " · acierto del ganador " + m.winnerPct + "%</div>" +
        "</div>";
    }
    if (!s.easiest && !s.hardest) return "";
    return card("🎯 Aciertos destacados",
      '<div class="grid grid-2">' + box("Mas acertado", s.easiest, "ok") + box("Mas fallado", s.hardest, "bad") + "</div>");
  }

  function perMatchdayCard(md) {
    if (!md || !md.length) return "";
    var rows = md.map(function (m) {
      return statRow("Jornada " + m.matchday, m.winnerPct, null, 0);
    }).join("");
    return card("📅 Acierto del ganador por jornada", rows);
  }

  function perMatchCard(pm) {
    if (!pm || !pm.length) return "";
    var rows = pm.map(function (m) {
      return "<tr><td class=\"l\">" + esc(m.homeName) +
        ' <span class="muted">' + m.real.h + "–" + m.real.a + "</span> " + esc(m.awayName) + "</td>" +
        '<td style="text-align:center">' + m.winnerPct + "%</td>" +
        '<td style="text-align:center">' + m.exactPct + "%</td>" +
        '<td style="text-align:center" class="muted">' + m.n + "</td></tr>";
    }).join("");
    return '<div class="card" style="padding:0;overflow:hidden;margin-top:16px">' +
      '<h3 style="margin:0;padding:20px 20px 0">📋 Detalle por partido</h3>' +
      '<div style="overflow-x:auto"><table class="rank-table stat-table">' +
      '<thead><tr><th class="l">Partido (resultado real)</th><th>% ganador</th><th>% exacto</th><th>Predic.</th></tr></thead>' +
      "<tbody>" + rows + "</tbody></table></div></div>";
  }

  function render(s) {
    var root = document.getElementById("stats");
    var sub = document.getElementById("st-sub");
    if (sub) {
      sub.textContent = s.totalUsers
        ? s.totalUsers + " participante(s) con predicciones · " +
          (s.ratedMatches ? s.ratedMatches + " partido(s) con resultado real." : "aun sin resultados reales.")
        : "Todavia no hay participantes con predicciones.";
    }
    if (!s.totalUsers) {
      root.innerHTML = '<div class="card" style="padding:40px;text-align:center"><span class="muted">Sin datos todavia. Las estadisticas apareceran cuando haya participantes.</span></div>';
      return;
    }
    var html = '<div class="grid grid-2">' +
      toplistCard("🏆 Campeon mas elegido", s.champions, s.totalUsers) +
      toplistCard("🥇 Finalistas mas repetidos", s.finalists, s.totalUsers) +
      "</div>";
    html += spainCard(s.spainFate, s.totalUsers);
    if (s.ratedMatches) {
      html += extremesCard(s);
      html += perMatchdayCard(s.perMatchday);
      html += perMatchCard(s.perMatch);
    } else {
      html += '<div class="card" style="padding:20px"><span class="muted">Cuando el admin introduzca resultados reales veras aqui los porcentajes de acierto por partido y jornada.</span></div>';
    }
    root.innerHTML = html;
  }

  Promise.all([
    fetch("/api/bootstrap").then(function (r) { return r.json(); }),
    fetch("/api/stats", { cache: "no-store" }).then(function (r) { return r.json(); })
  ]).then(function (res) {
    DATA = res[0];
    render(res[1] || {});
  }).catch(function () {
    document.getElementById("stats").innerHTML = '<div class="card" style="padding:24px"><span class="muted">No se pudieron cargar las estadisticas. Recarga la pagina.</span></div>';
  });
})();
