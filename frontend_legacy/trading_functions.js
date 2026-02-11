
// ==========================================
// LIVE TRADING FUNCTIONS
// ==========================================

async function fetchTradingData() {
    try {
        // Fetch balance
        const balanceResp = await fetch(`${API_URL}/trading-live/balance`, {
            headers: { Authorization: `Bearer ${authToken}` }
        });
        if (balanceResp.ok) {
            const balanceData = await balanceResp.json();
            document.getElementById('trading-balance').textContent = balanceData.formatted;
        }

        // Fetch positions
        const posResp = await fetch(`${API_URL}/trading-live/positions`, {
            headers: { Authorization: `Bearer ${authToken}` }
        });
        if (posResp.ok) {
            const posData = await posResp.json();
            renderPositions(posData.positions);
            document.getElementById('position-count').textContent = posData.count;
        }

        // Fetch risk stats
        const riskResp = await fetch(`${API_URL}/trading-live/risk/stats`, {
            headers: { Authorization: `Bearer ${authToken}` }
        });
        if (riskResp.ok) {
            const riskData = await riskResp.json();
            document.getElementById('daily-trades').textContent = riskData.daily_trades;
            const pnl = riskData.daily_pnl;
            const pnlEl = document.getElementById('daily-pnl');
            pnlEl.textContent = `$${Math.abs(pnl).toFixed(2)}`;
            pnlEl.className = `stat-value ${pnl >= 0 ? 'text-success' : 'text-danger'}`;
        }
    } catch (error) {
        console.error('Failed to fetch trading data:', error);
    }
}

function renderPositions(positions) {
    const tbody = document.getElementById('positions-table');
    const sellSelect = document.getElementById('sell-symbol');

    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No open positions</td></tr>';
        sellSelect.innerHTML = '<option value="">No positions</option>';
        return;
    }

    // Update positions table
    tbody.innerHTML = positions.map(pos => `
        <tr>
            <td>${pos.currency}</td>
            <td>${pos.amount.toFixed(6)}</td>
            <td>$${pos.current_price.toLocaleString()}</td>
            <td>$${pos.value_usdt.toFixed(2)}</td>
            <td>
                <button class="btn btn-sm btn-danger" onclick="quickSell('${pos.symbol}', ${pos.amount})">
                    Sell All
                </button>
            </td>
        </tr>
    `).join('');

    // Update sell dropdown
    sellSelect.innerHTML = '<option value="">Select position...</option>' +
        positions.map(pos => `<option value="${pos.symbol}" data-amount="${pos.amount}">${pos.currency}</option>`).join('');
}

async function executeTrade(side) {
    const symbol = side === 'buy' ? document.getElementById('buy-symbol').value : document.getElementById('sell-symbol').value;
    const amountInput = side === 'buy' ? null : parseFloat(document.getElementById('sell-amount').value);

    if (!symbol) {
        alert('Please select a symbol');
        return;
    }

    if (side === 'sell' && (!amountInput || amountInput <= 0)) {
        alert('Please enter a valid amount to sell');
        return;
    }

    const confirmed = confirm(`Execute ${side.toUpperCase()} order for ${symbol}?`);
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/trading-live/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Authorization: `Bearer ${authToken}`
            },
            body: JSON.stringify({
                symbol: symbol,
                side: side,
                amount: amountInput
            })
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}\nOrder ID: ${data.order_id}\nPrice: $${data.price}\nValue: $${data.value_usdt.toFixed(2)}`);
            fetchTradingData(); // Refresh
            if (side === 'sell') document.getElementById('sell-amount').value = '';
        } else {
            alert(`❌ Error: ${data.detail}`);
        }
    } catch (error) {
        console.error('Trade execution error:', error);
        alert(`❌ Failed to execute trade: ${error.message}`);
    }
}

async function quickSell(symbol, amount) {
    const confirmed = confirm(`Sell ALL ${amount.toFixed(6)} ${symbol}?`);
    if (!confirmed) return;

    document.getElementById('sell-symbol').value = symbol;
    document.getElementById('sell-amount').value = amount;
    await executeTrade('sell');
}

async function emergencyCloseAll() {
    const confirmed = confirm('⚠️ CLOSE ALL POSITIONS?\n\nThis will sell all holdings immediately at market price.\n\nAre you sure?');
    if (!confirmed) return;

    const doubleConfirm = confirm('⚠️⚠️ FINAL CONFIRMATION ⚠️⚠️\n\nThis action cannot be undone!\n\nProceed with closing all positions?');
    if (!doubleConfirm) return;

    try {
        const response = await fetch(`${API_URL}/trading-live/emergency/close-all`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${authToken}` }
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            fetchTradingData();
        } else {
            alert(`❌ Error: ${data.detail}`);
        }
    } catch (error) {
        console.error('Emergency close error:', error);
        alert(`❌ Failed: ${error.message}`);
    }
}

async function emergencyCancelOrders() {
    const confirmed = confirm('Cancel all pending orders?');
    if (!confirmed) return;

    try {
        const response = await fetch(`${API_URL}/trading-live/emergency/cancel-orders`, {
            method: 'POST',
            headers: { Authorization: `Bearer ${authToken}` }
        });

        const data = await response.json();

        if (response.ok) {
            alert(`✅ ${data.message}`);
            fetchTradingData();
        } else {
            alert(`❌ Error: ${data.detail}`);
        }
    } catch (error) {
        console.error('Emergency cancel error:', error);
        alert(`❌ Failed: ${error.message}`);
    }
}

// Event listeners for trading
document.getElementById('execute-buy-btn')?.addEventListener('click', () => executeTrade('buy'));
document.getElementById('execute-sell-btn')?.addEventListener('click', () => executeTrade('sell'));
document.getElementById('refresh-trading-btn')?.addEventListener('click', fetchTradingData);
document.getElementById('emergency-close-btn')?.addEventListener('click', emergencyCloseAll);
document.getElementById('emergency-cancel-btn')?.addEventListener('click', emergencyCancelOrders);

// Auto-refresh trading data every 10 seconds
setInterval(() => {
    if (authToken && !document.getElementById('dashboard-section')?.classList.contains('d-none')) {
        fetchTradingData();
    }
}, 10000);

// Initial load
if (authToken) {
    fetchTradingData();
}
