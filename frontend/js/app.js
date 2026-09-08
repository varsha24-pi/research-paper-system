// Base API URL for FastAPI backend
const API_BASE_URL = "http://127.0.0.1:8000";

// Check backend health on page load
document.addEventListener("DOMContentLoaded", async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        console.log("Backend status:", data);
    } catch (error) {
        console.warn("Backend is currently offline or unreachable.", error);
    }
});
