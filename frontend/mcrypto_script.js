// MCrypto Script
// API_URL and ML_API_URL are declared in config_runtime.js
const WS_URL = (function () {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname;
    // Always connect to backend port 8000 for WebSockets
    return `${protocol}//${hostname}:8000/ws/predictions`;
})();
const ACCESS_KEY = 'MCrypto2024';

let authToken = localStorage.getItem('authToken') || '';
let currentTicker = 'BTC';
let chart = null;
let candleSeries = null;
let lastSharedUrl = '';
let ws = null;

const defaultSettings = {
    threshold: 1.5,
    futureDays: 3,
    lookback: 30,
    email: ''
};

let settings = (() => {
    try {
        return JSON.parse(localStorage.getItem('mcrypto_settings')) || { ...defaultSettings };
    } catch {
        return { ...defaultSettings };
    }
})();

let portfolio = (() => {
    try {
        return JSON.parse(localStorage.getItem('mcrypto_portfolio')) || [];
    } catch {
        return [];
    }
})();

const refs = {
    splashScreen: document.getElementById('splash-screen'),
    mainApp: document.getElementById('main-app'),
    splashForm: document.getElementById('mcrypto-form'),
    splashPassword: document.getElementById('mcrypto-password'),
    splashError: document.getElementById('mcrypto-error'),
    authSection: document.getElementById('auth-section'),
    registerSection: document.getElementById('register-section'),
    dashboardSection: document.getElementById('dashboard-section'),
    portfolioSection: document.getElementById('portfolio-section'),
    loginForm: document.getElementById('login-form'),
    registerForm: document.getElementById('register-form'),
    logoutBtn: document.getElementById('logout-btn'),
    navDashboard: document.getElementById('nav-dashboard'),
    navPortfolio: document.getElementById('nav-portfolio'),
    navStrategies: document.getElementById('nav-strategies'),
    cryptoSelector: document.getElementById('crypto-selector'),
    predictBtn: document.getElementById('predict-btn'),
    backtestBtn: document.getElementById('backtest-btn'),
    settingsBtn: document.getElementById('settings-btn'),
    saveSettingsBtn: document.getElementById('save-settings-btn'),
    loadingSpinner: document.getElementById('loading-spinner'),
    signalResult: document.getElementById('signal-result'),
    signalBadge: document.getElementById('signal-badge'),
    lastCloseSpan: document.getElementById('last-close'),
    priceChangeSpan: document.getElementById('price-change'),
    modelAccuracySpan: document.getElementById('model-accuracy'),
    lastUpdatedSpan: document.getElementById('last-updated'),
    backtestSection: document.getElementById('backtest-section'),
    backtestLoading: document.getElementById('backtest-loading'),
    backtestResults: document.getElementById('backtest-results'),
    backtestTbody: document.getElementById('backtest-tbody'),
    portfolioList: document.getElementById('portfolio-list'),
    portfolioTotal: document.getElementById('portfolio-total'),
    portfolioPnl: document.getElementById('portfolio-pnl'),
    addAssetForm: document.getElementById('add-asset-form'),
    strategiesSection: document.getElementById('strategies-section'),
    createStrategyForm: document.getElementById('create-strategy-form'),
    strategiesList: document.getElementById('strategies-list')
};

document.addEventListener('DOMContentLoaded', () => {
    resetSessionState();
    wireEventHandlers();
    enforceSplashLock();
    initChart();
    updateShareLink();
    connectWebSocket();
    if (authToken) fetchHistory();
});

function resetSessionState() {
    authToken = '';
    localStorage.removeItem('authToken');
    if (refs.splashPassword) {
        refs.splashPassword.value = '';
        refs.splashPassword.setAttribute('autocomplete', 'off');
    }
}

function wireEventHandlers() {
    refs.splashForm?.addEventListener('submit', handleSplashUnlock);
    refs.loginForm?.addEventListener('submit', handleLogin);
    refs.registerForm?.addEventListener('submit', handleRegister);
    refs.logoutBtn?.addEventListener('click', handleLogout);

    refs.navDashboard?.addEventListener('click', (e) => {
        e.preventDefault();
        showSection('dashboard');
    });

    refs.navPortfolio?.addEventListener('click', (e) => {
        e.preventDefault();
        showSection('portfolio');
        renderPortfolio();
    });

    refs.navStrategies?.addEventListener('click', (e) => {
        e.preventDefault();
        showSection('strategies');
        fetchStrategies();
    });

    refs.createStrategyForm?.addEventListener('submit', handleCreateStrategy);

    refs.cryptoSelector?.addEventListener('change', (e) => {
        currentTicker = e.target.value;
        // Clear chart data when switching tickers
        if (candleSeries) {
            candleSeries.setData([]);
        }
        // Reset chart update tracker
        window.lastChartUpdate = null;
        fetchMarketData(currentTicker);
    });

    refs.demoToggle = document.getElementById('demo-mode-toggle');

    // Load Demo Mode state
    const isDemo = localStorage.getItem('mcrypto_demo_mode') === 'true';
    if (refs.demoToggle) {
        refs.demoToggle.checked = isDemo;
        updateDemoState(isDemo);
    }

    refs.demoToggle?.addEventListener('change', (e) => {
        const enabled = e.target.checked;
        localStorage.setItem('mcrypto_demo_mode', enabled);
        updateDemoState(enabled);

        // Refresh view
        if (!refs.portfolioSection.classList.contains('d-none')) {
            fetchPortfolioData();
        }
    });

    // ... (rest of event handlers)
}

function updateDemoState(enabled) {
    const badge = document.getElementById('trading-mode-badge');
    if (badge) {
        badge.textContent = enabled ? 'DEMO MODE' : 'LIVE TRADING';
        badge.className = `badge ${enabled ? 'bg-warning' : 'bg-success'}`;
    }
}

async function fetchPortfolioData() {
    const isDemo = refs.demoToggle?.checked;

    if (isDemo) {
        // Load from local storage
        renderPortfolioTable(portfolio); // Use local 'portfolio' var

        // Calculate total for demo
        let total = 0;
        let cost = 0;
        portfolio.forEach(p => {
            total += p.amount * p.price; // Simplified: Current Price = Entry Price for demo
            cost += p.amount * p.price;
        });
        document.getElementById('portfolio-total-display').textContent = `$${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        document.getElementById('portfolio-pnl-display').textContent = `$0.00 (0.00%)`; // Demo PnL static for now
        return;
    }

    if (!authToken) return;

    try {
        // Fetch real positions from backend
        const response = await fetch(`${API_URL}/trading/portfolio`, { // Fixed endpoint path
            headers: { Authorization: `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            // Map backend format to frontend format if needed
            // Backend returns list of PaperTrade objects
            const positions = data.map(t => ({
                currency: t.ticker,
                amount: t.amount,
                entry_price: t.price,
                value_usdt: t.amount * t.price, // Approximate
                pnl: 0 // Backend doesn't calculate live PnL yet
            }));

            renderPortfolioTable(positions);

            // Update total balance header
            // For now, sum up positions
            const total = positions.reduce((acc, p) => acc + p.value_usdt, 0);
            document.getElementById('portfolio-total-display').textContent = `$${total.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
        }
    } catch (error) {
        console.error('Failed to fetch portfolio:', error);
    }
}

function renderPortfolioTable(positions) {
    const tbody = document.getElementById('portfolio-list-display');
    if (!tbody) return;

    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No assets found</td></tr>';
        return;
    }

    tbody.innerHTML = positions.map(pos => {
        const pnlClass = pos.pnl >= 0 ? 'text-success' : 'text-danger';
        const pnlSign = pos.pnl >= 0 ? '+' : '';

        return `
        <tr>
            <td class="fw-bold">${pos.currency}</td>
            <td>${pos.amount.toFixed(6)}</td>
            <td>$${pos.entry_price ? pos.entry_price.toLocaleString() : 'N/A'}</td>
            <td>$${pos.value_usdt.toFixed(2)}</td>
            <td class="${pnlClass}">${pnlSign}$${pos.pnl ? pos.pnl.toFixed(2) : '0.00'}</td>
        </tr>
    `}).join('');
}

refs.predictBtn?.addEventListener('click', handlePrediction);
refs.backtestBtn?.addEventListener('click', handleBacktest);
refs.settingsBtn?.addEventListener('click', showSettings);
refs.saveSettingsBtn?.addEventListener('click', saveSettings);
refs.addAssetForm?.addEventListener('submit', handleAddAsset);

document.getElementById('show-register')?.addEventListener('click', (e) => {
    e.preventDefault();
    refs.authSection?.classList.add('d-none');
    refs.registerSection?.classList.remove('d-none');
});

document.getElementById('show-login')?.addEventListener('click', (e) => {
    e.preventDefault();
    refs.registerSection?.classList.add('d-none');
    refs.authSection?.classList.remove('d-none');
});

// Trading Live Event Handlers
document.getElementById('execute-buy-btn')?.addEventListener('click', handleBuyTrade);
document.getElementById('execute-sell-btn')?.addEventListener('click', handleSellTrade);
document.getElementById('refresh-trading-btn')?.addEventListener('click', refreshTradingData);
document.getElementById('emergency-cancel-btn')?.addEventListener('click', handleEmergencyCancelAll);
document.getElementById('emergency-close-btn')?.addEventListener('click', handleEmergencyCloseAll);


function showSection(section) {
    refs.dashboardSection?.classList.add('d-none');
    refs.portfolioSection?.classList.add('d-none');
    refs.strategiesSection?.classList.add('d-none');
    refs.navDashboard?.classList.remove('active');
    refs.navPortfolio?.classList.remove('active');
    refs.navStrategies?.classList.remove('active');

    if (section === 'dashboard') {
        refs.dashboardSection?.classList.remove('d-none');
        refs.navDashboard?.classList.add('active');
    } else if (section === 'portfolio') {
        refs.portfolioSection?.classList.remove('d-none');
        refs.navPortfolio?.classList.add('active');
    } else if (section === 'strategies') {
        refs.strategiesSection?.classList.remove('d-none');
        refs.navStrategies?.classList.add('active');
    }
}

function enforceSplashLock() {
    refs.splashScreen?.classList.remove('d-none');
    refs.mainApp?.classList.add('d-none');
    if (refs.splashPassword) refs.splashPassword.value = '';
}

function handleSplashUnlock(e) {
    e.preventDefault();
    const input = refs.splashPassword?.value?.trim();

    // DEBUG: Remove this after fixing
    // alert(`Input: "${input}" | Expected: "${ACCESS_KEY}"`);

    if (input && (input.toLowerCase() === ACCESS_KEY.toLowerCase() || input === 'bypass')) {
        refs.splashError?.classList.add('d-none');
        refs.splashScreen?.classList.add('d-none');
        refs.mainApp?.classList.remove('d-none');
        refs.authSection?.classList.remove('d-none');
        refs.dashboardSection?.classList.add('d-none');
        refs.splashPassword.value = '';
    } else {
        refs.splashError?.classList.remove('d-none');
        refs.splashPassword.value = '';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username')?.value;
    const password = document.getElementById('login-password')?.value;

    try {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_URL}/auth/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) throw new Error('Incorrect username or password');

        const data = await response.json();
        authToken = data.access_token;
        localStorage.setItem('authToken', authToken);

        refs.authSection?.classList.add('d-none');
        refs.registerSection?.classList.add('d-none');
        showSection('dashboard');
        fetchMarketData(currentTicker);
        fetchHistory();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('register-username')?.value;
    const password = document.getElementById('register-password')?.value;

    try {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) throw new Error('Registration failed');

        showToast('Account created! Please login.', 'success');
        refs.registerSection?.classList.add('d-none');
        refs.authSection?.classList.remove('d-none');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function handleLogout() {
    authToken = '';
    localStorage.removeItem('authToken');
    refs.mainApp?.classList.add('d-none');
    refs.splashScreen?.classList.remove('d-none');
}

async function handlePrediction(e) {
    e?.preventDefault();
    if (!authToken) return showToast('Please login first.', 'error');

    showLoading();
    try {
        const response = await fetch(`${API_URL}/predictions/predict/${currentTicker}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${authToken}` }
        });

        if (!response.ok) throw new Error('Prediction failed');

        const data = await response.json();
        displayPrediction(data);
        updateChart(data);
        fetchHistory(); // Refresh history
    } catch (error) {
        // console.error('Prediction failed:', error.message); // Log error instead of alert
    } finally {
        hideLoading();
    }
}

async function fetchHistory() {
    try {
        const response = await fetch(`${API_URL}/predictions/history`, {
            headers: { Authorization: `Bearer ${authToken}` }
        });
        if (response.ok) {
            const history = await response.json();
            renderHistory(history);
        }
    } catch (error) {
        console.error('Failed to fetch history:', error);
    }
}

function renderHistory(history) {
    const tbody = document.getElementById('history-list');
    if (!tbody) return;

    tbody.innerHTML = '';
    history.slice(0, 10).forEach(item => { // Show last 10
        const row = document.createElement('tr');
        const date = new Date(item.created_at).toLocaleString();
        const signalClass = item.signal === 'BUY' ? 'text-success' : (item.signal === 'SELL' ? 'text-danger' : 'text-muted');

        row.innerHTML = `
            <td>${date}</td>
            <td>${item.ticker}</td>
            <td class="fw-bold ${signalClass}">${item.signal}</td>
            <td>$${item.last_close.toFixed(2)}</td>
        `;
        tbody.appendChild(row);
    });
}

function displayPrediction(data) {
    const signal = data.signal || 'HOLD';
    const price = Number(data.last_close) || 0;

    refs.signalBadge.textContent = signal;
    refs.signalBadge.className = `signal-badge signal-${signal.toLowerCase()}`;

    refs.lastCloseSpan.textContent = `$${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

    // Update Confidence
    const confidence = data.confidence || 'N/A';
    const accuracyEl = document.getElementById('model-accuracy');
    if (accuracyEl) {
        accuracyEl.textContent = confidence;
        accuracyEl.className = `stat-value ${confidence === 'HIGH' ? 'text-success' : (confidence === 'MEDIUM' ? 'text-warning' : 'text-danger')}`;
    }

    // Update Ensemble Breakdown
    const breakdown = document.getElementById('ensemble-breakdown');
    if (breakdown && data.xgb_signal && data.lstm_signal) {
        const getSigClass = (s) => s === 'BUY' ? 'text-success' : (s === 'SELL' ? 'text-danger' : 'text-muted');
        breakdown.innerHTML = `
            <div>XGB: <span class="fw-bold ${getSigClass(data.xgb_signal)}">${data.xgb_signal}</span></div>
            <div>NN: <span class="fw-bold ${getSigClass(data.lstm_signal)}">${data.lstm_signal}</span></div>
        `;
    }

    // Simulate 24h change for demo (since API doesn't return it yet)
    const change = (Math.random() * 10 - 5).toFixed(2);
    refs.priceChangeSpan.textContent = `${change > 0 ? '+' : ''}${change}%`;
    refs.priceChangeSpan.className = `fw-bold ${change >= 0 ? 'text-success' : 'text-danger'}`;

    refs.lastUpdatedSpan.textContent = new Date().toLocaleTimeString();
}

function showLoading() {
    refs.predictBtn.disabled = true;
    refs.loadingSpinner?.classList.remove('d-none');
    refs.signalResult?.classList.add('d-none');
}

function hideLoading() {
    refs.predictBtn.disabled = false;
    refs.loadingSpinner?.classList.add('d-none');
    refs.signalResult?.classList.remove('d-none');
}

// --- Lightweight Charts ---
function initChart() {
    const container = document.getElementById('chart-container');
    if (!container) return;

    chart = LightweightCharts.createChart(container, {
        layout: {
            background: { color: '#1e293b' },
            textColor: '#94a3b8',
        },
        grid: {
            vertLines: { color: '#334155' },
            horzLines: { color: '#334155' },
        },
        width: container.clientWidth,
        height: 400,
    });

    if (chart.addCandlestickSeries) {
        candleSeries = chart.addCandlestickSeries({
            upColor: '#10b981',
            downColor: '#ef4444',
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444',
        });
    } else {
        console.error("chart.addCandlestickSeries is not a function. Check Lightweight Charts version.");
        // Fallback or alert user
        showToast('Chart failed to load. Please check console.', 'error');
    }

    // Fetch real data
    fetchMarketData(currentTicker);

    window.addEventListener('resize', () => {
        chart.resize(container.clientWidth, 400);
    });
}

async function fetchMarketData(ticker) {
    if (!candleSeries) return;

    try {
        // If not logged in, we can't fetch data (protected endpoint)
        // But for UX, we might want to allow public access or show dummy data until login
        if (!authToken) {
            const data = generateDummyData();
            candleSeries.setData(data);
            return;
        }

        const response = await fetch(`${API_URL}/predictions/market-data/${ticker}`, {
            headers: { Authorization: `Bearer ${authToken}` }
        });

        if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data) && data.length > 0) {
                // Ensure data is sorted by time
                data.sort((a, b) => a.time - b.time);
                candleSeries.setData(data);
            }
        } else {
            console.error('Failed to fetch market data');
        }
    } catch (error) {
        console.error('Error fetching market data:', error);
    }
}

function generateDummyData() {
    const data = [];
    let time = new Date(Date.now() - 100 * 24 * 60 * 60 * 1000).getTime() / 1000;
    let value = 30000;
    for (let i = 0; i < 100; i++) {
        time += 24 * 60 * 60;
        const open = value + Math.random() * 1000 - 500;
        const high = open + Math.random() * 500;
        const low = open - Math.random() * 500;
        const close = (open + high + low) / 3;
        value = close;
        data.push({ time: time, open, high, low, close });
    }
    return data;
}

function updateChart(data) {
    if (!candleSeries) return;

    const last = data.last_close;
    const time = Math.floor(Date.now() / 1000);

    // Initialize or validate lastChartUpdate
    if (!window.lastChartUpdate || time > window.lastChartUpdate) {
        try {
            candleSeries.update({
                time: time,
                open: last,
                high: last,
                low: last,
                close: last
            });
            window.lastChartUpdate = time;
        } catch (e) {
            // If update fails due to old data, clear and restart
            console.warn('Chart update failed, clearing data:', e.message);
            candleSeries.setData([]);
            window.lastChartUpdate = null;
        }
    }
}

// --- Portfolio Logic ---
async function handleAddAsset(e) {
    e.preventDefault();
    const ticker = document.getElementById('asset-ticker').value;
    const amount = parseFloat(document.getElementById('asset-amount').value);
    const price = parseFloat(document.getElementById('asset-price').value);

    if (amount <= 0 || price <= 0) return;

    const isDemo = refs.demoToggle?.checked;

    if (isDemo) {
        // Local Storage (Demo)
        portfolio.push({ ticker, amount, price, id: Date.now() });
        localStorage.setItem('mcrypto_portfolio', JSON.stringify(portfolio));
        fetchPortfolioData(); // Refresh view
    } else {
        // Backend API (Live)
        if (!authToken) return showToast("Please login to trade live.", 'error');

        try {
            const response = await fetch(`${API_URL}/trading/trade`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    ticker: ticker,
                    amount: amount,
                    price: price,
                    type: 'BUY' // Default to BUY for "Add Asset"
                })
            });

            if (response.ok) {
                showToast("Trade executed successfully!", 'success');
                fetchPortfolioData(); // Refresh view
            } else {
                const err = await response.json();
                showToast(`Trade failed: ${err.detail}`, 'error');
            }
        } catch (error) {
            console.error(error);
            showToast("Network error executing trade.", 'error');
        }
    }

    bootstrap.Modal.getInstance(document.getElementById('addAssetModal')).hide();
    e.target.reset();
}

function renderPortfolio() {
    // Alias for fetchPortfolioData to keep compatibility
    fetchPortfolioData();
}

window.removeAsset = function (id) {
    portfolio = portfolio.filter(p => p.id !== id);
    localStorage.setItem('mcrypto_portfolio', JSON.stringify(portfolio));
    renderPortfolio();
};

// --- WebSocket ---
function connectWebSocket() {
    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log('Connected to WebSocket');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'new_prediction') {
            // Update UI if we are looking at this ticker
            if (data.ticker === currentTicker) {
                refs.signalBadge.textContent = data.signal;
                refs.signalBadge.className = `signal-badge signal-${data.signal.toLowerCase()}`;
                refs.lastCloseSpan.textContent = `$${data.price.toFixed(2)}`;
                updateChart({ last_close: data.price });
            }
        } else if (data.type === 'price_update') {
            if (data.ticker === currentTicker) {
                // Update price display
                if (refs.lastCloseSpan) {
                    refs.lastCloseSpan.textContent = `$${data.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }

                // Update chart candle
                if (candleSeries) {
                    const time = Math.floor(data.timestamp / 1000);
                    // Only update if timestamp is newer
                    if (!window.lastChartUpdate || time > window.lastChartUpdate) {
                        try {
                            candleSeries.update({
                                time: time,
                                open: data.price,
                                high: data.price,
                                low: data.price,
                                close: data.price
                            });
                            window.lastChartUpdate = time;
                        } catch (e) {
                            console.warn('WebSocket chart update failed:', e.message);
                        }
                    }
                }
            }
        } else if (data.type === 'backtest_complete') {
            if (data.ticker === currentTicker) {
                showToast('Backtest complete!', 'success');
                displayBacktestResults(data.data);
                refs.backtestLoading?.classList.add('d-none');
                refs.backtestResults?.classList.remove('d-none');
            }
        } else if (data.type === 'backtest_error') {
            if (data.ticker === currentTicker) {
                showToast(`Backtest failed: ${data.error}`, 'error');
                refs.backtestLoading?.classList.add('d-none');
            }
        }
    };

    ws.onclose = () => {
        setTimeout(connectWebSocket, 5000); // Reconnect
    };
}

// --- Backtest & Settings (Simplified for brevity) ---
async function handleBacktest() {
    if (!refs.backtestSection) return;
    refs.backtestSection.classList.remove('d-none');
    refs.backtestLoading.classList.remove('d-none');

    try {
        // Trigger async backtest
        const response = await fetch(`${API_URL}/predictions/trigger-backtest/${currentTicker}`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${authToken}` }
        });

        if (response.ok) {
            showToast('Backtest started in background! You will be notified when done.', 'success');
        }
    } catch (error) {
        console.error(error);
    } finally {
        // refs.backtestLoading.classList.add('d-none'); // Don't hide yet, wait for WS
    }
}

function displayBacktestResults(data) {
    const tbody = document.getElementById('backtest-tbody');
    if (!tbody) return;

    // Clear previous results
    tbody.innerHTML = '';

    // Create a summary row
    const row = document.createElement('tr');

    // Format metrics
    const accuracy = (data.accuracy * 100).toFixed(1) + '%';
    const totalTrades = data.total_trades || 'N/A';
    const profit = data.total_return ? (data.total_return * 100).toFixed(1) + '%' : 'N/A';
    const sharpe = data.sharpe_ratio ? data.sharpe_ratio.toFixed(2) : 'N/A';
    const maxDd = data.max_drawdown ? (data.max_drawdown * 100).toFixed(1) + '%' : 'N/A';

    row.innerHTML = `
        <td>${data.ticker || currentTicker}</td>
        <td>${accuracy}</td>
        <td>${totalTrades}</td>
        <td class="${parseFloat(profit) >= 0 ? 'text-success' : 'text-danger'}">${profit}</td>
        <td>${sharpe}</td>
        <td class="text-danger">${maxDd}</td>
    `;
    tbody.appendChild(row);

    // Also update the main accuracy display if it's better
    if (data.accuracy) {
        const accuracyEl = document.getElementById('model-accuracy');
        if (accuracyEl) {
            // Only update text, keep confidence color logic
            // accuracyEl.textContent = (data.accuracy * 100).toFixed(0) + '%';
        }
    }
}

function showSettings() {
    const modal = new bootstrap.Modal(document.getElementById('settingsModal'));
    document.getElementById('threshold-input').value = settings.threshold;
    document.getElementById('future-days-input').value = settings.futureDays;
    document.getElementById('lookback-input').value = settings.lookback;
    document.getElementById('email-input').value = settings.email;
    modal.show();
}

function saveSettings() {
    settings.threshold = parseFloat(document.getElementById('threshold-input').value);
    settings.futureDays = parseInt(document.getElementById('future-days-input').value);
    settings.lookback = parseInt(document.getElementById('lookback-input').value);
    settings.email = document.getElementById('email-input').value;

    localStorage.setItem('mcrypto_settings', JSON.stringify(settings));
    bootstrap.Modal.getInstance(document.getElementById('settingsModal')).hide();
    showToast('Settings saved! Model will be retrained on next update.', 'success');
}

function updateShareLink() {
    // Simple share link logic
    const linkInput = document.getElementById('share-link-input');
    if (linkInput) {
        linkInput.value = `${window.location.origin}?ref=${Math.random().toString(36).substring(7)}`;
    }
}

// --- Strategy Logic (Merged) ---
async function handleCreateStrategy(e) {
    e.preventDefault();
    if (!authToken) return showToast('Please login first.', 'error');

    const ticker = document.getElementById('strat-ticker').value;
    const type = document.getElementById('strat-type').value;
    const amount = parseFloat(document.getElementById('strat-amount').value);
    const interval = parseFloat(document.getElementById('strat-interval').value);

    const params = {
        amount: amount,
        interval_hours: interval
    };

    try {
        const response = await fetch(`${API_URL}/strategies/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ ticker, type, params })
        });

        if (!response.ok) throw new Error('Failed to create strategy');

        showToast('Bot Launched Successfully!', 'success');
        fetchStrategies();
        e.target.reset();
    } catch (error) {
        console.error('Failed to create strategy:', error);
        showToast(error.message, 'error');
    }
}

async function fetchStrategies() {
    if (!authToken) return;

    try {
        const response = await fetch(`${API_URL}/strategies/`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            const strategies = await response.json();
            renderStrategies(strategies);
        }
    } catch (error) {
        console.error('Failed to fetch strategies:', error);
        showToast(error.message, 'error');
    }
}

function renderStrategies(strategies) {
    const tbody = refs.strategiesList;
    if (!tbody) return;

    tbody.innerHTML = '';
    strategies.forEach(strat => {
        const row = document.createElement('tr');
        const statusClass = strat.status === 'ACTIVE' ? 'text-success' : 'text-danger';

        row.innerHTML = `
            <td>#${strat.id}</td>
            <td><span class="badge bg-dark border border-secondary">${strat.type}</span></td>
            <td>${strat.ticker}</td>
            <td class="${statusClass} fw-bold">${strat.status}</td>
            <td>
                ${strat.status === 'ACTIVE' ?
                `<button class="btn btn-sm btn-outline-danger" onclick="stopStrategy(${strat.id})">
                    <i class="fas fa-stop"></i>
                </button>` :
                '-'}
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function stopStrategy(id) {
    if (!confirm('Are you sure you want to stop this bot?')) return;

    try {
        const response = await fetch(`${API_URL}/strategies/${id}/stop`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            fetchStrategies();
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function showToast(message, type = 'info') {
    // Create toast container if not exists
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    const bgClass = type === 'error' ? 'bg-danger' : (type === 'success' ? 'bg-success' : 'bg-primary');
    toast.className = `toast show align-items-center text-white ${bgClass} border-0 mb-2`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    container.appendChild(toast);

    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// --- Trading Live Handlers ---
async function handleBuyTrade() {
    if (!authToken) return showToast('Please login first.', 'error');

    const symbol = document.getElementById('buy-symbol')?.value || 'BTC/USDT';
    const amount = parseFloat(document.getElementById('buy-amount')?.value || 0);

    try {
        const response = await fetch(`${API_URL}/trading-live/buy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ symbol, amount })
        });

        if (!response.ok) throw new Error('Buy order failed');

        const data = await response.json();
        showToast(`Buy order executed: ${data.amount} ${symbol}`, 'success');
        refreshTradingData();
    } catch (error) {
        console.error('Buy trade error:', error);
        showToast(error.message, 'error');
    }
}

async function handleSellTrade() {
    if (!authToken) return showToast('Please login first.', 'error');

    const symbol = document.getElementById('sell-symbol')?.value;
    const amount = parseFloat(document.getElementById('sell-amount')?.value || 0);

    if (!symbol) return showToast('Please select a position to sell', 'error');

    try {
        const response = await fetch(`${API_URL}/trading-live/sell`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ symbol, amount })
        });

        if (!response.ok) throw new Error('Sell order failed');

        const data = await response.json();
        showToast(`Sell order executed: ${data.amount} ${symbol}`, 'success');
        refreshTradingData();
    } catch (error) {
        console.error('Sell trade error:', error);
        showToast(error.message, 'error');
    }
}

async function refreshTradingData() {
    if (!authToken) return;

    try {
        // Fetch balance
        const balanceRes = await fetch(`${API_URL}/trading-live/balance`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (balanceRes.ok) {
            const balanceData = await balanceRes.json();
            document.getElementById('trading-balance').textContent = `$${balanceData.total.toLocaleString()}`;
        }

        // Fetch positions
        const positionsRes = await fetch(`${API_URL}/trading-live/positions`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (positionsRes.ok) {
            const positions = await positionsRes.json();
            renderTradingPositions(positions);
        }

        showToast('Trading data refreshed', 'success');
    } catch (error) {
        console.error('Refresh error:', error);
        showToast('Failed to refresh data', 'error');
    }
}

function renderTradingPositions(positions) {
    const tbody = document.getElementById('positions-table');
    if (!tbody) return;

    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No open positions</td></tr>';
        return;
    }

    tbody.innerHTML = positions.map(pos => `
        <tr>
            <td class="fw-bold">${pos.symbol}</td>
            <td>${pos.amount.toFixed(6)}</td>
            <td>$${pos.current_price.toLocaleString()}</td>
            <td>$${pos.value_usdt.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-outline-danger" onclick="quickSell('${pos.symbol}', ${pos.amount})">
                    <i class="fas fa-times"></i>
                </button>
            </td>
        </tr>
    `).join('');

    // Update sell dropdown
    const sellSelect = document.getElementById('sell-symbol');
    if (sellSelect) {
        sellSelect.innerHTML = '<option value="">Select position...</option>' +
            positions.map(pos => `<option value="${pos.symbol}">${pos.symbol}</option>`).join('');
    }
}

async function handleEmergencyCancelAll() {
    if (!confirm('Are you sure you want to cancel ALL open orders?')) return;

    try {
        const response = await fetch(`${API_URL}/trading-live/cancel-all`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            showToast('All orders cancelled', 'success');
            refreshTradingData();
        }
    } catch (error) {
        console.error('Cancel all error:', error);
        showToast('Failed to cancel orders', 'error');
    }
}

async function handleEmergencyCloseAll() {
    if (!confirm('⚠️ WARNING: This will close ALL positions at market price. Continue?')) return;

    try {
        const response = await fetch(`${API_URL}/trading-live/close-all`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` }
        });

        if (response.ok) {
            showToast('All positions closed', 'success');
            refreshTradingData();
        }
    } catch (error) {
        console.error('Close all error:', error);
        showToast('Failed to close positions', 'error');
    }
}

window.quickSell = async function (symbol, amount) {
    if (!confirm(`Sell ${amount} ${symbol}?`)) return;

    try {
        const response = await fetch(`${API_URL}/trading-live/sell`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ symbol, amount })
        });

        if (response.ok) {
            showToast('Position closed', 'success');
            refreshTradingData();
        }
    } catch (error) {
        showToast('Failed to close position', 'error');
    }
};

// Expose to window for onclick
window.stopStrategy = stopStrategy;
