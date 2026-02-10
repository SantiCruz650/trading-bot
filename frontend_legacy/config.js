// Configuration for different environments
const config = {
    local: {
        API_URL: 'http://localhost:8000',
        ML_URL: 'http://localhost:8001'
    },
    ngrok: {
        API_URL: window.location.protocol + '//' + window.location.host + '/api',
        ML_URL: window.location.protocol + '//' + window.location.host + '/ml'
    }
};

// Detect if we're running through ngrok
const isNgrok = window.location.hostname.includes('ngrok-free.dev');

// Export the configuration based on environment
const currentConfig = isNgrok ? config.ngrok : config.local;

export const API_URL = currentConfig.API_URL;
export const ML_URL = currentConfig.ML_URL;