/**
 * MCrypto v2 - Reactive Frontend (Netlify Ready)
 * Responsabilidad: Solo presentación y consulta de APIs.
 */

// Dynamic API detection: Use env variable or fallback to current host
const API_BASE =
    window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? "http://localhost:8000/api"
        : "https://trading-bot-kea3.onrender.com/api";

const UPDATE_INTERVAL = 15000;

let uiState = {
    connected: false,
    lastUpdate: null,
};

const els = {
    connStatus: document.querySelector('#connection-status'),
    sysState: document.querySelector('#system-state'),
    equity: document.querySelector('#equity-value'),
    dailyPnl: document.querySelector('#daily-pnl'),
    drawdown: document.querySelector('#current-drawdown'),
    balance: document.querySelector('#usdt-balance'),
    price: document.querySelector('#eth-price'),
    regime: document.querySelector('#market-regime'),
    confidence: document.querySelector('#ml-confidence'),
    shs: document.querySelector('#shs-score'),
    erBar: document.querySelector('#er-bar'),
    govMode: document.querySelector('#gov-mode'),
    tradesList: document.querySelector('#trades-list'),
    lastUpdateTs: document.querySelector('#last-update'),
    notifContainer: document.querySelector('#notification-container'),

    // Controls
    btnStart: document.querySelector('#btn-start'),
    btnStop: document.querySelector('#btn-stop'),
    btnKill: document.querySelector('#btn-kill'),
    btnNormal: document.querySelector('#mode-normal'),
    btnCons: document.querySelector('#mode-conservative')
};

async function refreshData() {
    try {
        const balanceRes = await fetch(`${API_BASE}/trading/balance`);
        if (!balanceRes.ok) throw new Error("Backend unreachable");
        const balanceData = await balanceRes.json();

        const strategyId = 2; // ETH
        const strategyRes = await fetch(`${API_BASE}/strategies/${strategyId}`);
        const strategyData = await strategyRes.json();

        const mlRes = await fetch(`${API_BASE}/ml/metrics/ETH`);
        const mlData = await mlRes.json();

        const execRes = await fetch(`${API_BASE}/strategies/${strategyId}/executions`);
        const executions = await execRes.json();

        updateUI({
            balance: balanceData.balance,
            price: balanceData.prices?.ETH || 0,
            equity: balanceData.equity || 0,
            drawdown: balanceData.stats?.daily_drawdown || 0,
            pnl: balanceData.stats?.pnl || 0,
            regime: mlData.regime || "UNKNOWN",
            confidence: mlData.confidence || "---",
            shs: mlData.shs || 0,
            govMode: balanceData.stats?.gec_state || "NORMAL",
            er: balanceData.stats?.exposure || 0,
            executions: executions.slice(0, 10)
        });

        markConnected(true);
    } catch (error) {
        markConnected(false);
    }
}

function updateUI(data) {
    els.equity.textContent = `${formatCurrency(data.equity)} USDT`;
    els.balance.textContent = `${formatCurrency(data.balance)}`;
    els.drawdown.textContent = `${(data.drawdown * 100).toFixed(2)}%`;
    els.dailyPnl.textContent = `${data.pnl >= 0 ? '+' : ''}${formatCurrency(data.pnl)}`;
    els.dailyPnl.className = `value ${data.pnl >= 0 ? 'positive' : 'negative'}`;
    els.price.textContent = `$${data.price.toLocaleString()}`;
    els.regime.textContent = data.regime;
    els.confidence.textContent = data.confidence;
    els.shs.textContent = `${Math.round(data.shs)}/100`;
    els.govMode.textContent = data.govMode;
    els.erBar.style.width = `${Math.min(100, data.er * 100)}%`;
    const erColor = data.er > 0.8 ? 'var(--danger)' : data.er > 0.6 ? 'var(--warning)' : 'var(--accent)';
    els.erBar.style.background = erColor;
    renderTrades(data.executions);
    els.lastUpdateTs.textContent = `Actualizado: ${new Date().toLocaleTimeString()}`;
}

function renderTrades(executions) {
    if (!executions || executions.length === 0) return;
    els.tradesList.innerHTML = executions.map(ex => `
        <div class="trade-row">
            <span class="side-${ex.order_type.toLowerCase()}">${ex.order_type}</span>
            <span class="amount">${ex.amount} USDT</span>
            <span class="price">$${ex.price.toLocaleString()}</span>
            <span class="time">${new Date(ex.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
    `).join('');
}

// Actions
async function sendAction(endpoint, method = "POST", body = null) {
    try {
        const options = { method };
        if (body) {
            options.headers = { 'Content-Type': 'application/json' };
            options.body = JSON.stringify(body);
        }
        const res = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await res.json();

        if (res.ok) {
            showNotification(data.message || "Acción completada con éxito", "success");
            setTimeout(refreshData, 1000);
        } else {
            throw new Error(data.detail || "Error en la operación");
        }
    } catch (err) {
        showNotification(err.message, "error");
    }
}

function showNotification(msg, type = "info") {
    const div = document.createElement('div');
    div.className = `notif ${type}`;
    div.textContent = msg;
    els.notifContainer.appendChild(div);
    setTimeout(() => div.classList.add('show'), 10);
    setTimeout(() => {
        div.classList.remove('show');
        setTimeout(() => div.remove(), 300);
    }, 5000);
}

// Event Listeners
els.btnStart.addEventListener('click', () => {
    if (confirm("¿Encender el Bot y comenzar operaciones?")) sendAction("/trading/start");
});
els.btnStop.addEventListener('click', () => {
    if (confirm("¿Detener el Bot? Se mantendrán las posiciones abiertas.")) sendAction("/trading/stop");
});
els.btnKill.addEventListener('click', () => {
    const code = prompt("🚨 EMERGENCIA: Escriba 'CONFIRMAR' para detener el bot y cancelar todo:");
    if (code === "CONFIRMAR") sendAction("/trading/kill-switch");
});

els.btnNormal.addEventListener('click', () => {
    els.btnNormal.classList.add('active');
    els.btnCons.classList.remove('active');
    sendAction("/trading/mode", "POST", { mode: "NORMAL" });
});
els.btnCons.addEventListener('click', () => {
    els.btnCons.classList.add('active');
    els.btnNormal.classList.remove('active');
    sendAction("/trading/mode", "POST", { mode: "CONSERVATIVE" });
});

function markConnected(status) {
    uiState.connected = status;
    els.connStatus.className = `status-item ${status ? 'active' : ''}`;
    els.connStatus.querySelector('.status-text').textContent = status ? "Online" : "Offline";
    if (status) {
        els.sysState.className = "status-item active";
        els.sysState.querySelector('.status-text').textContent = "Operativo";
    }
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val);
}

refreshData();
setInterval(refreshData, UPDATE_INTERVAL);
