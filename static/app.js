const form = document.getElementById('search-form');
const queryInput = document.getElementById('query');
const submitBtn = document.getElementById('submit-btn');
const resultsList = document.getElementById('results-list');
const resultsHeader = document.getElementById('results-header');

form.addEventListener('submit', (e) => {
    e.preventDefault();
    runSearch();
});

async function runSearch() {
    const q = queryInput.value.trim();
    if (!q) return;

    const params = new URLSearchParams({
        q,
        mode: document.getElementById('mode').value,
        sort: document.getElementById('sort').value,
        min_likes: document.getElementById('min_likes').value || 0,
        min_reposts: document.getElementById('min_reposts').value || 0,
        date_from: document.getElementById('date_from').value,
        date_to: document.getElementById('date_to').value,
    });

    setLoading(true);

    try {
        const res = await fetch(`/api/search?${params}`);
        const data = await res.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        renderResults(data);
    } catch {
        showError('Search failed. Is the server running?');
    } finally {
        setLoading(false);
    }
}

function setLoading(loading) {
    submitBtn.disabled = loading;
    if (loading) {
        resultsList.innerHTML = '<div class="state-message"><span class="spinner"></span>Searching…</div>';
        resultsHeader.textContent = '';
    }
}

function showError(msg) {
    resultsList.innerHTML = `<div class="state-message error">${escapeHtml(msg)}</div>`;
    resultsHeader.textContent = '';
}

function renderResults(results) {
    if (results.length === 0) {
        resultsHeader.textContent = '';
        resultsList.innerHTML = '<div class="state-message">No results found.</div>';
        return;
    }

    resultsHeader.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;
    resultsList.innerHTML = results.map(buildCard).join('');
}

function buildCard(r) {
    const date = r.created_at
        ? new Date(r.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
        : '';

    const linksHtml = (r.url_list || [])
        .map((url, i) => {
            const title = r.title_list && r.title_list[i] ? r.title_list[i] : url;
            return `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`;
        })
        .join('');

    return `
<div class="result-card">
  <div class="card-header">
    <div class="author-info">
      <span class="handle">@${escapeHtml(r.author_handle || '')}</span>
      ${r.author_display_name ? `<span class="display-name">${escapeHtml(r.author_display_name)}</span>` : ''}
    </div>
    <div class="card-meta">
      ${date ? `<span>${date}</span>` : ''}
      <span>score ${r.score.toFixed(3)}</span>
    </div>
  </div>
  <p class="post-text">${escapeHtml(r.text || '')}</p>
  ${linksHtml ? `<div class="post-links">${linksHtml}</div>` : ''}
  <div class="engagement">
    <span>♥ ${r.like_count || 0}</span>
    <span>↺ ${r.repost_count || 0}</span>
    <span>↩ ${r.reply_count || 0}</span>
    <span>❝ ${r.quote_count || 0}</span>
  </div>
</div>`;
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
}
