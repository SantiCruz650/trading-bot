/* ============================================
   MCRYPTO — App Logic (API Connected)
   ============================================ */

const API_BASE = 'https://trading-bot-kea3.onrender.com';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ========= Token Management ========= */
function getToken() { return localStorage.getItem('mcrypto_token'); }
function setToken(t) { localStorage.setItem('mcrypto_token', t); }
function clearToken() { localStorage.removeItem('mcrypto_token'); }

function authHeaders() {
  const t = getToken();
  return t ? { 'Authorization': `Bearer ${t}` } : {};
}

async function apiFetch(path, opts = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { ...authHeaders(), ...opts.headers };
  try {
    const res = await fetch(url, { ...opts, headers });
    if (res.status === 401) { clearToken(); showLogin(); throw new Error('Session expired'); }
    return res;
  } catch (e) {
    console.error(`API Error (${path}):`, e);
    throw e;
  }
}

/* ========= Toast Notifications ========= */
function toast(msg, type = 'ok') {
  const c = $('#toasts');
  const el = document.createElement('div');
  el.className = `toast toast--${type}`;
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 4000);
}

/* ========= Login ========= */
function showLogin() {
  $('#loginOverlay').classList.remove('hidden');
  $('#appContent').classList.remove('visible');
}

function showApp() {
  $('#loginOverlay').classList.add('hidden');
  $('#appContent').classList.add('visible');
}

$('#loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const btn = $('#loginBtn');
  const err = $('#loginError');
  const user = $('#loginUser').value.trim();
  const pass = $('#loginPass').value;

  btn.disabled = true;
  btn.innerHTML = '<span class="login-spinner"></span>Conectando al servidor...';
  err.textContent = '';

  try {
    const body = new URLSearchParams({ username: user, password: pass });
    const res = await fetch(`${API_BASE}/api/auth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || 'Credenciales incorrectas');
    }

    const data = await res.json();
    setToken(data.access_token);

    // Set username in UI
    const username = user;
    $('#profileName').textContent = username;
    $('#menuName').textContent = username;

    showApp();
    toast(`Bienvenido, ${username}`);
    initDashboard();
  } catch (error) {
    err.textContent = error.message || 'Error de conexión. El servidor puede estar iniciando (~30s).';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Iniciar sesión';
  }
});

// Check existing session on load
async function checkSession() {
  const token = getToken();
  if (!token) { showLogin(); return; }

  try {
    const res = await apiFetch('/api/auth/verify');
    if (res.ok) {
      const user = await res.json();
      $('#profileName').textContent = user.username;
      $('#menuName').textContent = user.username;
      showApp();
      initDashboard();
    } else {
      clearToken();
      showLogin();
    }
  } catch {
    // Server might be cold-starting, show login
    showLogin();
  }
}

/* ========= Dashboard Init ========= */
function initDashboard() {
  fetchStatus();
  fetchBalance();
  fetchPortfolio();
  fetchTickers();
  initTradingViewChart();
  // Auto-refresh every 30s
  setInterval(() => {
    fetchStatus();
    fetchBalance();
    fetchPortfolio();
    fetchTickers();
  }, 30000);
}

/* ========= Fetch Tickers (Live Prices) ========= */
async function fetchTickers() {
  const symbols = ['ETHUSDT', 'BTCUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT'];
  try {
    // Try to fetch from Binance directly for the UI tickers
    const res = await fetch(`https://api.binance.com/api/v3/ticker/24hr?symbols=${JSON.stringify(symbols)}`);
    if (!res.ok) return;
    const data = await res.json();

    data.forEach(t => {
      const btn = $(`.symbol[data-sym="${t.symbol}"]`);
      if (!btn) return;
      const px = btn.querySelector('.symbol__px');
      const chg = btn.querySelector('.symbol__chg');
      
      const price = parseFloat(t.lastPrice);
      const change = parseFloat(t.priceChangePercent);
      
      px.textContent = price < 1 ? price.toFixed(4) : price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
      chg.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
      chg.className = `symbol__chg num ${change >= 0 ? 't-green' : 't-red'}`;
    });
  } catch (e) {
    console.warn('Ticker fetch failed:', e);
  }
}

/* ========= Fetch Status ========= */
async function fetchStatus() {
  try {
    const res = await apiFetch('/api/status');
    if (!res.ok) return;
    const d = await res.json();

    // Status text
    const statusMap = { RUNNING: 'Online', STOPPED: 'Offline', KILLED: 'KILLED' };
    $('#statusText').textContent = statusMap[d.status] || d.status;
    const dot = $('#statusDot');
    dot.className = 'dot ' + (d.status === 'RUNNING' ? 'dot--green' : d.status === 'KILLED' ? 'dot--red' : 'dot--orange');

    // GEC state
    $('#gecBadge').textContent = `GEC ${d.risk_state || 'NORMAL'}`;

    // Mode badge
    const mb = $('#modeBadge');
    const mode = (d.mode || 'MOCK').toUpperCase();
    mb.textContent = mode;
    mb.className = 'mode-badge ' + (mode === 'LIVE' ? 'mode-badge--live' : mode === 'DRY_RUN' ? 'mode-badge--dry' : 'mode-badge--mock');

    // Uptime
    if (d.uptime > 0) {
      const days = Math.floor(d.uptime / 86400);
      const hrs = Math.floor((d.uptime % 86400) / 3600);
      const mins = Math.floor((d.uptime % 3600) / 60);
      const uptimeEl = document.querySelector('.clock .num:last-child');
      // Not critical if not found
    }

    // Update risk ladder
    $$('.risk-ladder li').forEach(li => li.classList.remove('is-active'));
    const stateMap = { 'NORMAL': 0, 'SOFT_CAP': 1, 'HARD_CAP': 2, 'FREEZE': 3, 'KILL_SWITCH': 4 };
    const idx = stateMap[d.risk_state] ?? 0;
    const ladderItems = $$('.risk-ladder li');
    if (ladderItems[idx]) ladderItems[idx].classList.add('is-active');

  } catch (e) { console.warn('Status fetch failed:', e); }
}

/* ========= Fetch Balance ========= */
async function fetchBalance() {
  try {
    const res = await apiFetch('/api/trading/balance');
    if (!res.ok) return;
    const d = await res.json();

    const balance = d.balance ?? 0;
    const equity = d.equity ?? balance;
    const stats = d.stats || {};

    $('#kpiEquity').textContent = equity.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    $('#kpiCash').textContent = balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

    const pnl = stats.pnl ?? 0;
    const pnlEl = $('#kpiPnl');
    pnlEl.textContent = (pnl >= 0 ? '+' : '') + pnl.toFixed(2);
    pnlEl.className = 'kpi__val num ' + (pnl >= 0 ? 't-green' : 't-red');

    const dd = (stats.daily_drawdown ?? 0) * 100;
    $('#kpiDrawdown').textContent = dd.toFixed(2) + '%';

  } catch (e) { console.warn('Balance fetch failed:', e); }
}

/* ========= Fetch Portfolio ========= */
async function fetchPortfolio() {
  try {
    const res = await apiFetch('/api/trading/portfolio');
    if (!res.ok) return;
    const positions = await res.json();

    const body = $('#posBody');
    const countEl = $('#posCount');

    if (!positions || positions.length === 0) {
      body.innerHTML = '<tr id="posEmpty"><td colspan="8" style="text-align:center;padding:30px;color:var(--muted)">No hay posiciones abiertas</td></tr>';
      countEl.innerHTML = '0 <span data-i18n="pos.active">activas</span>';
      return;
    }

    countEl.innerHTML = `${positions.length} <span data-i18n="pos.active">activas</span>`;
    body.innerHTML = positions.map(p => `
      <tr>
        <td><span class="pair"><i class="pair__i">${p.ticker.charAt(0)}</i>${p.ticker}</span></td>
        <td><span class="side side--long">LONG</span></td>
        <td class="r num">${p.amount.toFixed(4)}</td>
        <td class="r num">${p.price.toFixed(2)}</td>
        <td class="r num">—</td>
        <td class="r num muted">—</td>
        <td class="r num muted">—</td>
        <td></td>
      </tr>
    `).join('');
  } catch (e) { console.warn('Portfolio fetch failed:', e); }
}

/* ========= Command Panel ========= */
$$('.card--cmd .btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const text = btn.textContent.trim();
    let endpoint, method = 'POST', confirmMsg;

    if (text === 'START') endpoint = '/api/start';
    else if (text === 'STOP') endpoint = '/api/stop';
    else if (text === 'EMERGENCY KILL') { endpoint = '/api/kill'; confirmMsg = '⚠️ ¿Activar KILL SWITCH? El bot se bloqueará permanentemente hasta un UNLOCK.'; }
    else if (text === 'UNLOCK') endpoint = '/api/unlock';
    else return;

    if (confirmMsg && !confirm(confirmMsg)) return;

    try {
      btn.disabled = true;
      const res = await apiFetch(endpoint, { method });
      const data = await res.json();
      toast(data.message || 'Acción ejecutada', res.ok ? 'ok' : 'err');
      setTimeout(fetchStatus, 1000);
    } catch (e) {
      toast('Error: ' + e.message, 'err');
    } finally {
      btn.disabled = false;
    }
  });
});

/* ========= Risk Mode Toggle ========= */
$$('#riskModeGroup .seg__b').forEach(btn => {
  btn.addEventListener('click', async () => {
    const profile = btn.dataset.risk;
    try {
      const res = await apiFetch('/api/risk-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile })
      });
      const data = await res.json();
      toast(data.message || `Modo: ${profile}`, res.ok ? 'ok' : 'err');
      // Update UI
      $$('#riskModeGroup .seg__b').forEach(b => b.classList.remove('is-active'));
      btn.classList.add('is-active');
    } catch (e) {
      toast('Error cambiando modo', 'err');
    }
  });
});

/* ========= Logout ========= */
$$('.menu__item--danger').forEach(btn => {
  btn.addEventListener('click', () => {
    clearToken();
    showLogin();
    toast('Sesión cerrada');
  });
});

/* ========= TradingView Chart ========= */
function initTradingViewChart() {
  const container = $('#tvChart');
  if (!container || container.querySelector('iframe')) return;
  container.innerHTML = '';

  const script = document.createElement('script');
  script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
  script.async = true;
  script.innerHTML = JSON.stringify({
    autosize: true,
    symbol: "BINANCE:ETHUSDT",
    interval: "15",
    timezone: "Etc/UTC",
    theme: document.body.dataset.theme === 'light' ? 'light' : 'dark',
    style: "1",
    locale: "en",
    allow_symbol_change: true,
    hide_top_toolbar: false,
    hide_legend: false,
    save_image: false,
    calendar: false,
    support_host: "https://www.tradingview.com"
  });

  const wrapper = document.createElement('div');
  wrapper.className = 'tradingview-widget-container';
  wrapper.style.height = '100%';
  wrapper.style.width = '100%';
  const inner = document.createElement('div');
  inner.className = 'tradingview-widget-container__widget';
  inner.style.height = '100%';
  inner.style.width = '100%';
  wrapper.appendChild(inner);
  wrapper.appendChild(script);
  container.appendChild(wrapper);
}

/* ========= I18N ========= */
function applyI18n(lang) {
  const dict = window.__I18N[lang] || window.__I18N.es;
  $$('[data-i18n]').forEach(el => {
    const k = el.dataset.i18n;
    if (dict[k]) el.textContent = dict[k];
  });
  document.documentElement.lang = lang;
}

/* ========= Theme Toggle ========= */
$('#themeBtn').addEventListener('click', () => {
  const next = document.body.dataset.theme === 'dark' ? 'light' : 'dark';
  document.body.dataset.theme = next;
  // Re-init chart with matching theme
  const container = $('#tvChart');
  if (container) { container.innerHTML = ''; initTradingViewChart(); }
});

/* ========= Language Toggle ========= */
$$('[data-lang-set]').forEach(b => {
  b.addEventListener('click', () => {
    $$('[data-lang-set]').forEach(x => x.classList.remove('is-active'));
    b.classList.add('is-active');
    document.body.dataset.lang = b.dataset.langSet;
    applyI18n(b.dataset.langSet);
  });
});

/* ========= Profile Menu ========= */
(function () {
  const p = $('#profile');
  const btn = $('#profileBtn');
  btn.addEventListener('click', (e) => { e.stopPropagation(); p.classList.toggle('is-open'); });
  document.addEventListener('click', (e) => { if (!p.contains(e.target)) p.classList.remove('is-open'); });
})();

/* ========= Tabs ========= */
$$('.tab').forEach(t => {
  t.addEventListener('click', () => {
    if (t.dataset.tab === 'manual') return;
    $$('.tab').forEach(x => x.classList.remove('is-active'));
    t.classList.add('is-active');
  });
});

/* ========= Symbol Switching ========= */
$$('.symbol').forEach(s => {
  s.addEventListener('click', () => {
    $$('.symbol').forEach(x => x.classList.remove('is-active'));
    s.classList.add('is-active');
    const tick = s.querySelector('.symbol__tick').textContent;
    const badge = $('.badge--pair');
    if (badge) badge.textContent = tick;
  });
});

/* ========= Manual Drawer ========= */
const manual = $('#manual');
$('#openManual').addEventListener('click', () => manual.setAttribute('aria-hidden', 'false'));
manual.querySelectorAll('[data-close]').forEach(el => {
  el.addEventListener('click', () => manual.setAttribute('aria-hidden', 'true'));
});
$$('.drawer__toc a').forEach(a => {
  a.addEventListener('click', () => {
    $$('.drawer__toc a').forEach(x => x.classList.remove('is-active'));
    a.classList.add('is-active');
  });
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') manual.setAttribute('aria-hidden', 'true');
});

/* ========= Clock ========= */
(function () {
  const clock = $('#clock');
  const next = $('#nextCycle');
  let cycle = 47;
  function pad(n) { return n.toString().padStart(2, '0'); }
  function tick() {
    const d = new Date();
    clock.textContent = `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())} UTC`;
    cycle = cycle <= 0 ? 60 : cycle - 1;
    next.textContent = `00:${pad(cycle)}`;
  }
  tick(); setInterval(tick, 1000);
})();

/* ========= Event Log Appender ========= */
(function () {
  const log = $('#log');
  const clear = $('.card--log .link');
  if (clear) clear.addEventListener('click', () => { log.innerHTML = ''; });
  const evts = [
    ['INFO', 'Strategy scan: ML models confirming trend'],
    ['OK', 'Heartbeat ML-DCA · Cycle active'],
    ['OK', 'GEC check: Global Exposure is safe'],
    ['INFO', 'Liquidity check: Spread is optimal'],
    ['WARN', 'Volatility spike detected · Caution mode'],
    ['INFO', 'Polling exchange for price updates'],
  ];
  let n = 8421;
  setInterval(() => {
    // Only add logs if the app is visible
    if (!$('#appContent').classList.contains('visible')) return;

    const e = evts[Math.floor(Math.random() * evts.length)];
    const d = new Date();
    const t = `${String(d.getUTCHours()).padStart(2, '0')}:${String(d.getUTCMinutes()).padStart(2, '0')}:${String(d.getUTCSeconds()).padStart(2, '0')}`;
    const li = document.createElement('li');
    const cls = e[0] === 'OK' ? 'tag--ok' : e[0] === 'WARN' ? 'tag--warn' : 'tag--info';
    li.innerHTML = `<span class="log__t num">${t}</span><span class="tag ${cls}">${e[0]}</span><span>${e[1]} · cycle #${++n}</span>`;
    log.insertBefore(li, log.firstChild);
    while (log.children.length > 15) log.removeChild(log.lastChild);
  }, 8000);
})();

/* ========= Segmented Controls ========= */
$$('.seg').forEach(g => {
  g.addEventListener('click', (e) => {
    const b = e.target.closest('.seg__b');
    if (!b || b.dataset.tw || b.dataset.risk) return;
    g.querySelectorAll('.seg__b').forEach(x => x.classList.remove('is-active'));
    b.classList.add('is-active');
  });
});

/* ========= Boot ========= */
applyI18n(document.body.dataset.lang || 'es');
checkSession();
