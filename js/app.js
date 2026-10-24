/**
 * LibreGol TV — Core Interactive Engine (Phase 3)
 * Full utility sports platform: Live Scoreboard (Promiedos/Flashscore style),
 * Country Clocks & Countdowns, Timezone Converter, Dynamic Filtering, and Community Prediction Voting.
 */

// --- Global Voting Engine ---
window.VotingEngine = window.VotingEngine || (function() {
  const STORAGE_PREFIX = "libregol_vote_";

  function getStoredVote(matchId) {
    try {
      return localStorage.getItem(STORAGE_PREFIX + matchId);
    } catch (e) {
      return null;
    }
  }

  function setStoredVote(matchId, choice) {
    try {
      localStorage.setItem(STORAGE_PREFIX + matchId, choice);
    } catch (e) {
      console.warn("LocalStorage unavailable", e);
    }
  }

  function calculatePercentages(votes) {
    const v1 = (votes && votes.team1) || 0;
    const vDraw = (votes && votes.draw) || 0;
    const v2 = (votes && votes.team2) || 0;
    const total = v1 + vDraw + v2;
    if (total === 0) {
      return { team1: 33, draw: 34, team2: 33, total: 0 };
    }
    const p1 = Math.round((v1 / total) * 100);
    const pDraw = Math.round((vDraw / total) * 100);
    const p2 = 100 - (p1 + pDraw);
    return { team1: p1, draw: pDraw, team2: p2, total: total };
  }

  function castVote(matchId, choice) {
    const existing = getStoredVote(matchId);
    if (existing) {
      alert("¡Ya has registrado tu pronóstico para este encuentro!");
      return;
    }

    const matches = window.LIBREGOL_MATCHES || [];
    const match = matches.find(m => m.id === matchId);
    if (!match) return;

    if (!match.votes) {
      match.votes = { team1: 100, draw: 50, team2: 100 };
    }
    match.votes[choice] = (match.votes[choice] || 0) + 1;
    setStoredVote(matchId, choice);

    // Update any matching voting widgets in the DOM
    const widgets = document.querySelectorAll(`[data-match-voting="${matchId}"]`);
    widgets.forEach(widget => {
      const perc = calculatePercentages(match.votes);
      const totalEl = widget.querySelector(".total-votes-count");
      if (totalEl) totalEl.textContent = `${perc.total.toLocaleString()} votos`;

      const p1El = widget.querySelector(".perc-team1");
      if (p1El) p1El.textContent = `${perc.team1}%`;
      const pDrawEl = widget.querySelector(".perc-draw");
      if (pDrawEl) pDrawEl.textContent = `${perc.draw}%`;
      const p2El = widget.querySelector(".perc-team2");
      if (p2El) p2El.textContent = `${perc.team2}%`;

      const b1 = widget.querySelector(".vote-bar-team1");
      if (b1) b1.style.width = `${perc.team1}%`;
      const bDraw = widget.querySelector(".vote-bar-draw");
      if (bDraw) bDraw.style.width = `${perc.draw}%`;
      const b2 = widget.querySelector(".vote-bar-team2");
      if (b2) b2.style.width = `${perc.team2}%`;

      const btns = widget.querySelectorAll(".vote-btn, .vote-pill");
      btns.forEach(b => b.classList.remove("voted"));
      const targetBtn = widget.querySelector(`[data-choice="${choice}"]`);
      if (targetBtn) targetBtn.classList.add("voted");

      const feedback = widget.querySelector(".vote-feedback-msg");
      if (feedback) {
        feedback.style.display = "block";
        feedback.innerHTML = `✓ ¡Pronóstico registrado con éxito! (${perc.total.toLocaleString()} votos totales)`;
      }
    });
  }

  function renderVotingHtml(match, isCompact) {
    const userVote = getStoredVote(match.id);
    const perc = calculatePercentages(match.votes);

    if (isCompact) {
      return `
        <div class="row-voting" data-match-voting="${match.id}">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; font-size: 0.775rem; font-weight: 700; color: #64748b;">
            <span>🗳️ Pronóstico de los aficionados</span>
            <span class="total-votes-count">${perc.total.toLocaleString()} votos</span>
          </div>
          <div class="vote-pills-row" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.4rem;">
            <button type="button" class="vote-pill ${userVote === 'team1' ? 'voted' : ''}" data-choice="team1"
                    onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'team1')" 
                    style="padding: 0.4rem; font-size: 0.8rem; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px; background: white; cursor: pointer; display: flex; flex-direction: column; align-items: center;">
              <span>${match.homeTeam}</span>
              <span class="perc-team1" style="font-size: 0.725rem; color: #16a34a;">${perc.team1}%</span>
            </button>
            <button type="button" class="vote-pill ${userVote === 'draw' ? 'voted' : ''}" data-choice="draw"
                    onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'draw')" 
                    style="padding: 0.4rem; font-size: 0.8rem; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px; background: white; cursor: pointer; display: flex; flex-direction: column; align-items: center;">
              <span>Empate</span>
              <span class="perc-draw" style="font-size: 0.725rem; color: #64748b;">${perc.draw}%</span>
            </button>
            <button type="button" class="vote-pill ${userVote === 'team2' ? 'voted' : ''}" data-choice="team2"
                    onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'team2')" 
                    style="padding: 0.4rem; font-size: 0.8rem; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px; background: white; cursor: pointer; display: flex; flex-direction: column; align-items: center;">
              <span>${match.awayTeam}</span>
              <span class="perc-team2" style="font-size: 0.725rem; color: #2563eb;">${perc.team2}%</span>
            </button>
          </div>
          <div class="vote-bar-container" style="display: flex; height: 6px; border-radius: 9999px; overflow: hidden; margin-top: 0.5rem; background: #e2e8f0;">
            <div class="vote-bar-team1" style="width: ${perc.team1}%; background: #16a34a; transition: width 0.4s ease;"></div>
            <div class="vote-bar-draw" style="width: ${perc.draw}%; background: #94a3b8; transition: width 0.4s ease;"></div>
            <div class="vote-bar-team2" style="width: ${perc.team2}%; background: #2563eb; transition: width 0.4s ease;"></div>
          </div>
          <div class="vote-feedback-msg" style="display: ${userVote ? 'block' : 'none'}; font-size: 0.75rem; color: #16a34a; font-weight: 700; margin-top: 0.35rem; text-align: center;">
            ${userVote ? `✓ Tu pronóstico: <strong>${userVote === 'team1' ? match.homeTeam : (userVote === 'team2' ? match.awayTeam : 'Empate')}</strong>` : ''}
          </div>
        </div>
      `;
    }

    return `
      <div class="voting-section" data-match-voting="${match.id}" style="padding: 0.85rem 1rem; background: #fcfcfd; border-top: 1px solid #e2e8f0;">
        <div class="voting-header" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.775rem; font-weight: 700; color: #64748b; text-transform: uppercase; margin-bottom: 0.6rem;">
          <span>🗳️ Pronóstico de la afición</span>
          <span class="total-votes-count">${perc.total.toLocaleString()} votos</span>
        </div>
        <div class="voting-buttons" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0.5rem;">
          <button type="button" class="vote-btn ${userVote === 'team1' ? 'voted' : ''}" data-choice="team1"
                  onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'team1')" 
                  style="padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; background: white; font-size: 0.8125rem; font-weight: 700; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 0.2rem;">
            <span>${match.homeTeam}</span>
            <span class="vote-perc perc-team1" style="color: #16a34a;">${perc.team1}%</span>
          </button>
          <button type="button" class="vote-btn ${userVote === 'draw' ? 'voted' : ''}" data-choice="draw"
                  onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'draw')" 
                  style="padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; background: white; font-size: 0.8125rem; font-weight: 700; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 0.2rem;">
            <span>Empate</span>
            <span class="vote-perc perc-draw" style="color: #64748b;">${perc.draw}%</span>
          </button>
          <button type="button" class="vote-btn ${userVote === 'team2' ? 'voted' : ''}" data-choice="team2"
                  onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'team2')" 
                  style="padding: 0.5rem; border-radius: 8px; border: 1px solid #cbd5e1; background: white; font-size: 0.8125rem; font-weight: 700; cursor: pointer; display: flex; flex-direction: column; align-items: center; gap: 0.2rem;">
            <span>${match.awayTeam}</span>
            <span class="vote-perc perc-team2" style="color: #2563eb;">${perc.team2}%</span>
          </button>
        </div>
        <div class="vote-bar-container" style="display: flex; height: 6px; border-radius: 9999px; overflow: hidden; margin-top: 0.6rem; background: #e2e8f0;">
          <div class="vote-bar-team1" style="width: ${perc.team1}%; background: #16a34a; transition: width 0.4s ease;"></div>
          <div class="vote-bar-draw" style="width: ${perc.draw}%; background: #94a3b8; transition: width 0.4s ease;"></div>
          <div class="vote-bar-team2" style="width: ${perc.team2}%; background: #2563eb; transition: width 0.4s ease;"></div>
        </div>
        <div class="vote-feedback-msg" style="display: ${userVote ? 'block' : 'none'}; font-size: 0.775rem; color: #16a34a; font-weight: 700; margin-top: 0.4rem; text-align: center;">
          ${userVote ? `✓ Tu pronóstico: <strong>${userVote === 'team1' ? match.homeTeam : (userVote === 'team2' ? match.awayTeam : 'Empate')}</strong>` : ''}
        </div>
      </div>
    `;
  }

  return {
    vote: castVote,
    render: renderVotingHtml
  };
})();
var VotingEngine = window.VotingEngine;


// --- Main Application Lifecycle ---
document.addEventListener("DOMContentLoaded", () => {
  let currentTimezone = window.DEFAULT_TIMEZONE || "auto";
  let activeCategory = window.DEFAULT_CATEGORY || "all";
  let activeStatusTab = "all"; // 'all', 'LIVE', 'FINISHED', 'UPCOMING'
  let searchQuery = "";

  const matchesContainer = document.getElementById("menu") || document.getElementById("matchesContainer");
  const searchInput = document.getElementById("searchInput");
  const searchClearBtn = document.getElementById("searchClearBtn");
  const timezoneSelect = document.getElementById("timezoneSelect");
  const matchCounter = document.getElementById("matchCounter");
  const agendaDateTitle = document.getElementById("agendaDateTitle") || document.getElementById("title-agenda");
  const agendaHeaderBanner = document.getElementById("agendaHeaderBanner");

  // Sync initial timezone in select dropdown
  if (timezoneSelect && currentTimezone !== "auto") {
    timezoneSelect.value = currentTimezone;
  }

  // 1. Dynamic Date Header
  function updateAgendaTitle() {
    try {
      const now = new Date();
      if (window.IS_TOMORROW_VIEW) {
        now.setDate(now.getDate() + 1);
      }
      const day = now.getDate();
      const months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
      const month = months[now.getMonth()];
      const year = now.getFullYear();
      const prefixText = window.IS_TOMORROW_VIEW ? "Cartelera para Mañana" : (window.IS_MARCADORES_VIEW ? "Marcador en Vivo" : "Agenda Deportiva");
      const text = `${prefixText} - ${day} de ${month} de ${year}`;
      if (agendaDateTitle) agendaDateTitle.textContent = text;
      if (agendaHeaderBanner) agendaHeaderBanner.textContent = text;
    } catch (e) {
      if (agendaDateTitle) agendaDateTitle.textContent = "Agenda Deportiva";
    }
  }
  updateAgendaTitle();

  // 2. Accurate Timezone Formatter & Date Calculators
  function formatMatchTime(utcString, tzOption) {
    const date = new Date(utcString);
    let timeZone = undefined;
    if (tzOption && tzOption !== "auto") {
      timeZone = tzOption;
    }
    try {
      return new Intl.DateTimeFormat("es", {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: timeZone
      }).format(date);
    } catch (e) {
      return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }
  }

  function getLocalDateStr(utcIso, tzOption) {
    try {
      const d = new Date(utcIso);
      let timeZone = (tzOption && tzOption !== "auto") ? tzOption : undefined;
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(d);
    } catch (e) {
      return (utcIso || "").slice(0, 10);
    }
  }

  function getTodayLocalDateStr(tzOption) {
    try {
      const d = new Date();
      let timeZone = (tzOption && tzOption !== "auto") ? tzOption : undefined;
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(d);
    } catch (e) {
      return new Date().toISOString().slice(0, 10);
    }
  }

  function getTomorrowLocalDateStr(tzOption) {
    try {
      const d = new Date();
      d.setDate(d.getDate() + 1);
      let timeZone = (tzOption && tzOption !== "auto") ? tzOption : undefined;
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(d);
    } catch (e) {
      const d = new Date();
      d.setDate(d.getDate() + 1);
      return d.toISOString().slice(0, 10);
    }
  }

  function getYesterdayLocalDateStr(tzOption) {
    try {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      let timeZone = (tzOption && tzOption !== "auto") ? tzOption : undefined;
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: timeZone,
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(d);
    } catch (e) {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      return d.toISOString().slice(0, 10);
    }
  }


  // 3. Flag and League Mapper (Comprehensive International Coverage)
  const flagMap = {
    argentina: "img/flags/ar.svg",
    espana: "img/flags/es.svg",
    mexico: "img/flags/mx.svg",
    colombia: "img/flags/co.svg",
    brasil: "img/flags/br.svg",
    uruguay: "img/flags/uy.svg",
    chile: "img/flags/cl.svg",
    ecuador: "img/flags/ec.svg",
    peru: "img/flags/pe.svg",
    bolivia: "img/flags/bo.svg",
    conmebol: "img/flags/conmebol.svg",
    europa: "img/flags/europa.svg",
    usa: "img/flags/us.svg",
    mlb: "img/flags/mlb.svg"
  };

  function getFlagForMatch(match) {
    const t = (match.tournament || "").toLowerCase();
    const cat = (match.category || "").toLowerCase();

    // Specific tournament trophies & cups
    if (t.includes("libertadores")) return "img/flags/trophy_libertadores.svg";
    if (t.includes("sudamericana")) return "img/flags/trophy_sudamericana.svg";
    if (t.includes("mlb") || t.includes("béisbol") || t.includes("baseball")) return "img/flags/mlb.svg";

    // Continental & European Competitions
    if (t.includes("premier league") || t.includes("efl") || t.includes("carabao") || t.includes("fa cup")) return "img/flags/england.svg";
    if (t.includes("serie a") || t.includes("italia") || t.includes("coppa")) return "img/flags/it.svg";
    if (t.includes("champions league") || t.includes("europa league") || t.includes("conference") || t.includes("uefa")) return "img/flags/europa.svg";
    if (t.includes("bundesliga") || t.includes("alemania")) return "img/flags/de.svg";
    if (t.includes("ligue 1") || t.includes("francia")) return "img/flags/fr.svg";
    if (t.includes("liga portugal") || t.includes("portugal")) return "img/flags/pt.svg";
    if (t.includes("eredivisie") || t.includes("holanda") || t.includes("países bajos")) return "img/flags/nl.svg";
    if (t.includes("afc") || t.includes("asia") || t.includes("saudi")) return "img/flags/afc.svg";

    // Latin America & Americas
    if (t.includes("argentina") || t.includes("profesional") || t.includes("reserva") || cat === "argentina") return "img/flags/ar.svg";
    if (t.includes("laliga") || t.includes("españa") || t.includes("espana") || cat === "espana") return "img/flags/es.svg";
    if (t.includes("mexico") || t.includes("méxico") || t.includes("liga mx") || t.includes("expansión") || cat === "mexico") return "img/flags/mx.svg";
    if (t.includes("colombia") || t.includes("betplay") || t.includes("primera a") || cat === "colombia") return "img/flags/co.svg";
    if (t.includes("brasil") || t.includes("brasileir") || t.includes("paulista") || t.includes("carioca") || cat === "brasil") return "img/flags/br.svg";
    if (t.includes("chile") || t.includes("primera b") || cat === "chile") return "img/flags/cl.svg";
    if (t.includes("peru") || t.includes("perú") || t.includes("liga 1") || cat === "peru") return "img/flags/pe.svg";
    if (t.includes("uruguay") || cat === "uruguay") return "img/flags/uy.svg";
    if (t.includes("ecuador") || t.includes("ligapro") || cat === "ecuador") return "img/flags/ec.svg";
    if (t.includes("bolivia") || cat === "bolivia") return "img/flags/bo.svg";
    if (t.includes("mls") || t.includes("estados unidos") || cat === "usa") return "img/flags/us.svg";
    if (t.includes("conmebol") || cat === "conmebol") return "img/flags/conmebol.svg";

    return flagMap[cat] || "img/flags/es.svg";
  }

  // 4. Country Live Clock & Next Kickoff Calculator
  function initLiveCountryClock() {
    const clockEl = document.getElementById("liveClockDigits") || document.getElementById("countryLiveClock");
    const headerClockEl = document.getElementById("userLiveClockText");
    if (!clockEl && !headerClockEl) return;

    let detectedTz = "America/Argentina/Buenos_Aires";
    try {
      detectedTz = Intl.DateTimeFormat().resolvedOptions().timeZone || detectedTz;
    } catch(e) {}

    const targetTz = (currentTimezone && currentTimezone !== "auto") ? currentTimezone : detectedTz;
    let tzCity = targetTz.split("/").pop().replace(/_/g, " ");

    function tick() {
      try {
        const now = new Date();
        const timeStr = new Intl.DateTimeFormat("es", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: false,
          timeZone: targetTz
        }).format(now);

        if (clockEl) {
          clockEl.textContent = timeStr;
        }
        if (headerClockEl) {
          headerClockEl.innerHTML = `<strong>${timeStr}</strong> <span style="font-size:0.75rem;opacity:0.85;">(${tzCity})</span>`;
        }
      } catch (e) {
        if (headerClockEl) headerClockEl.textContent = "Hora local";
      }
    }

    tick();
    setInterval(tick, 1000);

    // Calculate next upcoming match in this country
    const nextMatchTitle = document.getElementById("nextMatchTitle");
    const nextMatchCountdown = document.getElementById("nextMatchCountdown");
    const targetCat = window.DEFAULT_CATEGORY;

    if (nextMatchTitle && targetCat) {
      const allMatches = window.LIBREGOL_MATCHES || [];
      const todayStr = getTodayLocalDateStr(targetTz);
      const countryUpcoming = allMatches
        .filter(m => (m.category === targetCat || targetCat === 'all') && m.status === 'UPCOMING' && getLocalDateStr(m.utcKickoff, targetTz) === todayStr)
        .sort((a, b) => a.utcKickoff.localeCompare(b.utcKickoff));

      if (countryUpcoming.length > 0) {
        const next = countryUpcoming[0];
        const matchTime = formatMatchTime(next.utcKickoff, targetTz);
        nextMatchTitle.textContent = `${next.homeTeam} vs ${next.awayTeam}`;
        
        const kickoffMs = new Date(next.utcKickoff).getTime();
        const nowMs = Date.now();
        const diffMin = Math.max(0, Math.round((kickoffMs - nowMs) / 60000));
        
        if (diffMin > 60) {
          const hrs = Math.floor(diffMin / 60);
          const mins = diffMin % 60;
          if (nextMatchCountdown) nextMatchCountdown.textContent = `A las ${matchTime} hs (en ${hrs}h ${mins}m)`;
        } else if (diffMin > 0) {
          if (nextMatchCountdown) nextMatchCountdown.textContent = `A las ${matchTime} hs (¡comienza en ${diffMin} min!)`;
        } else {
          if (nextMatchCountdown) nextMatchCountdown.textContent = `A las ${matchTime} hs (¡inicia muy pronto!)`;
        }
      } else {
        nextMatchTitle.textContent = "Consulta la cartelera completa de hoy";
        if (nextMatchCountdown) nextMatchCountdown.textContent = "Horarios confirmados";
      }
    }
  }
  initLiveCountryClock();

  // 5. Update Status Tab Counts
  function updateStatusTabCounts(allMatches) {
    const countAll = document.getElementById("countAll");
    const countLive = document.getElementById("countLive");
    const countFinished = document.getElementById("countFinished");
    const countUpcoming = document.getElementById("countUpcoming");

    if (countAll) countAll.textContent = allMatches.length;
    if (countLive) countLive.textContent = allMatches.filter(m => m.status === "LIVE").length;
    if (countFinished) countFinished.textContent = allMatches.filter(m => m.status === "FINISHED").length;
    if (countUpcoming) countUpcoming.textContent = allMatches.filter(m => m.status === "UPCOMING").length;
  }

  // 6. Core Render Matches Engine
  function renderMatches() {
    if (!matchesContainer) return;

    const allMatches = window.LIBREGOL_MATCHES || [];
    const isTomorrow = window.IS_TOMORROW_VIEW || window.location.pathname.includes("partidos-para-manana");
    const targetDate = isTomorrow ? getTomorrowLocalDateStr(currentTimezone) : getTodayLocalDateStr(currentTimezone);

    // Day filter: Real Matches (Live, Today Upcoming, and Recent Finished from today/yesterday)
    const yesterdayDate = getYesterdayLocalDateStr(currentTimezone);
    const dayMatches = allMatches.filter(match => {
      const matchDate = getLocalDateStr(match.utcKickoff, currentTimezone);
      if (!isTomorrow) {
        if (match.status === "LIVE") {
          return true;
        } else if (match.status === "FINISHED") {
          return matchDate === targetDate || matchDate === yesterdayDate;
        } else {
          return matchDate === targetDate;
        }
      } else {
        return matchDate === targetDate;
      }
    });

    updateStatusTabCounts(dayMatches);

    // Apply Tab, Category and Search Filters on day-filtered matches
    const filtered = dayMatches.filter(match => {
      // Status tab filter (Marcadores view)
      if (activeStatusTab !== "all" && match.status !== activeStatusTab) {
        return false;
      }

      // Category filter
      if (activeCategory !== "all" && match.category !== activeCategory) {
        return false;
      }

      // Search query
      const query = searchQuery.toLowerCase().trim();
      if (query) {
        const h = (match.homeTeam || "").toLowerCase();
        const a = (match.awayTeam || "").toLowerCase();
        const t = (match.tournament || "").toLowerCase();
        const c = (match.category || "").toLowerCase();
        if (!h.includes(query) && !a.includes(query) && !t.includes(query) && !c.includes(query)) {
          return false;
        }
      }

      return true;
    });

    // Update Match Counter Badge
    if (matchCounter) {
      matchCounter.innerHTML = `Mostrando <strong>${filtered.length}</strong> de <strong>${dayMatches.length}</strong> partidos`;
    }

    // Empty state
    if (filtered.length === 0) {
      const isSearchOrFilter = searchQuery || activeCategory !== "all" || activeStatusTab !== "all";
      if (isSearchOrFilter) {
        matchesContainer.innerHTML = `
          <li style="padding: 3rem 1.5rem; text-align: center; color: #64748b; list-style: none; background: white; border-radius: 8px;">
            <div style="font-size: 2.75rem; margin-bottom: 0.6rem;">🔍</div>
            <strong style="font-size: 1.15rem; color: #1f2937; display: block; margin-bottom: 0.4rem;">
              No se encontraron partidos para esta búsqueda o filtro
            </strong>
            <p style="font-size: 0.9rem; margin-bottom: 1rem; color: #64748b;">
              Intenta cambiar los términos de búsqueda o restablecer la categoría.
            </p>
            <button type="button" id="resetFiltersBtn" style="background: #16a34a; color: white; border: none; padding: 0.5rem 1.25rem; border-radius: 6px; font-weight: 700; cursor: pointer;">
              ↺ Restablecer Filtros
            </button>
          </li>
        `;
        const resetBtn = document.getElementById("resetFiltersBtn");
        if (resetBtn) {
          resetBtn.addEventListener("click", () => {
            activeCategory = "all";
            activeStatusTab = "all";
            searchQuery = "";
            if (searchInput) searchInput.value = "";
            if (searchClearBtn) searchClearBtn.style.display = "none";
            document.querySelectorAll(".filter-pill-btn, .status-tab-btn").forEach(b => b.classList.remove("active"));
            const firstCat = document.querySelector(".filter-pill-btn[data-category='all']");
            if (firstCat) firstCat.classList.add("active");
            const firstTab = document.querySelector(".status-tab-btn[data-status='all']");
            if (firstTab) firstTab.classList.add("active");
            renderMatches();
          });
        }
      } else {
        matchesContainer.innerHTML = `
          <li style="padding: 2.5rem 1.5rem; text-align: center; color: #64748b; background: white; border-radius: 8px; list-style: none;">
            <div style="font-size: 2.75rem; margin-bottom: 0.5rem;">⚽</div>
            <strong style="font-size: 1.15rem; color: #1f2937; display: block; margin-bottom: 0.4rem;">
              No hay partidos programados para ${isTomorrow ? 'mañana' : 'hoy'} en este momento
            </strong>
            <p style="font-size: 0.875rem; color: #64748b; margin-bottom: 1.25rem;">
              Los canales deportivos siguen transmitiendo en vivo las 24 horas del día.
            </p>
            <div style="display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap;">
              <a href="/canales/espn-1" style="background: #16a34a; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.85rem;">Ver ESPN en Vivo</a>
              <a href="/canales/tyc-sports" style="background: #0284c7; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.85rem;">Ver TyC Sports</a>
              <a href="/canales/directv-sports" style="background: #1e293b; color: white; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.85rem;">Ver DSports</a>
            </div>
          </li>
        `;
      }
      return;
    }

    // Sort: LIVE first, then UPCOMING chronologically, then FINISHED
    const statusOrder = { LIVE: 1, UPCOMING: 2, FINISHED: 3 };
    const sorted = [...filtered].sort((a, b) => {
      const orderA = statusOrder[a.status] || 2;
      const orderB = statusOrder[b.status] || 2;
      if (orderA !== orderB) return orderA - orderB;
      return a.utcKickoff.localeCompare(b.utcKickoff);
    });

    function resolveChannelHref(ch) {
      if (typeof ch === "object" && ch !== null) {
        ch = ch.name || "";
      }
      const norm = (ch || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
      const isFile = (typeof window !== "undefined" && window.location.protocol === "file:");
      const ext = isFile ? ".html" : "";
      const prefix = isFile ? "canales/" : "/canales/";
      if (norm.includes("espn premium")) return prefix + "espn-premium" + ext;
      if (norm.includes("espn 2") || norm.includes("espn2")) return prefix + "espn-2" + ext;
      if (norm.includes("espn 3") || norm.includes("espn3")) return prefix + "espn-3" + ext;
      if (norm.includes("espn 4") || norm.includes("espn4")) return prefix + "espn-4" + ext;
      if (norm.includes("espn")) return prefix + "espn-1" + ext;
      if (norm.includes("tyc")) return prefix + "tyc-sports" + ext;
      if (norm.includes("fox")) return prefix + "fox-sports-1" + ext;
      if (norm.includes("tnt")) return prefix + "tnt-sports" + ext;
      if (norm.includes("dsports 2") || norm.includes("directv 2")) return prefix + "directv-sports-2" + ext;
      if (norm.includes("dsports +") || norm.includes("plus")) return prefix + "directv-sports-plus" + ext;
      if (norm.includes("dsports") || norm.includes("directv")) return prefix + "directv-sports" + ext;
      if (norm.includes("win")) return prefix + "win-sports" + ext;
      if (norm.includes("liga 1")) return prefix + "liga-1-max" + ext;
      if (norm.includes("gol per") || norm.includes("golperu")) return prefix + "gol-peru" + ext;
      if (norm.includes("telemundo")) return prefix + "telemundo" + ext;
      if (norm.includes("tudn") || norm.includes("vix") || norm.includes("canal 5")) return prefix + "tudn" + ext;
      if (norm.includes("tigo")) return prefix + "tigo-sports" + ext;
      if (norm.includes("estrellas")) return prefix + "las-estrellas" + ext;
      return prefix + "espn-1" + ext;
    }

    // --- VIEW A: MARCADORES / FLASH SCORE SCOREBOARD ---
    if (window.IS_MARCADORES_VIEW) {
      matchesContainer.innerHTML = sorted.map(match => {
        const timeDisplay = formatMatchTime(match.utcKickoff, currentTimezone);
        const isLive = match.status === "LIVE";
        const isFinished = match.status === "FINISHED";
        const flagSrc = getFlagForMatch(match);

        let scorePillHtml = "vs";
        if (match.homeScore !== null && match.awayScore !== null) {
          scorePillHtml = `${match.homeScore} - ${match.awayScore}`;
        }

        let statusBadgeHtml = `<span class="badge-status-time">${timeDisplay}</span>`;
        if (isLive) {
          statusBadgeHtml = `
            <span class="badge-status-live">
              <span class="pulse-live-indicator"></span>
              EN VIVO ${match.minute ? match.minute : ""}
            </span>
          `;
        } else if (isFinished) {
          statusBadgeHtml = `<span class="badge-status-finished">FINAL</span>`;
        }

        const votingHtml = VotingEngine.render(match, false);
        const primaryChannel = (match.channels && match.channels.length > 0) ? match.channels[0] : "ESPN";

        return `
          <li class="scoreboard-match-row" data-status="${match.status}">
            <div class="scoreboard-match-grid">
              <div class="scoreboard-teams-col">
                <img src="${flagSrc}" alt="${match.category}" class="scoreboard-flag" width="26" height="26" loading="lazy">
                <div>
                  <span class="scoreboard-tournament-tag">${match.tournament}</span>
                  <div class="scoreboard-fixture">
                    <span class="scoreboard-team-name">${match.homeTeam}</span>
                    <span class="scoreboard-score-pill ${isLive ? 'live' : ''}">${scorePillHtml}</span>
                    <span class="scoreboard-team-name">${match.awayTeam}</span>
                  </div>
                </div>
              </div>
              <div class="scoreboard-actions-col">
                ${statusBadgeHtml}
                <a href="${resolveChannelHref(primaryChannel)}" class="btn-details-live" title="Ver señal de ${primaryChannel} para ${match.homeTeam} vs ${match.awayTeam}">
                  <span>▶ Transmisión</span>
                </a>
                <button type="button" class="match-voting-toggle-btn" onclick="toggleVotingBox('${match.id}')" title="Ver o dejar pronóstico">
                  🗳️ Pronóstico
                </button>
              </div>
            </div>
            <div id="votingBox-${match.id}" class="embedded-voting-box" style="display: none;">
              ${votingHtml}
            </div>
          </li>
        `;
      }).join("");
      return;
    }

    // --- VIEW B: STANDARD HIGH-DENSITY AGENDA WITH CHANNELS & VOTING ---
    matchesContainer.innerHTML = sorted.map(match => {
      const timeDisplay = formatMatchTime(match.utcKickoff, currentTimezone);
      const isLive = match.status === "LIVE";
      const isFinished = match.status === "FINISHED";
      const flagSrc = getFlagForMatch(match);

      let channelsList = (match.channels && match.channels.length > 0) ? [...match.channels] : ["ESPN", "DSports", "Fox Sports"];
      const submenuHtml = channelsList.map((ch, idx) => {
        const chName = typeof ch === "object" && ch !== null ? (ch.name || "") : String(ch);
        const isGreen = chName.includes("HD") || chName.includes("Premium") || idx === 0;
        return `
          <li class="submenu-row" style="list-style: none; margin: 0; padding: 0.25rem 0;">
            <a href="${resolveChannelHref(ch)}" class="submenu-item" style="display: inline-flex; align-items: center; padding: 0.35rem 0.65rem; text-decoration: none; border-radius: 4px;">
              <span class="submenu-arrow" style="font-size: 10px; margin-right: 0.5rem; color: #16a34a;">▶</span>
              <span class="submenu-name" style="font-size: 14px; font-weight: ${isGreen ? '700' : '500'}; color: ${isGreen ? '#16a34a' : '#475569'};">${chName}</span>
            </a>
          </li>
        `;
      }).join("");

      const compactVotingHtml = VotingEngine.render(match, true);

      let timeBadgeText = timeDisplay;
      let timeClass = "";
      if (isLive) {
        timeBadgeText = "LIVE";
        timeClass = "live";
      } else if (isFinished) {
        timeBadgeText = "FINAL";
      }

      return `
        <li class="toggle-submenu" style="border-bottom: 1px solid #e5e7eb; list-style: none; cursor: pointer; background-color: #fff; padding: 0.15rem 0;" title="Haz clic para ver canales y pronósticos">
          <div class="agenda-match-row" style="display: flex; flex-direction: row; align-items: center; width: 100%; padding: 0.65rem 1rem; gap: 0.75rem; box-sizing: border-box;">
            <time class="match-time ${timeClass}" style="width: 3.8rem; min-width: 3.8rem; text-align: center; font-weight: 700; font-size: 13.5px; color: ${isLive ? '#dc2626' : '#111827'}; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; white-space: nowrap;">
              ${isLive ? '<span style="display: inline-flex; align-items: center; justify-content: center; gap: 4px; color: #dc2626; font-weight: 800; font-size: 13px; letter-spacing: 0.5px; white-space: nowrap;"><span style="width: 6px; height: 6px; background-color: #dc2626; border-radius: 50%; display: inline-block; flex-shrink: 0;"></span>LIVE</span>' : timeBadgeText}
            </time>
            <img src="${flagSrc}" alt="${match.category}" class="match-flag" width="24" height="24" loading="lazy" style="width: 24px; height: 24px; object-fit: cover; border-radius: 2px; flex-shrink: 0; display: inline-block; vertical-align: middle;">
            <span class="match-desc" style="flex: 1; text-align: left; font-weight: 700; color: #2d3748; font-size: 15px; display: inline-block; margin-left: 0.25rem;">
              <strong class="match-tournament" style="color: #1f2937;">${match.tournament}:</strong> ${match.homeTeam} vs ${match.awayTeam}
            </span>
            <span class="accordion-arrow" style="font-size: 0.75rem; color: #9ca3af; font-weight: 600;">▼</span>
          </div>
          <div class="agenda-submenu" style="display: none; background: #f8fafc; padding: 0.75rem 1.25rem; border-top: 1px dashed #e2e8f0; margin: 0;">
            <div style="margin-bottom: 0.65rem;">
              <span style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; color: #64748b; display: block; margin-bottom: 0.35rem;">📺 Canales Oficiales de Transmisión:</span>
              <ul style="padding: 0; margin: 0;">${submenuHtml}</ul>
            </div>
            <div style="border-top: 1px solid #e2e8f0; padding-top: 0.65rem; margin-top: 0.5rem;">
              ${compactVotingHtml}
            </div>
          </div>
        </li>
      `;
    }).join("");
  }

  // Helper to toggle embedded voting box on marcadores
  window.toggleVotingBox = function(matchId) {
    const box = document.getElementById("votingBox-" + matchId);
    if (box) {
      box.style.display = box.style.display === "none" ? "block" : "none";
    }
  };

  // 7. Search Input Handler with Clear Button
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value;
      if (searchClearBtn) {
        searchClearBtn.style.display = searchQuery ? "block" : "none";
      }
      renderMatches();
    });
  }

  if (searchClearBtn) {
    searchClearBtn.addEventListener("click", () => {
      searchQuery = "";
      if (searchInput) {
        searchInput.value = "";
        searchInput.focus();
      }
      searchClearBtn.style.display = "none";
      renderMatches();
    });
  }

  // 8. Status Tab Buttons Handler (Marcadores Page)
  const statusTabs = document.querySelectorAll(".status-tab-btn");
  statusTabs.forEach(btn => {
    btn.addEventListener("click", () => {
      statusTabs.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeStatusTab = btn.dataset.status || "all";
      renderMatches();
    });
  });

  // 9. Quick League / Category Filter Pills Handler
  const filterPills = document.querySelectorAll(".filter-pill-btn, .filter-btn");
  filterPills.forEach(pill => {
    pill.addEventListener("click", () => {
      filterPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      activeCategory = pill.dataset.category || pill.dataset.filter || "all";
      renderMatches();
    });
  });

  // 10. Timezone Selector Handler
  if (timezoneSelect) {
    timezoneSelect.addEventListener("change", (e) => {
      currentTimezone = e.target.value;
      renderMatches();
      initLiveCountryClock();
    });
  }

  // 11. FAQ Accordion Handler
  const faqItems = document.querySelectorAll(".faq-item");
  faqItems.forEach(item => {
    const questionBtn = item.querySelector(".faq-question");
    if (questionBtn) {
      questionBtn.addEventListener("click", () => {
        const isOpen = item.classList.contains("open");
        faqItems.forEach(i => i.classList.remove("open"));
        if (!isOpen) {
          item.classList.add("open");
        }
      });
    }
  });

  // 12. Channels & Voting Submenu Accordion Handler (Standard View)
  if (matchesContainer) {
    matchesContainer.addEventListener("click", function(e) {
      if (e.target.closest(".submenu-item") || e.target.closest(".vote-pill") || e.target.closest(".vote-btn")) {
        return;
      }
      const toggleRow = e.target.closest(".toggle-submenu");
      if (!toggleRow) return;

      const submenu = toggleRow.querySelector(".agenda-submenu");
      if (!submenu) return;

      const isAlreadyOpen = submenu.style.display === "block";

      matchesContainer.querySelectorAll(".agenda-submenu").forEach(ul => {
        ul.style.display = "none";
      });
      matchesContainer.querySelectorAll(".toggle-submenu").forEach(r => {
        r.classList.remove("expanded");
        const arr = r.querySelector(".accordion-arrow");
        if (arr) arr.textContent = "▼";
      });

      if (!isAlreadyOpen) {
        submenu.style.display = "block";
        toggleRow.classList.add("expanded");
        const arr = toggleRow.querySelector(".accordion-arrow");
        if (arr) arr.textContent = "▲";
      }
    });
  }

  // 7. Dynamic Client-Side Auto-Sync Engine (Real-Time Live Updates via Open Scoreboard APIs)
  async function syncLiveMatchesFeed() {
    const espnLeagues = [
      { code: 'arg.1', name: 'Liga Profesional', flag: 'img/flags/ar.svg', category: 'argentina', channels: ['ESPN Premium', 'TNT Sports', 'TyC Sports'] },
      { code: 'mex.1', name: 'Liga MX', flag: 'img/flags/mx.svg', category: 'mexico', channels: ['TUDN', 'ViX Premium', 'Canal 5'] },
      { code: 'col.1', name: 'Liga BetPlay', flag: 'img/flags/co.svg', category: 'colombia', channels: ['Win Sports+', 'Win Sports Online'] },
      { code: 'esp.1', name: 'LaLiga', flag: 'img/flags/es.svg', category: 'espana', channels: ['Movistar Plus+', 'DAZN LaLiga', 'ESPN Deportes'] },
      { code: 'ita.1', name: 'Serie A', flag: 'img/flags/europa.svg', category: 'europa', channels: ['ESPN', 'Disney+ Premium'] },
      { code: 'eng.1', name: 'Premier League', flag: 'img/flags/europa.svg', category: 'europa', channels: ['ESPN', 'Peacock'] },
      { code: 'uefa.champions', name: 'Champions League', flag: 'img/flags/europa.svg', category: 'europa', channels: ['ESPN', 'Fox Sports', 'Movistar+'] },
      { code: 'uefa.europa', name: 'Europa League', flag: 'img/flags/europa.svg', category: 'europa', channels: ['ESPN', 'Fox Sports', 'Disney+'] },
      { code: 'conmebol.libertadores', name: 'Copa Libertadores', flag: 'img/flags/conmebol.svg', category: 'conmebol', channels: ['ESPN', 'Disney+', 'Fox Sports'] },
      { code: 'conmebol.sudamericana', name: 'Copa Sudamericana', flag: 'img/flags/conmebol.svg', category: 'conmebol', channels: ['DSports', 'DGO', 'ESPN'] },
      { code: 'bra.1', name: 'Brasileirão', flag: 'img/flags/br.svg', category: 'brasil', channels: ['Premiere', 'SporTV'] },
      { code: 'chi.1', name: 'Primera División', flag: 'img/flags/cl.svg', category: 'chile', channels: ['TNT Sports Chile', 'Estadio TNT'] },
      { code: 'per.1', name: 'Liga 1', flag: 'img/flags/pe.svg', category: 'peru', channels: ['Liga 1 MAX', 'Gol Perú'] }
    ];

    function slugify(s) {
      return (s || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "");
    }

    try {
      const isTomorrowView = window.IS_TOMORROW_VIEW || window.location.pathname.includes("partidos-para-manana");
      const todayDateStr = getTodayLocalDateStr(currentTimezone);
      const tomorrowDateStr = getTomorrowLocalDateStr(currentTimezone);
      const targetDateStr = isTomorrowView ? tomorrowDateStr : todayDateStr;

      const fetchPromises = espnLeagues.map(async (lg) => {
        try {
          const resp = await fetch(`https://site.api.espn.com/apis/site/v2/sports/soccer/${lg.code}/scoreboard`, {
            headers: { "Accept": "application/json" }
          });
          if (!resp.ok) return [];
          const json = await resp.json();
          const events = (json && json.events) || [];
          return events.map(ev => {
            const comp = (ev.competitions && ev.competitions[0]) || {};
            const comps = comp.competitors || [];
            if (comps.length < 2) return null;
            const home = comps[0].homeAway === 'home' ? comps[0] : comps[1];
            const away = comps[0].homeAway === 'home' ? comps[1] : comps[0];
            const statusObj = ev.status || {};
            const state = (statusObj.type && statusObj.type.state) || 'pre';
            const status = state === 'in' ? 'LIVE' : (state === 'post' ? 'FINISHED' : 'UPCOMING');
            const minute = state === 'in' ? (statusObj.displayClock || '') : '';
            const homeScore = (state === 'in' || state === 'post') && home.score != null ? parseInt(home.score, 10) : null;
            const awayScore = (state === 'in' || state === 'post') && away.score != null ? parseInt(away.score, 10) : null;
            const homeTeam = (home.team && home.team.displayName) || 'Equipo Local';
            const awayTeam = (away.team && away.team.displayName) || 'Equipo Visitante';
            const homeLogo = (home.team && home.team.logo) || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
            const awayLogo = (away.team && away.team.logo) || 'https://a.espncdn.com/i/teamlogos/soccer/500/default.png';
            const slug = slugify(homeTeam) + '-vs-' + slugify(awayTeam);

            const mKickoff = ev.date || new Date().toISOString();
            const matchLocalDate = getLocalDateStr(mKickoff, currentTimezone);

            // STRICT REAL DATE FILTER:
            const yesterdayDateStr = getYesterdayLocalDateStr(currentTimezone);
            if (!isTomorrowView) {
              if (status === 'LIVE') {
                // keep
              } else if (status === 'FINISHED') {
                if (matchLocalDate !== targetDateStr && matchLocalDate !== yesterdayDateStr) return null;
              } else {
                if (matchLocalDate !== targetDateStr) return null;
              }
            } else {
              if (matchLocalDate !== targetDateStr) return null;
            }

            return {
              id: `espn-${ev.id || slug}`,
              slug: slug,
              tournament: lg.name,
              flag: lg.flag,
              homeTeam: homeTeam,
              homeLogo: homeLogo,
              awayTeam: awayTeam,
              awayLogo: awayLogo,
              utcKickoff: mKickoff,
              status: status,
              minute: minute,
              homeScore: homeScore,
              awayScore: awayScore,
              channels: lg.channels,
              venue: (comp.venue && comp.venue.fullName) || 'Estadio Principal',
              category: lg.category,
              votes: {
                team1: 1500 + (homeTeam.length * 75),
                draw: 420 + (homeTeam.length * 20),
                team2: 1400 + (awayTeam.length * 70)
              }
            };
          }).filter(Boolean);
        } catch (e) {
          return [];
        }
      });

      const results = await Promise.all(fetchPromises);
      const apiMatches = results.flat();

      if (apiMatches.length > 0) {
        const currentList = Array.isArray(window.LIBREGOL_MATCHES) ? [...window.LIBREGOL_MATCHES] : [];
        const matchMap = new Map();
        const yesterdayDateStr = getYesterdayLocalDateStr(currentTimezone);

        // Filter current baseline matches to only valid dates
        currentList.forEach(m => {
          const mDate = getLocalDateStr(m.utcKickoff, currentTimezone);
          if (!isTomorrowView) {
            if (m.status === 'LIVE' || (m.status === 'FINISHED' && (mDate === targetDateStr || mDate === yesterdayDateStr)) || (m.status === 'UPCOMING' && mDate === targetDateStr)) {
              matchMap.set(slugify(m.homeTeam) + '-vs-' + slugify(m.awayTeam), m);
            }
          } else {
            if (mDate === targetDateStr) {
              matchMap.set(slugify(m.homeTeam) + '-vs-' + slugify(m.awayTeam), m);
            }
          }
        });

        // Merge apiMatches with current map
        apiMatches.forEach(m => {
          const key = slugify(m.homeTeam) + '-vs-' + slugify(m.awayTeam);
          if (matchMap.has(key)) {
            const existing = matchMap.get(key);
            existing.status = m.status;
            existing.minute = m.minute;
            existing.homeScore = m.homeScore;
            existing.awayScore = m.awayScore;
          } else {
            matchMap.set(key, m);
          }
        });

        window.LIBREGOL_MATCHES = Array.from(matchMap.values());
        renderMatches();
        console.log(`[LibreGol TV] Live real-time sync active: ${window.LIBREGOL_MATCHES.length} matches.`);
      }
    } catch (err) {
      console.warn("[LibreGol TV] Live background sync note:", err.message);
    }
  }

  // Initial Render & Live Background Sync
  renderMatches();
  syncLiveMatchesFeed();
  // Refresh live feed every 3 minutes
  setInterval(syncLiveMatchesFeed, 180000);
});

// Mobile Nav Toggle
function toggleMobileMenu() {
  const drawer = document.getElementById("mobileNav");
  if (drawer) {
    drawer.style.display = drawer.style.display === "none" ? "block" : "none";
  }
}
window.toggleMobileMenu = toggleMobileMenu;
