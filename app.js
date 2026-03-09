console.log('--- VERSION 2.0 - CONEXION REPARADA ---');
/**
 * MCrypto v2 - Professional Trading Terminal
 * Architecture: APP CONTROLLER (Stricter Stabilization)
 */

const UPDATE_INTERVAL = 15000;

// 1. GLOBAL APP CONTROLLER
window.APP = {
    state: "BOOT",
    initialized: false,
    user: null,
    pollingTimeout: null,
    backoffDelay: 15000,
    maxBackoff: 60000,
    backendHealthy: true,
    mlHealthy: true,
    lastError: null
};

// 2. BOOTLOADER
document.addEventListener("DOMContentLoaded", startApp);

async function startApp() {
    if (APP.initialized) return;
    APP.initialized = true;

    // --- RESET ONBOARDING (VERSION 2.0 CRITICAL) ---
    if (!localStorage.getItem('terminal_v2_reset_final')) {
        console.warn("[System] CRITICAL RESET: Clearing localStorage for stabilization...");
        localStorage.clear();
        localStorage.setItem('terminal_v2_reset_final', 'true');
        // Re-set initial state after clear if needed (handled by navigate below)
    }

    console.info("[App] Booting Terminal...");

    const token = localStorage.getItem("access_token");

    if (!token) {
        console.info("[App] No session token found. Redirecting to auth.");
        APP.state = "UNAUTHENTICATED";
        navigate("auth");
        return;
    }

    showLoadingScreen("Verificando sesión...");

    try {
        const user = await api.request("/auth/verify");
        if (user && user.authenticated !== false) {
            APP.user = user;

            // Critical Rule 2.0: Check manual status before dashboard
            if (localStorage.getItem("manualAccepted") === "true") {
                console.info("[App] Session valid. Starting Dashboard...");
                startDashboard();
            } else {
                console.info("[App] Session valid but manual pending.");
                APP.state = "ONBOARDING";
                navigate("manual");
            }
        } else {
            throw new Error("Invalid session");
        }
    } catch (err) {
        console.warn("[App] Auth verification failed:", err.message);
        localStorage.removeItem("access_token");
        APP.state = "UNAUTHENTICATED";
        navigate("auth");
    }
}

// 3. DASHBOARD CONTROLLER
function startDashboard() {
    console.info("[App] Switching to DASHBOARD mode.");
    APP.state = "DASHBOARD";
    renderDashboard();
    startPolling();
}

function renderDashboard() {
    navigate("dashboard");
    refreshData(); // Initial immediate load
}

// 4. POLLING CONTROL (Exponential Backoff Implementation)
function startPolling() {
    if (APP.pollingTimeout) return;
    console.info("[System] Initializing Pollers...");
    APP.backoffDelay = UPDATE_INTERVAL; // Reset delay
    scheduleNextPoll(0); // Run immediately
}

function stopPolling() {
    if (APP.pollingTimeout) {
        console.info("[System] Halting Pollers.");
        clearTimeout(APP.pollingTimeout);
        APP.pollingTimeout = null;
    }
}

function scheduleNextPoll(delay) {
    if (APP.pollingTimeout) clearTimeout(APP.pollingTimeout);
    APP.pollingTimeout = setTimeout(async () => {
        try {
            await refreshData();
            // On success, reset backoff to default interval
            APP.backoffDelay = UPDATE_INTERVAL;
        } catch (err) {
            // Exponential backoff logic
            console.warn(`[System] Poll failed. Backing off... Original error: ${err.message}`);
            APP.backoffDelay = Math.min(APP.backoffDelay * 2, APP.maxBackoff);
        }

        // Always schedule next poll unless stopped
        if (APP.state === "DASHBOARD") {
            scheduleNextPoll(APP.backoffDelay);
        }
    }, delay);
}

// 5. NAVIGATOR (With Screen Clearing)
function navigate(view) {
    console.info(`[Router] View Transition -> ${view}`);

    // Critical Rule 6: Clear screen before render
    const containers = [
        els.loadingGuard,
        els.authContainer,
        els.dashboardContent,
        els.manualContainer,
        els.userProfile
    ];
    containers.forEach(c => { if (c) c.style.display = 'none'; });

    // Render Logic
    if (view === 'loading') {
        els.loadingGuard.style.display = 'flex';
    } else if (view === 'auth') {
        els.authContainer.style.display = 'flex';
    } else if (view === 'manual') {
        els.manualContainer.style.display = 'flex';
    } else if (view === 'dashboard') {
        els.dashboardContent.style.display = 'grid';
        els.userProfile.style.display = 'flex';
        if (APP.user) {
            els.userDisplay.textContent = APP.user.username;
        }
    }
}
window.navigate = navigate; // Allow global access for api.js
window.ui = { navigate: navigate }; // Compatibility with api.js

function showLoadingScreen(msg) {
    if (els.loadingGuard) {
        els.loadingGuard.querySelector('p').textContent = msg;
        navigate('loading');
    }
}

// 6. ELEMENT REGISTRY
const els = {
    loadingGuard: document.querySelector('#loading-guard'),
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

    // Major View Containers
    authContainer: document.querySelector('#auth-container'),
    dashboardContent: document.querySelector('#dashboard-content'),
    manualContainer: document.querySelector('#manual-container'),
    userProfile: document.querySelector('#user-profile'),
    userDisplay: document.querySelector('#user-display'),

    // Forms
    loginForm: document.querySelector('#login-form'),
    registerForm: document.querySelector('#register-form'),
    tabLogin: document.querySelector('#tab-login'),
    tabRegister: document.querySelector('#tab-register'),

    // Buttons
    btnStart: document.querySelector('#btn-start'),
    btnStop: document.querySelector('#btn-stop'),
    btnKill: document.querySelector('#btn-kill'),
    btnLogout: document.querySelector('#btn-logout'),
    btnAcceptManual: document.querySelector('#btn-accept-manual'),
    navManual: document.querySelector('#nav-manual'),
    btnResetManual: document.querySelector('#btn-reset-manual'),
    healthIcon: document.querySelector('#system-health-icon')
};

// 7. DATA PIPELINE
async function refreshData() {
    if (APP.state !== "DASHBOARD") return;

    try {
        const results = await Promise.allSettled([
            api.request('/trading/balance'),
            api.request('/strategies')
        ]);

        if (results.some(r => r.value && r.value.authenticated === false)) return;

        const data = {
            balance: results[0].status === 'fulfilled' ? results[0].value : { balance: 0, prices: { ETH: 0 }, stats: {} },
            strategies: results[1].status === 'fulfilled' ? results[1].value : []
        };

        let executions = [];
        if (data.strategies.length > 0) {
            try {
                executions = await api.request(`/strategies/${data.strategies[0].id}/executions`);
            } catch (e) {
                console.warn("[Data] Strategy executions fail.");
            }
        } else {
            // FALLBACK: Load general paper trades if no strategies exist
            try {
                console.info("[Data] No active strategies. Fetching general trades...");
                const trades = await api.request('/trading/trades');
                // Map PaperTrade model to execution display format
                executions = (trades || []).map(t => ({
                    order_type: t.type,
                    amount: t.amount,
                    price: t.price,
                    timestamp: t.created_at
                }));
            } catch (err) {
                console.warn("[Data] Trades fallback fail:", err.message);
            }
        }

        updateUI({
            balance: data.balance.balance || 0,
            price: data.balance.prices?.ETH || 0,
            equity: data.balance.equity || 0,
            drawdown: data.balance.stats?.daily_drawdown || 0,
            pnl: data.balance.stats?.pnl || 0,
            govMode: data.balance.stats?.gec_state || "NORMAL",
            er: data.balance.stats?.exposure || 0,
            executions: (executions || []).slice(0, 10)
        });

        markConnected(true);
        APP.backendHealthy = true;
        updateSystemHealthUI();
        refreshMLInsights();
    } catch (err) {
        console.error("[Data] Fault:", err.message);
        markConnected(false);
        APP.backendHealthy = false;
        APP.lastError = `Backend Fault: ${err.message}`;
        updateSystemHealthUI();
    }
}

async function refreshMLInsights() {
    try {
        const ml = await api.request('/ml/metrics/ETH');
        if (ml && ml.authenticated === false) return;
        els.regime.textContent = ml.regime || "N/A";
        els.confidence.textContent = ml.confidence || "---";
        els.shs.textContent = `${Math.round(ml.shs)}/100`;
        APP.mlHealthy = true;
        updateSystemHealthUI();
    } catch (error) {
        els.regime.textContent = "OFFLINE";
        APP.mlHealthy = false;
        APP.lastError = `ML Service Fault: ${error.message}`;
        updateSystemHealthUI();
    }
}

function updateSystemHealthUI() {
    if (!els.healthIcon) return;
    const isHealthy = APP.backendHealthy && APP.mlHealthy;
    els.healthIcon.className = `status-icon ${isHealthy ? 'ok' : 'err'}`;
}

// 8. RENDERERS
function updateUI(data) {
    els.equity.textContent = `${formatCurrency(data.equity)} USDT`;
    els.balance.textContent = `${formatCurrency(data.balance)}`;
    els.drawdown.textContent = `${(data.drawdown * 100).toFixed(2)}%`;
    els.dailyPnl.textContent = `${data.pnl >= 0 ? '+' : ''}${formatCurrency(data.pnl)}`;
    els.dailyPnl.className = `value ${data.pnl >= 0 ? 'positive' : 'negative'}`;
    els.price.textContent = `$${data.price.toLocaleString()}`;
    els.govMode.textContent = data.govMode;
    els.erBar.style.width = `${Math.min(100, data.er * 100)}%`;
    const erColor = data.er > 0.8 ? 'var(--danger)' : data.er > 0.6 ? 'var(--warning)' : 'var(--accent)';
    els.erBar.style.background = erColor;
    renderTrades(data.executions);
}

function renderTrades(executions) {
    if (!executions || executions.length === 0) {
        els.tradesList.innerHTML = '<p class="placeholder-text">Esperando datos...</p>';
        return;
    }
    els.tradesList.innerHTML = executions.map(ex => `
        <div class="trade-row">
            <span class="side-${ex.order_type.toLowerCase()}">${ex.order_type}</span>
            <span class="amount">${ex.amount} USDT</span>
            <span class="price">$${ex.price.toLocaleString()}</span>
            <span class="time">${new Date(ex.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
    `).join('');
}

function markConnected(status) {
    els.connStatus.className = `status-item ${status ? 'active' : ''}`;
    els.connStatus.querySelector('.status-text').textContent = status ? "Online" : "Offline";
}

function formatCurrency(val) {
    return new Intl.NumberFormat('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(val);
}

function showNotification(msg, type = "info") {
    const div = document.createElement('div');
    div.className = `notif ${type}`;
    div.textContent = msg;
    els.notifContainer.appendChild(div);
    setTimeout(() => div.classList.add('show'), 10);
    setTimeout(() => { div.classList.remove('show'); setTimeout(() => div.remove(), 300); }, 5000);
}

// 9. EVENTS
els.loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = document.querySelector('#login-username').value;
    const pass = document.querySelector('#login-password').value;
    try {
        await auth.login(user, pass);
        APP.initialized = false; // Reset for re-boot
        startApp();
    } catch (err) {
        showNotification(err.message, "error");
    }
});

els.btnLogout.addEventListener('click', () => {
    localStorage.removeItem('access_token');
    stopPolling();
    APP.state = "UNAUTHENTICATED";
    APP.user = null;
    navigate('auth');
});

els.btnAcceptManual.addEventListener('click', async () => {
    try {
        // Guardar manualVisto: true as requested by user
        localStorage.setItem("manualVisto", "true");
        localStorage.setItem("manualAccepted", "true");

        // After manual, check where to go
        const token = localStorage.getItem("access_token");
        if (!token) {
            APP.state = "UNAUTHENTICATED";
            navigate("auth");
        } else if (APP.user) {
            APP.state = "DASHBOARD";
            startDashboard();
        } else {
            // Token exists but user not verified yet? 
            // Re-run startApp logic or just go to auth
            APP.state = "UNAUTHENTICATED";
            navigate("auth");
        }

        // Optional: inform backend
        api.request("/auth/accept-manual", { method: "POST" }).catch(() => { });
    } catch (err) {
        showNotification(err.message, "error");
    }
});

els.tabLogin.addEventListener('click', () => switchAuthTab('login'));
els.tabRegister.addEventListener('click', () => switchAuthTab('register'));

function switchAuthTab(tab) {
    if (tab === 'login') {
        els.tabLogin.classList.add('active'); els.tabRegister.classList.remove('active');
        els.loginForm.style.display = 'block'; els.registerForm.style.display = 'none';
    } else {
        els.tabRegister.classList.add('active'); els.tabLogin.classList.remove('active');
        els.registerForm.style.display = 'block'; els.loginForm.style.display = 'none';
    }
}

// Bot Actions
async function sendAction(endpoint, method = "POST", body = null) {
    try {
        const data = await api.request(endpoint, { method, body: body ? JSON.stringify(body) : null });
        if (data && data.authenticated === false) return;
        showNotification(data.message || "Éxito", "success");
        setTimeout(refreshData, 1000);
    } catch (err) {
        showNotification(err.message, "error");
    }
}

els.btnStart.addEventListener('click', () => sendAction("/trading/start"));
els.btnStop.addEventListener('click', () => sendAction("/trading/stop"));
els.btnKill.addEventListener('click', () => sendAction("/trading/kill-switch"));
els.navManual.addEventListener('click', () => navigate('manual'));
if (els.btnResetManual) {
    els.btnResetManual.addEventListener('click', () => {
        console.info("--- FORZANDO RENDERIZADO DE MANUAL (RESET) ---");
        navigate('manual');
    });
}
els.healthIcon.addEventListener('click', () => {
    if (APP.lastError) {
        alert(`Último error del sistema:\n\n${APP.lastError}`);
    } else {
        showNotification("Sistema operando normalmente", "success");
    }
});
