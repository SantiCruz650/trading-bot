console.log('--- VERSION 2.0 - CONEXION REPARADA ---');
/**
 * api.js - Wrapper para fetch con autenticación
 */

const api = {
    async request(endpoint, options = {}) {
        const token = auth.getToken();

        const defaultHeaders = {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
        };

        if (token) {
            defaultHeaders['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            ...options,
            credentials: 'include', // Para soporte opcional de cookies/sesión
            headers: {
                ...defaultHeaders,
                ...options.headers
            }
        };

        try {
            const response = await fetch(`${window.API_BASE_URL}${endpoint}`, config);

            if (response.status === 401) {
                console.info("[API Security] 401 Unauthorized. Triggering system lockdown.");

                // Clear state
                localStorage.removeItem('access_token');
                if (window.stopPolling) window.stopPolling();
                window.authState = "unauthenticated";

                // If the app is initialized, force navigation
                if (window.ui && window.ui.navigate) {
                    window.ui.navigate('auth');
                }

                return { authenticated: false };
            }

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Error en la petición');
            }

            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }
};

// Exponer globalmente
window.api = api;
window.API_BASE_URL = API_BASE_URL;
