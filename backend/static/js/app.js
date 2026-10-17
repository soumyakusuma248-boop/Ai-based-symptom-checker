/* =========================================================
   AI Symptom Checker — Frontend JavaScript
   ========================================================= */

(function () {
  'use strict';

  // ── DOM references ──────────────────────────────────────
  const searchInput      = document.getElementById('symptom-search');
  const clearSearchBtn   = document.getElementById('clear-search');
  const chipsWrap        = document.getElementById('selected-chips');
  const chipsLabel       = document.getElementById('chips-label');
  const categoriesWrap   = document.getElementById('categories-wrap');
  const analyzeBtn       = document.getElementById('analyze-btn');
  const clearAllBtn      = document.getElementById('clear-all-btn');
  const selectedCount    = document.getElementById('selected-count');

  const emptyState       = document.getElementById('empty-state');
  const loadingState     = document.getElementById('loading-state');
  const errorState       = document.getElementById('error-state');
  const errorMsg         = document.getElementById('error-msg');
  const resultsEl        = document.getElementById('results');

  const triageBanner     = document.getElementById('triage-banner');
  const triageIcon       = document.getElementById('triage-icon');
  const triageLabel      = document.getElementById('triage-label');
  const triageMessage    = document.getElementById('triage-message');
  const redFlagAlert     = document.getElementById('red-flag-alert');
  const redFlagList      = document.getElementById('red-flag-list');
  const conditionsList   = document.getElementById('conditions-list');
  const disclaimerBox    = document.getElementById('disclaimer-box');
  const recheckBtn       = document.getElementById('recheck-btn');

  // ── State ───────────────────────────────────────────────
  const selectedSymptoms = new Map(); // key → label

  // ── Category Accordions ─────────────────────────────────
  document.querySelectorAll('.category-toggle').forEach(toggle => {
    toggle.addEventListener('click', () => {
      const isOpen = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!isOpen));
      const list = toggle.nextElementSibling;
      list.classList.toggle('collapsed', isOpen);
    });
  });

  // ── Checkbox interaction ─────────────────────────────────
  document.querySelectorAll('.sym-checkbox').forEach(cb => {
    cb.addEventListener('change', () => {
      const item  = cb.closest('.symptom-item');
      const key   = cb.value;
      const label = item.dataset.label;

      if (cb.checked) {
        selectedSymptoms.set(key, label);
      } else {
        selectedSymptoms.delete(key);
      }
      updateUI();
    });
  });

  // ── Chips ────────────────────────────────────────────────
  function updateUI() {
    // Update chips
    chipsWrap.innerHTML = '';
    if (selectedSymptoms.size === 0) {
      chipsWrap.appendChild(chipsLabel);
      chipsLabel.textContent = 'No symptoms selected';
    } else {
      selectedSymptoms.forEach((label, key) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.innerHTML = `
          <span>${label}</span>
          <button class="chip-remove" data-key="${key}" title="Remove" aria-label="Remove ${label}">✕</button>
        `;
        chipsWrap.appendChild(chip);
      });
    }

    // Update count
    const n = selectedSymptoms.size;
    selectedCount.textContent = `${n} symptom${n !== 1 ? 's' : ''} selected`;

    // Enable/disable analyze button
    analyzeBtn.disabled = n === 0;

    // Update category badges
    updateCategoryBadges();
  }

  // Remove chip → uncheck checkbox
  chipsWrap.addEventListener('click', e => {
    const btn = e.target.closest('.chip-remove');
    if (!btn) return;
    const key = btn.dataset.key;
    selectedSymptoms.delete(key);
    const cb = document.querySelector(`.sym-checkbox[value="${key}"]`);
    if (cb) cb.checked = false;
    updateUI();
  });

  // ── Category Badges ──────────────────────────────────────
  function updateCategoryBadges() {
    document.querySelectorAll('.category-block').forEach((block, i) => {
      const checked = block.querySelectorAll('.sym-checkbox:checked').length;
      const badge = document.getElementById(`count-${i + 1}`);
      if (badge) {
        badge.textContent = checked;
        badge.classList.toggle('active', checked > 0);
      }
    });
  }

  // ── Search / Filter ──────────────────────────────────────
  searchInput.addEventListener('input', () => {
    const q = searchInput.value.trim().toLowerCase();
    clearSearchBtn.style.display = q ? 'block' : 'none';

    document.querySelectorAll('.category-block').forEach((block, i) => {
      let visibleCount = 0;
      block.querySelectorAll('.symptom-item').forEach(item => {
        const label = item.dataset.label.toLowerCase();
        const match = !q || label.includes(q);
        item.classList.toggle('filtered-out', !match);
        if (match) visibleCount++;
      });

      // Auto-expand matching categories, collapse empty ones
      const toggle = block.querySelector('.category-toggle');
      const list   = block.querySelector('.symptom-list');
      if (q) {
        if (visibleCount > 0) {
          toggle.setAttribute('aria-expanded', 'true');
          list.classList.remove('collapsed');
        } else {
          list.classList.add('collapsed');
        }
      }
    });
  });

  clearSearchBtn.addEventListener('click', () => {
    searchInput.value = '';
    clearSearchBtn.style.display = 'none';
    document.querySelectorAll('.symptom-item').forEach(item => {
      item.classList.remove('filtered-out');
    });
  });

  // ── Clear All ────────────────────────────────────────────
  clearAllBtn.addEventListener('click', () => {
    selectedSymptoms.clear();
    document.querySelectorAll('.sym-checkbox').forEach(cb => cb.checked = false);
    updateUI();
    showPanel('empty');
  });

  // ── Analyze ──────────────────────────────────────────────
  analyzeBtn.addEventListener('click', async () => {
    if (selectedSymptoms.size === 0) return;
    showPanel('loading');

    try {
      const response = await fetch('/api/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms: [...selectedSymptoms.keys()] }),
      });

      const data = await response.json();

      if (!response.ok || data.error) {
        showError(data.error || `Server error (${response.status})`);
        return;
      }

      renderResults(data);
    } catch (err) {
      showError('Network error — please check your connection and try again.');
    }
  });

  // ── Re-check ─────────────────────────────────────────────
  recheckBtn.addEventListener('click', () => {
    showPanel('empty');
    // Scroll back to symptom panel on mobile
    document.getElementById('symptom-panel').scrollIntoView({ behavior: 'smooth' });
  });

  // ── Panel switcher ───────────────────────────────────────
  function showPanel(state) {
    emptyState.classList.add('hidden');
    loadingState.classList.add('hidden');
    errorState.classList.add('hidden');
    resultsEl.classList.add('hidden');

    if (state === 'empty')   emptyState.classList.remove('hidden');
    if (state === 'loading') loadingState.classList.remove('hidden');
    if (state === 'error')   errorState.classList.remove('hidden');
    if (state === 'results') resultsEl.classList.remove('hidden');
  }

  function showError(msg) {
    errorMsg.textContent = msg;
    showPanel('error');
  }

  // ── Render Results ───────────────────────────────────────
  function renderResults(data) {
    // Triage banner
    triageBanner.className = `triage-banner ${data.triage_color}`;
    triageIcon.textContent = data.triage_icon;
    triageLabel.textContent = data.triage_label;
    triageMessage.textContent = data.triage_message;

    // Red flags
    if (data.red_flags && data.red_flags.length > 0) {
      redFlagList.innerHTML = data.red_flags
        .map(f => `<li>${escapeHtml(f)}</li>`)
        .join('');
      redFlagAlert.classList.remove('hidden');
    } else {
      redFlagAlert.classList.add('hidden');
    }

    // Conditions
    conditionsList.innerHTML = '';
    const triageLabels = {
      self_care:  { label: 'Self-Care', color: 'green' },
      see_doctor: { label: 'See Doctor', color: 'orange' },
      emergency:  { label: 'Emergency', color: 'red' },
    };

    if (data.top_conditions && data.top_conditions.length > 0) {
      data.top_conditions.forEach((cond, idx) => {
        const tInfo = triageLabels[cond.triage] || { label: cond.triage, color: 'orange' };
        const rankClass = idx === 0 ? 'rank-1' : idx === 1 ? 'rank-2' : 'rank-3';

        const matchedChipsHtml = (cond.matched_symptoms || [])
          .map(s => `<span class="matched-chip">${escapeHtml(s)}</span>`)
          .join('');

        const card = document.createElement('div');
        card.className = 'condition-card';
        card.innerHTML = `
          <div class="condition-header">
            <span class="condition-rank ${rankClass}">${idx + 1}</span>
            <span class="condition-name">${escapeHtml(cond.name)}</span>
            <span class="triage-pill ${tInfo.color}">${tInfo.label}</span>
            <div class="match-bar-wrap">
              <div class="match-bar">
                <div class="match-fill" style="width: ${cond.match_percent}%"></div>
              </div>
              <span class="match-pct">${cond.match_percent}%</span>
            </div>
            <span class="caret">▼</span>
          </div>
          <div class="condition-body">
            <p>${escapeHtml(cond.description)}</p>
            <div class="advice-box">
              <strong>What to do:</strong>
              ${escapeHtml(cond.advice)}
            </div>
            ${matchedChipsHtml ? `
            <div class="matched-symptoms-wrap">
              <div class="matched-symptoms-title">Matching symptoms:</div>
              <div class="matched-chips">${matchedChipsHtml}</div>
            </div>` : ''}
            <p class="icd-hint">ICD-10 reference: ${escapeHtml(cond.icd_hint)}</p>
          </div>
        `;

        // Toggle expand
        card.querySelector('.condition-header').addEventListener('click', () => {
          card.classList.toggle('open');
        });

        conditionsList.appendChild(card);
      });

      // Auto-open the first card
      const firstCard = conditionsList.querySelector('.condition-card');
      if (firstCard) firstCard.classList.add('open');

    } else {
      conditionsList.innerHTML = `
        <p style="color:var(--text-muted);font-size:0.88rem;padding:12px 0;">
          No specific conditions matched your symptom combination. 
          Please consult a healthcare professional.
        </p>`;
    }

    // Disclaimer
    disclaimerBox.textContent = data.disclaimer;

    showPanel('results');
  }

  // ── Utilities ────────────────────────────────────────────
  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  // Initialise
  updateUI();

})();
