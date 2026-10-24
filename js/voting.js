/**
 * LibreGol TV — Interactive Fan Voting & Match Prediction Engine
 * Manages live match polls, percentage calculations, animations, and anti-spam persistence.
 */

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
    const total = (votes.team1 || 0) + (votes.draw || 0) + (votes.team2 || 0);
    if (total === 0) {
      return { team1: 33, draw: 34, team2: 33, total: 0 };
    }
    const p1 = Math.round((votes.team1 / total) * 100);
    const pDraw = Math.round((votes.draw / total) * 100);
    const p2 = 100 - (p1 + pDraw); // guarantees 100% sum
    return { team1: p1, draw: pDraw, team2: p2, total: total };
  }

  function renderVotingWidget(match) {
    const userVote = getStoredVote(match.id);
    const perc = calculatePercentages(match.votes);

    return `
      <div class="voting-section" id="voting-${match.id}" data-match-id="${match.id}">
        <div class="voting-header">
          <span>🗳️ Pronóstico de la afición</span>
          <span class="total-votes-count">${perc.total.toLocaleString()} votos</span>
        </div>
        <div class="voting-buttons">
          <button class="vote-btn ${userVote === 'team1' ? 'voted' : ''}" 
                  onclick="VotingEngine.vote('${match.id}', 'team1')" 
                  title="Votar por ${match.homeTeam}">
            <span>${match.homeTeam}</span>
            <span class="vote-perc perc-team1">${perc.team1}%</span>
          </button>
          
          <button class="vote-btn ${userVote === 'draw' ? 'voted' : ''}" 
                  onclick="VotingEngine.vote('${match.id}', 'draw')" 
                  title="Votar por Empate">
            <span>Empate</span>
            <span class="vote-perc perc-draw">${perc.draw}%</span>
          </button>
          
          <button class="vote-btn ${userVote === 'team2' ? 'voted' : ''}" 
                  onclick="VotingEngine.vote('${match.id}', 'team2')" 
                  title="Votar por ${match.awayTeam}">
            <span>${match.awayTeam}</span>
            <span class="vote-perc perc-team2">${perc.team2}%</span>
          </button>
        </div>
        
        <div class="vote-bar-container" title="${match.homeTeam} ${perc.team1}% | Empate ${perc.draw}% | ${match.awayTeam} ${perc.team2}%">
          <div class="vote-bar-team1" style="width: ${perc.team1}%;"></div>
          <div class="vote-bar-draw" style="width: ${perc.draw}%;"></div>
          <div class="vote-bar-team2" style="width: ${perc.team2}%;"></div>
        </div>
      </div>
    `;
  }

  function renderCompactWidget(match) {
    const userVote = getStoredVote(match.id);
    const perc = calculatePercentages(match.votes);

    return `
      <div class="row-voting" id="voting-${match.id}" data-match-id="${match.id}">
        <span class="vote-tag">🗳️ Pronóstico:</span>
        <div class="vote-pills-row">
          <button type="button" class="vote-pill ${userVote === 'team1' ? 'voted' : ''}" 
                  onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'team1')" 
                  title="Votar por ${match.homeTeam}">
            <span class="v-name">${match.homeTeam}</span>
            <span class="v-perc perc-team1">${perc.team1}%</span>
          </button>
          
          <button type="button" class="vote-pill ${userVote === 'draw' ? 'voted' : ''}" 
                  onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'draw')" 
                  title="Votar por Empate">
            <span class="v-name">Empate</span>
            <span class="v-perc perc-draw">${perc.draw}%</span>
          </button>
          
          <button type="button" class="vote-pill ${userVote === 'team2' ? 'voted' : ''}" 
                  onclick="event.stopPropagation(); VotingEngine.vote('${match.id}', 'team2')" 
                  title="Votar por ${match.awayTeam}">
            <span class="v-name">${match.awayTeam}</span>
            <span class="v-perc perc-team2">${perc.team2}%</span>
          </button>
        </div>
        
        <div class="vote-micro-bar" title="${match.homeTeam} ${perc.team1}% | Empate ${perc.draw}% | ${match.awayTeam} ${perc.team2}%">
          <div class="vote-bar-team1" style="width: ${perc.team1}%;"></div>
          <div class="vote-bar-draw" style="width: ${perc.draw}%;"></div>
          <div class="vote-bar-team2" style="width: ${perc.team2}%;"></div>
        </div>
      </div>
    `;
  }

  function castVote(matchId, choice) {
    const existing = getStoredVote(matchId);
    if (existing) {
      alert("¡Ya has dejado tu pronóstico para este encuentro!");
      return;
    }

    const match = (window.LIBREGOL_MATCHES || []).find(m => m.id === matchId);
    if (!match) return;

    // Increment count
    match.votes[choice] = (match.votes[choice] || 0) + 1;
    setStoredVote(matchId, choice);

    // Update DOM element directly
    const widget = document.getElementById("voting-" + matchId);
    if (widget) {
      const perc = calculatePercentages(match.votes);
      const totalEl = widget.querySelector(".total-votes-count");
      if (totalEl) totalEl.textContent = perc.total.toLocaleString() + " votos";

      const p1 = widget.querySelector(".perc-team1");
      if (p1) p1.textContent = perc.team1 + "%";
      const pDraw = widget.querySelector(".perc-draw");
      if (pDraw) pDraw.textContent = perc.draw + "%";
      const p2 = widget.querySelector(".perc-team2");
      if (p2) p2.textContent = perc.team2 + "%";

      const b1 = widget.querySelector(".vote-bar-team1");
      if (b1) b1.style.width = perc.team1 + "%";
      const bDraw = widget.querySelector(".vote-bar-draw");
      if (bDraw) bDraw.style.width = perc.draw + "%";
      const b2 = widget.querySelector(".vote-bar-team2");
      if (b2) b2.style.width = perc.team2 + "%";

      const btns = widget.querySelectorAll(".vote-btn, .vote-pill");
      btns.forEach(b => b.classList.remove("voted"));
      if (choice === "team1" && btns[0]) btns[0].classList.add("voted");
      if (choice === "draw" && btns[1]) btns[1].classList.add("voted");
      if (choice === "team2" && btns[2]) btns[2].classList.add("voted");
    }
  }

  return {
    render: renderVotingWidget,
    renderCompact: renderCompactWidget,
    vote: castVote
  };
})();

var VotingEngine = window.VotingEngine;
