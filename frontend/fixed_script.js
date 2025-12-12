const API_URL = "http://localhost:8000";
let authToken = localStorage.getItem("authToken") || "";

// --- DOM Elements ---
const splashScreen = document.getElementById("splash-screen");
const mainApp = document.getElementById("main-app");
const mcryptoForm = document.getElementById("mcrypto-form");
const mcryptoPassword = document.getElementById("mcrypto-password");
const mcryptoError = document.getElementById("mcrypto-error");

const authSection = document.getElementById("auth-section");
const registerSection = document.getElementById("register-section");
const dashboardSection = document.getElementById("dashboard-section");
const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const predictionForm = document.getElementById("prediction-form");
const loadingSpinner = document.getElementById("loading-spinner");
const predictionResult = document.getElementById("prediction-result");
const historyList = document.getElementById("history-list");
const logoutBtn = document.getElementById("logout-btn");

// --- Event Listeners ---
document.addEventListener("DOMContentLoaded", () => {
    // Check if user is already logged in
    if (authToken) {
        showDashboard();
    } else {
        splashScreen.classList.remove("d-none");
        mainApp.classList.add("d-none");
    }

    // MCrypto form submission
    mcryptoForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const password = mcryptoPassword.value;
        
        if (password === "MCrypto2024") {
            mcryptoError.classList.add("d-none");
            // Show auth section instead of directly going to dashboard
            splashScreen.classList.add("d-none");
            authSection.classList.remove("d-none");
            mainApp.classList.remove("d-none");
        } else {
            mcryptoError.classList.remove("d-none");
        }
    });

    // Login form submission
    loginForm.addEventListener("submit", handleLogin);

    // Register form submission
    registerForm.addEventListener("submit", handleRegister);

    // Prediction form submission
    predictionForm.addEventListener("submit", handlePrediction);

    // Logout button
    logoutBtn.addEventListener("click", handleLogout);

    // Show register form
    document.getElementById("show-register").addEventListener("click", (e) => {
        e.preventDefault();
        authSection.classList.add("d-none");
        registerSection.classList.remove("d-none");
    });

    // Show login form
    document.getElementById("show-login").addEventListener("click", (e) => {
        e.preventDefault();
        registerSection.classList.add("d-none");
        authSection.classList.remove("d-none");
    });
});

// --- Functions ---
function showDashboard() {
    splashScreen.classList.add("d-none");
    mainApp.classList.remove("d-none");
    authSection.classList.add("d-none");
    registerSection.classList.add("d-none");
    dashboardSection.classList.remove("d-none");
    loadPredictionHistory();
}

function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById("login-username").value;
    const password = document.getElementById("login-password").value;

    fetch(`${API_URL}/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `username=${username}&password=${password}`
    })
    .then(response => response.json())
    .then(data => {
        authToken = data.access_token;
        localStorage.setItem("authToken", authToken);
        showDashboard();
    })
    .catch(error => {
        console.error("Login error:", error);
        alert("Login failed. Please check your credentials.");
    });
}

function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById("register-username").value;
    const password = document.getElementById("register-password").value;

    fetch(`${API_URL}/register`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password })
    })
    .then(response => response.json())
    .then(data => {
        alert("Registration successful! Please login.");
        registerSection.classList.add("d-none");
        authSection.classList.remove("d-none");
    })
    .catch(error => {
        console.error("Registration error:", error);
        alert("Registration failed. Please try again.");
    });
}

function handlePrediction(e) {
    e.preventDefault();
    const ticker = document.getElementById("prediction-ticker").value;

    loadingSpinner.classList.remove("d-none");
    predictionResult.classList.add("d-none");

    fetch(`${API_URL}/predict/${ticker}`, {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        loadingSpinner.classList.add("d-none");
        displayPrediction(data);
        loadPredictionHistory();
    })
    .catch(error => {
        console.error("Prediction error:", error);
        loadingSpinner.classList.add("d-none");
        alert("Failed to get prediction. Please try again.");
    });
}

function displayPrediction(data) {
    const resultDiv = document.getElementById("prediction-details");
    
    let signalClass = "";
    if (data.signal === "BUY") {
        signalClass = "text-success";
    } else if (data.signal === "SELL") {
        signalClass = "text-danger";
    } else {
        signalClass = "text-warning";
    }

    resultDiv.innerHTML = `
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Prediction for ${data.ticker}</h5>
                <p class="card-text">
                    <strong>Last Close:</strong> $${data.last_close}<br>
                    <strong>Predicted Close:</strong> $${data.predicted_close}<br>
                    <strong>Signal:</strong> <span class="${signalClass}">${data.signal}</span><br>
                    <strong>Created At:</strong> ${new Date(data.created_at).toLocaleString()}
                </p>
            </div>
        </div>
    `;
    
    predictionResult.classList.remove("d-none");
}

function loadPredictionHistory() {
    fetch(`${API_URL}/my-predictions`, {
        headers: {
            "Authorization": `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        historyList.innerHTML = "";
        
        if (data.length === 0) {
            historyList.innerHTML = "<p class=\"text-muted\">No predictions yet.</p>";
            return;
        }

        data.forEach(prediction => {
            let signalClass = "";
            if (prediction.signal === "BUY") {
                signalClass = "text-success";
            } else if (prediction.signal === "SELL") {
                signalClass = "text-danger";
            } else {
                signalClass = "text-warning";
            }

            const predictionItem = document.createElement("div");
            predictionItem.className = "card mb-3";
            predictionItem.innerHTML = `
                <div class="card-body">
                    <h5 class="card-title">${prediction.ticker} - <span class="${signalClass}">${prediction.signal}</span></h5>
                    <p class="card-text">
                        <strong>Last Close:</strong> $${prediction.last_close}<br>
                        <strong>Predicted Close:</strong> $${prediction.predicted_close}<br>
                        <strong>Created At:</strong> ${new Date(prediction.created_at).toLocaleString()}
                    </p>
                </div>
            `;
            historyList.appendChild(predictionItem);
        });
    })
    .catch(error => {
        console.error("History error:", error);
    });
}

function handleLogout() {
    authToken = "";
    localStorage.removeItem("authToken");
    splashScreen.classList.remove("d-none");
    mainApp.classList.add("d-none");
    mcryptoPassword.value = "";
}
