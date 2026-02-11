async function handleCreateStrategy(e) {
    e.preventDefault();
    if (!authToken) return alert('Please login first.');

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

        alert('Bot Launched Successfully!');
        fetchStrategies();
    } catch (error) {
        alert(error.message);
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
        alert('Failed to stop strategy');
    }
}

// Expose to window for onclick
window.stopStrategy = stopStrategy;
