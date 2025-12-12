(function () {
    const protocol = window.location.protocol;
    const hostname = window.location.hostname;
    
    // Always assume backend is on port 8000 of the same host
    const apiBase = `${protocol}//${hostname}:8000/api`;
    const mlBase = `${protocol}//${hostname}:8000/api/ml`;

    window.API_URL = window.API_URL || apiBase;
    window.ML_API_URL = window.ML_API_URL || mlBase;
})();
