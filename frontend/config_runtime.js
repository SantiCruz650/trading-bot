(function () {
    // Use the current origin (protocol + hostname + port if any)
    // This works for both localhost:8000 and production domains
    const origin = window.location.origin;

    window.API_URL = `${origin}/api`;
    window.ML_API_URL = `${origin}/api/ml`;
})();
