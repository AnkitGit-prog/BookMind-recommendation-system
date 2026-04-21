/**
 * BookMind — app.js
 * Autocomplete, recommendation fetch, card render, popular card clicks
 */
'use strict';

/* ── DOM refs ─────────────────────────────────────────────── */
const bookInput        = document.getElementById('book-input');
const recommendBtn     = document.getElementById('recommend-btn');
const clearBtn         = document.getElementById('clear-btn');
const errorBanner      = document.getElementById('error-banner');
const errorMessage     = document.getElementById('error-message');
const resultsSection   = document.getElementById('results-section');
const resultsGrid      = document.getElementById('results-grid');
const resultsSubtitle  = document.getElementById('results-subtitle');
const resultsCount     = document.getElementById('results-count');
const autocompleteList = document.getElementById('autocomplete-list');
const cardTemplate     = document.getElementById('book-card-template');

/* ── State ────────────────────────────────────────────────── */
let acIndex = -1;
let acTimer = null;

/* ═══════════════════════════════════════════════════════════
   Utilities
   ═══════════════════════════════════════════════════════════ */
function showError(msg) {
  errorMessage.textContent = msg;
  errorBanner.removeAttribute('hidden');
  errorBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}
function hideError() { errorBanner.setAttribute('hidden', ''); }

function setLoading(on) {
  const text    = recommendBtn.querySelector('.btn-text');
  const icon    = recommendBtn.querySelector('.btn-icon');
  const spinner = recommendBtn.querySelector('.btn-spinner');
  if (on) {
    text.textContent = 'Finding…';
    icon.setAttribute('hidden', '');
    spinner.removeAttribute('hidden');
    recommendBtn.classList.add('loading');
  } else {
    text.textContent = 'Recommend';
    icon.removeAttribute('hidden');
    spinner.setAttribute('hidden', '');
    recommendBtn.classList.remove('loading');
  }
}

function highlightMatch(text, query) {
  if (!query) return document.createTextNode(text);
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return document.createTextNode(text);
  const frag = document.createDocumentFragment();
  frag.appendChild(document.createTextNode(text.slice(0, idx)));
  const mark = document.createElement('strong');
  mark.textContent = text.slice(idx, idx + query.length);
  frag.appendChild(mark);
  frag.appendChild(document.createTextNode(text.slice(idx + query.length)));
  return frag;
}

/* ═══════════════════════════════════════════════════════════
   Autocomplete
   ═══════════════════════════════════════════════════════════ */
function closeAutocomplete() {
  autocompleteList.innerHTML = '';
  autocompleteList.setAttribute('hidden', '');
  acIndex = -1;
}

function buildDropdown(titles) {
  const q = bookInput.value.trim();
  autocompleteList.innerHTML = '';
  acIndex = -1;

  if (!titles.length) { closeAutocomplete(); return; }

  titles.forEach((title, i) => {
    const li = document.createElement('li');
    li.setAttribute('role', 'option');
    li.setAttribute('id', `ac-${i}`);
    li.appendChild(highlightMatch(title, q));
    li.addEventListener('mousedown', (e) => {
      e.preventDefault();
      bookInput.value = title;
      clearBtn.removeAttribute('hidden');
      closeAutocomplete();
    });
    autocompleteList.appendChild(li);
  });
  autocompleteList.removeAttribute('hidden');
}

function fetchSuggestions(q) {
  clearTimeout(acTimer);
  if (q.length < 2) { closeAutocomplete(); return; }
  acTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/autocomplete?q=${encodeURIComponent(q)}`);
      buildDropdown(await res.json());
    } catch { closeAutocomplete(); }
  }, 160);
}

/* Keyboard nav */
bookInput.addEventListener('keydown', (e) => {
  const items = autocompleteList.querySelectorAll('li');
  if (!items.length && e.key === 'Enter') { triggerRecommend(); return; }

  if (e.key === 'ArrowDown') {
    e.preventDefault();
    acIndex = (acIndex + 1) % items.length;
    syncSelection(items);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    acIndex = (acIndex - 1 + items.length) % items.length;
    syncSelection(items);
  } else if (e.key === 'Enter') {
    if (acIndex >= 0 && items[acIndex]) {
      bookInput.value = items[acIndex].textContent;
      closeAutocomplete();
    } else {
      triggerRecommend();
    }
  } else if (e.key === 'Escape') {
    closeAutocomplete();
  }
});

function syncSelection(items) {
  items.forEach((li, i) => {
    const active = i === acIndex;
    li.setAttribute('aria-selected', String(active));
    if (active) { li.scrollIntoView({ block: 'nearest' }); bookInput.value = li.textContent; }
  });
}

/* Input events */
bookInput.addEventListener('input', () => {
  const v = bookInput.value;
  clearBtn.toggleAttribute('hidden', !v);
  fetchSuggestions(v);
  hideError();
});
bookInput.addEventListener('blur', () => setTimeout(closeAutocomplete, 200));

clearBtn.addEventListener('click', () => {
  bookInput.value = '';
  clearBtn.setAttribute('hidden', '');
  bookInput.focus();
  closeAutocomplete();
  hideError();
  resultsSection.setAttribute('hidden', '');
});

/* ═══════════════════════════════════════════════════════════
   Recommendation fetch & render
   ═══════════════════════════════════════════════════════════ */
async function triggerRecommend() {
  const query = bookInput.value.trim();
  if (!query) { showError('Please enter a book name first.'); bookInput.focus(); return; }

  hideError();
  setLoading(true);
  closeAutocomplete();

  try {
    const res  = await fetch('/recommend', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ book_name: query }),
    });
    const data = await res.json();

    if (!res.ok) {
      showError(data.error || 'Something went wrong. Please try again.');
      resultsSection.setAttribute('hidden', '');
      return;
    }
    renderResults(data.results, data.query);

  } catch {
    showError('Network error — check your connection and try again.');
  } finally {
    setLoading(false);
  }
}

recommendBtn.addEventListener('click', triggerRecommend);

/* ── Render cards ──────────────────────────────────────────── */
function renderResults(books, query) {
  resultsGrid.innerHTML = '';
  resultsSubtitle.textContent = `Because you liked "${query}"`;
  resultsCount.textContent    = `${books.length} recommendation${books.length !== 1 ? 's' : ''}`;

  books.forEach((book) => {
    const node    = cardTemplate.content.cloneNode(true);
    const img     = node.querySelector('.card-image');
    const fallback= node.querySelector('.card-image-fallback');
    const title   = node.querySelector('.card-title');
    const author  = node.querySelector('.card-author');
    const score   = node.querySelector('.card-score');
    const barFill = node.querySelector('.card-bar-fill');

    title.textContent  = book.title  || 'Unknown Title';
    author.textContent = book.author || 'Unknown Author';

    const pct = book.score != null ? Math.round(book.score * 100) : 0;
    score.textContent = pct;
    setTimeout(() => { barFill.style.width = `${pct}%`; }, 60);

    if (book.image) {
      img.src = book.image;
      img.alt = `Cover of ${book.title}`;
      img.addEventListener('error', () => {
        img.style.display = 'none';
        fallback.style.opacity = '0.55';
      });
    } else {
      img.style.display = 'none';
      fallback.style.opacity = '0.45';
    }

    resultsGrid.appendChild(node);
  });

  resultsSection.removeAttribute('hidden');
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/* ═══════════════════════════════════════════════════════════
   Quick chips (top bar) & Popular cards
   ═══════════════════════════════════════════════════════════ */
function attachTrigger(selector) {
  document.querySelectorAll(selector).forEach((el) => {
    el.addEventListener('click', () => {
      const title = el.dataset.title;
      if (!title) return;
      bookInput.value = title;
      clearBtn.removeAttribute('hidden');
      hideError();
      window.scrollTo({ top: 0, behavior: 'smooth' });
      setTimeout(triggerRecommend, 300); // let scroll start first
    });
    // keyboard: Enter / Space on pop-cards
    el.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        el.click();
      }
    });
  });
}

attachTrigger('.chip');
attachTrigger('.pop-card');
