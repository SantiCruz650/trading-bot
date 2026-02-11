/**
 * MCrypto v2 - Reactive Frontend (Netlify Ready)
 * Responsabilidad: Solo presentación y consulta de APIs.
 */

// Dynamic API detection: Use env variable or fallback to current host
// Dynamic API detection: Use env variable (Netlify/Vite)
const API_BASE = import.meta.env?.VITE_API_URL || "";

if (!API_BASE) {
    console.error("CRITICAL: VITE_API_URL not defined.");
}

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

        // New Canonical Status (Etapa 4.2.2)
        const statusRes = await fetch(`${API_BASE}/status`);
        const statusData = await statusRes.json();

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
            executions: executions.slice(0, 10),
            botStatus: statusData.status
        });

        markConnected(true, statusData.status);
    } catch (error) {
        markConnected(false);
    }
}

function updateControls(isConnected) {
    const isOffline = !isConnected || !API_BASE;
    els.btnStart.disabled = isOffline;
    els.btnStop.disabled = isOffline;
    els.btnKill.disabled = isOffline;

    if (isOffline) {
        els.btnStart.title = "Backend no conectado";
        els.btnStop.title = "Backend no conectado";
        els.btnKill.title = "Backend no conectado";
    } else {
        els.btnStart.title = "";
        els.btnStop.title = "";
        els.btnKill.title = "";
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
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        // Ensure POST always has a body to satisfy some strict backend parsers
        if (method === "POST") {
            options.body = JSON.stringify(body || { source: "dashboard" });
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
els.btnStart.addEventListener('click', () => sendAction('/start', 'POST', { mode: 'MOCK', source: 'dashboard' }));
els.btnStop.addEventListener('click', () => {
    if (confirm("¿Detener el Bot? Se mantendrán las posiciones abiertas.")) sendAction("/stop");
});
els.btnKill.addEventListener('click', () => {
    const code = prompt("🚨 EMERGENCIA: Escriba 'CONFIRMAR' para detener el bot y bloquear el sistema:");
    if (code === "CONFIRMAR") sendAction("/kill");
});

function markConnected(status, botStatus = "Offline") {
    uiState.connected = status;
    const isConnected = status && !!API_BASE;

    els.connStatus.className = `status-item ${isConnected ? 'active' : ''}`;

    if (!API_BASE) {
        els.connStatus.querySelector('.status-text').textContent = "Config Error";
        showNotification("Error: VITE_API_URL no configurado", "error");
    } else {
        els.connStatus.querySelector('.status-text').textContent = isConnected ? "Online" : "Unreachable";
    }

    updateControls(isConnected);

    if (isConnected) {
        const isWarning = botStatus.includes("KILLED") || botStatus.includes("PROTECTIVE");
        const isActive = botStatus.includes("RUNNING");

        els.sysState.className = `status-item ${isActive ? 'active' : ''} ${isWarning ? 'warning' : ''}`;
        els.sysState.querySelector('.status-text').textContent = botStatus;
    } else {
        els.sysState.className = "status-item";
        els.sysState.querySelector('.status-text').textContent = isConnected ? "---" : "Backend no conectado";
    }
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val);
}

refreshData();
setInterval(refreshData, UPDATE_INTERVAL);
