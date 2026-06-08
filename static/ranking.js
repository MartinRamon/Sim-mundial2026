/* Ranking interactivo. Sin dependencias externas. */
(function () {
  "use strict";
  var openRow = null;

  var ME = (typeof window.__ME__ !== "undefined") ? window.__ME__ : null;

  var TROPHY = '<img class="rk-trophy" src="/static/wc-trophy.svg" alt="Campeon" title="Campeon del Mundo">';

  function medal(pos) {
    // El primer clasificado luce el trofeo de la Copa del Mundo.
    return pos === 1 ? TROPHY : pos === 2 ? "\uD83E\uDD48" : pos === 3 ? "\uD83E\uDD49" : String(pos);
  }
  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function render(json) {
    var rows = json.ranking || [];
    var hasResults = json.hasResults;
    document.getElementById("rk-sub").textContent = hasResults
      ? "Puntuaciones segun los resultados reales introducidos por el admin."
      : "Aun no hay resultados reales. El ranking se activara cuando el admin empiece a introducirlos.";

    var podium = document.getElementById("rk-podium");
    if (rows.length >= 3 && hasResults) {
      var order = [rows[1], rows[0], rows[2]];
      var heights = [90, 130, 70];
      var grad = ["rgba(203,213,225,0.2)", "rgba(245,158,11,0.3)", "rgba(180,83,9,0.2)"];
      var realPos = [2, 1, 3];
      var h = '<div class="card podium">';
      order.forEach(function (r, i) {
        h += '<div class="podium-col"><div style="font-size:24px;margin-bottom:8px">' + medal(realPos[i]) +
          '</div><div style="font-weight:700;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + esc(r.name) +
          '</div><div class="text-pitch" style="font-size:18px;font-weight:800;margin-bottom:8px">' + r.total +
          '</div><div class="podium-bar" style="height:' + heights[i] + "px;background:linear-gradient(to top," + grad[i] + ",transparent)\"></div></div>";
      });
      h += "</div>";
      podium.innerHTML = h;
    } else {
      podium.innerHTML = "";
    }

    var t = document.getElementById("rk-table");
    if (rows.length === 0) {
      t.innerHTML = '<div style="padding:40px;text-align:center" class="muted">Todavia no hay participantes con predicciones.</div>';
      return;
    }
    var html = '<table class="rank-table"><thead><tr><th class="l">#</th><th class="l">Participante</th><th>Grupos</th><th>Elim.</th><th>Extra</th><th style="text-align:right">Total</th></tr></thead><tbody>';
    rows.forEach(function (r, i) {
      var pos = i + 1;
      var draft = r.submitted ? "" : ' <span class="muted" style="font-size:10px">borrador</span>';
      var youBadge = (ME && r.name === ME) ? ' <span class="pill pill-brand" style="font-size:10px">T\u00fa</span>' : "";
      var extra = r.extraPoints || 0;
      var extraCell = extra > 0 ? '<span class="text-pitch">+' + extra + "</span>"
        : extra < 0 ? '<span class="text-red">' + extra + "</span>"
        : '<span style="color:#4b5563">0</span>';
      html += '<tr class="clickable' + (pos <= 3 ? " top" : "") + ((ME && r.name === ME) ? " me" : "") + '" data-i="' + i + '">' +
        '<td style="font-size:18px;font-weight:700">' + (hasResults ? medal(pos) : pos) + "</td>" +
        '<td><b>' + esc(r.name) + "</b>" + youBadge + draft + "</td>" +
        '<td style="text-align:center">' + r.groupPoints + "</td>" +
        '<td style="text-align:center">' + r.knockoutPoints + "</td>" +
        '<td style="text-align:center">' + extraCell + "</td>" +
        '<td class="rank-total">' + r.total + "</td></tr>";
      if (openRow === r.name) {
        var ver = json.deadlinePassed
          ? '<a class="btn btn-ghost" style="padding:6px 12px;font-size:13px" href="/ver?name=' + encodeURIComponent(r.name) + '">\uD83D\uDC41\uFE0F Ver quiniela completa</a>'
          : '<span class="muted" style="font-size:12px">\uD83D\uDC41\uFE0F La quiniela podra verse cuando se cierren las predicciones.</span>';
        function bonus(label, v) {
          v = v || 0;
          var cls = v > 0 ? "text-pitch" : (v < 0 ? "text-red" : "");
          var style = v === 0 ? "color:#6b7280" : "";
          var txt = (v > 0 ? "+" : "") + v;
          return "<span>" + label + ": <b class=\"" + cls + "\" style=\"" + style + "\">" + txt + "</b></span>";
        }
        html += '<tr style="background:rgba(0,0,0,0.2)"><td colspan="6"><div style="display:flex;flex-wrap:wrap;gap:16px;font-size:14px;align-items:center" class="muted">' +
          "<span>\uD83C\uDFAF Exactos: <b style=\"color:#fff\">" + r.exactHits + "</b></span>" +
          "<span>\u2705 Ganadores: <b style=\"color:#fff\">" + r.winnerHits + "</b></span>" +
          "<span>Grupos: <b style=\"color:#fff\">" + r.groupPoints + "</b></span>" +
          "<span>Elim.: <b style=\"color:#fff\">" + r.knockoutPoints + "</b></span>" +
          bonus("\uD83C\uDFC6 Campeon", r.championBonus) +
          bonus("\uD83C\uDDEA\uD83C\uDDF8 Espana", r.spainBonus) +
          bonus("\uD83D\uDC5F Pichichi", r.pichichiBonus) +
          bonus("\u2B50 MVP", r.mvpBonus) +
          '<span style="margin-left:auto">' + ver + "</span>" +
          "</div></td></tr>";
      }
    });
    html += "</tbody></table>";
    t.innerHTML = html;
    t.querySelectorAll("tr.clickable").forEach(function (tr) {
      tr.addEventListener("click", function () {
        var name = rows[parseInt(tr.getAttribute("data-i"), 10)].name;
        openRow = openRow === name ? null : name;
        render(json);
      });
    });
  }

  /* ---------- Grafico de evolucion del ranking ---------- */
  var CHART_COLORS = ["#22c55e", "#f59e0b", "#38bdf8", "#a855f7", "#ef4444", "#14b8a6", "#eab308", "#fb7185", "#60a5fa", "#c084fc"];
  var SHORT_STAGE = { "Jornada 1": "J1", "Jornada 2": "J2", "Jornada 3": "J3", "Dieciseisavos": "16avos", "Octavos": "8vos", "Cuartos": "4tos", "Semis": "Semis", "Final": "Final" };

  function shortName(n) { return n.length > 14 ? n.slice(0, 13) + "…" : n; }

  function renderHistory(hist) {
    var box = document.getElementById("rk-history");
    if (!box) return;
    if (!hist || !hist.hasData || !hist.series || !hist.series.length || !hist.stages || hist.stages.length < 2) {
      box.innerHTML = "";
      return;
    }
    var stages = hist.stages;
    var series = hist.series.slice();
    var shown = series.slice(0, 8);
    if (ME && !shown.some(function (s) { return s.name === ME; })) {
      var mine = series.filter(function (s) { return s.name === ME; })[0];
      if (mine) shown.push(mine);
    }
    var nS = stages.length;
    var maxPos = 1;
    shown.forEach(function (s) { s.positions.forEach(function (p) { if (p > maxPos) maxPos = p; }); });

    var padL = 30, padR = 128, padT = 18, padB = 28, stepY = 30, stepX = 92;
    var plotW = (nS - 1) * stepX;
    var W = padL + plotW + padR;
    var H = padT + padB + (maxPos - 1) * stepY;
    function X(i) { return padL + i * stepX; }
    function Y(p) { return padT + (p - 1) * stepY; }

    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" class="rk-chart-svg" role="img" aria-label="Evolucion del ranking">';
    for (var p = 1; p <= maxPos; p++) {
      svg += '<line x1="' + padL + '" y1="' + Y(p) + '" x2="' + (padL + plotW) + '" y2="' + Y(p) + '" stroke="rgba(255,255,255,0.06)"/>';
      svg += '<text x="' + (padL - 8) + '" y="' + (Y(p) + 4) + '" text-anchor="end" fill="#6b7280" font-size="11">' + p + "</text>";
    }
    stages.forEach(function (st, i) {
      svg += '<text x="' + X(i) + '" y="' + (H - 9) + '" text-anchor="middle" fill="#9ca3af" font-size="11">' + esc(SHORT_STAGE[st] || st) + "</text>";
    });
    shown.forEach(function (s, idx) {
      var isMe = !!(ME && s.name === ME);
      var color = isMe ? "#ffffff" : CHART_COLORS[idx % CHART_COLORS.length];
      var pts = s.positions.map(function (pos, i) { return X(i) + "," + Y(pos); }).join(" ");
      svg += '<polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="' + (isMe ? 3 : 2) + '" stroke-linejoin="round" stroke-linecap="round" opacity="' + (isMe ? 1 : 0.9) + '"/>';
      s.positions.forEach(function (pos, i) {
        svg += '<circle cx="' + X(i) + '" cy="' + Y(pos) + '" r="' + (isMe ? 4 : 3) + '" fill="' + color + '"/>';
      });
      var lastP = s.positions[s.positions.length - 1];
      svg += '<text x="' + (padL + plotW + 8) + '" y="' + (Y(lastP) + 4) + '" fill="' + color + '" font-size="12" font-weight="' + (isMe ? 700 : 500) + '">' + esc(shortName(s.name)) + "</text>";
    });
    svg += "</svg>";

    box.innerHTML =
      '<div class="card" style="padding:20px;margin-bottom:16px">' +
      '<h3 style="margin:0 0 4px">📈 Evolucion del ranking</h3>' +
      '<p class="muted" style="margin:0 0 12px;font-size:13px">Posicion al cierre de cada fase (1 = lider). Se muestran los mejores' + (ME ? " y tu" : "") + ".</p>" +
      '<div class="rk-chart-scroll">' + svg + "</div>" +
      "</div>";
  }

  function loadHistory() {
    fetch("/api/ranking-history", { cache: "no-store" })
      .then(function (r) { return r.json(); })
      .then(renderHistory)
      .catch(function () {});
  }

  window.loadRanking = function () {
    fetch("/api/ranking", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (j) {
      render(j);
      var u = document.getElementById("rk-updated");
      if (u) u.textContent = "Actualizado " + new Date().toLocaleTimeString("es-ES");
    });
    loadHistory();
  };

  loadRanking();
  setInterval(loadRanking, 30000);
})();
