/**
 * PaperIntel AI - Client-side Application Logic (Vanilla JavaScript)
 * Communicates with FastAPI Backend at http://127.0.0.1:8000
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// =============================================================================
// 1. Initialization on DOM Content Loaded
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
    initAuthUI();
    checkSystemHealth();
    loadDashboardStatsAndRecentPapers();
    initHeroSearchForm();
});

// =============================================================================
// 2. Authentication & User Session Management
// =============================================================================
function getAuthToken() {
    return localStorage.getItem("access_token");
}

function getCurrentUser() {
    const token = getAuthToken();
    if (!token) return null;
    return {
        id: localStorage.getItem("user_id"),
        username: localStorage.getItem("username"),
        full_name: localStorage.getItem("full_name") || localStorage.getItem("username") || "Researcher",
        email: localStorage.getItem("email")
    };
}

function logoutUser() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_id");
    localStorage.removeItem("username");
    localStorage.removeItem("full_name");
    localStorage.removeItem("email");
    window.location.href = "login.html";
}

function requireAuth(redirectUrl = window.location.pathname) {
    if (!getAuthToken()) {
        window.location.href = `login.html?redirect=${encodeURIComponent(redirectUrl)}`;
        return false;
    }
    return true;
}

function initAuthUI() {
    const navRight = document.querySelector(".nav-right");
    if (!navRight) return;

    // Remove any existing user widget
    const existingUserBadge = navRight.querySelector(".user-badge, .auth-nav-btn");
    if (existingUserBadge) existingUserBadge.remove();

    const user = getCurrentUser();

    if (user) {
        // Logged in user UI
        const userContainer = document.createElement("div");
        userContainer.className = "user-badge";
        userContainer.style.display = "inline-flex";
        userContainer.style.alignItems = "center";
        userContainer.style.gap = "0.6rem";
        userContainer.innerHTML = `
            <span style="display: inline-flex; align-items: center; gap: 0.35rem; cursor: pointer;" title="Username: ${escapeHtml(user.username)}">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                ${escapeHtml(user.full_name)}
            </span>
            <button type="button" id="logout-btn" style="background: none; border: none; color: var(--danger); font-size: 0.8rem; font-weight: 700; cursor: pointer; padding: 0.15rem 0.4rem; border-radius: 4px; display: inline-flex; align-items: center; gap: 0.25rem;" title="Sign out of account">
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                Logout
            </button>
        `;
        navRight.appendChild(userContainer);

        const logoutBtn = document.getElementById("logout-btn");
        if (logoutBtn) {
            logoutBtn.addEventListener("click", () => {
                if (confirm("Are you sure you want to sign out?")) {
                    logoutUser();
                }
            });
        }
    } else {
        // Logged out / Guest UI
        const loginBtn = document.createElement("a");
        loginBtn.href = "login.html";
        loginBtn.className = "btn btn-primary auth-nav-btn";
        loginBtn.style.padding = "0.35rem 0.85rem";
        loginBtn.style.fontSize = "0.85rem";
        loginBtn.style.display = "inline-flex";
        loginBtn.style.alignItems = "center";
        loginBtn.style.gap = "0.35rem";
        loginBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
            Sign In / Register
        `;
        navRight.appendChild(loginBtn);
    }
}

// =============================================================================
// 3. Health Check Indicator
// =============================================================================
async function checkSystemHealth() {
    const statusBadge = document.getElementById("system-status");
    const statusText = document.getElementById("status-text");

    if (!statusBadge || !statusText) return;

    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            statusBadge.className = "status-badge online";
            statusText.textContent = "Backend Online";
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        statusBadge.className = "status-badge offline";
        statusText.textContent = "Backend Offline";
        console.warn("Backend connection failed:", error);
    }
}

// =============================================================================
// 4. Load Stats & Recent Uploaded Papers
// =============================================================================
async function loadDashboardStatsAndRecentPapers() {
    const papersContainer = document.getElementById("papers-list-container");
    const statPapers = document.getElementById("stat-papers");
    const statSections = document.getElementById("stat-sections");
    const statKeywords = document.getElementById("stat-keywords");

    try {
        const response = await fetch(`${API_BASE_URL}/documents/?limit=5`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        const papers = data.documents || [];
        const totalDocs = data.total_documents || 0;

        if (statPapers) statPapers.textContent = totalDocs;
        if (statSections) statSections.textContent = totalDocs > 0 ? `${totalDocs * 5}+` : "0";
        if (statKeywords) statKeywords.textContent = totalDocs > 0 ? `${totalDocs * 10}+` : "0";

        if (!papersContainer) return;

        if (papers.length === 0) {
            papersContainer.innerHTML = `
                <div style="text-align: center; padding: 3rem 1.5rem; color: var(--text-muted);">
                    <div style="width: 48px; height: 48px; margin: 0 auto 1rem; border-radius: 50%; background: var(--primary-subtle); color: var(--primary); display: flex; align-items: center; justify-content: center;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                    </div>
                    <p style="font-size: 1.05rem; font-weight: 700; color: var(--text-main); margin-bottom: 0.35rem;">No research papers indexed yet</p>
                    <p style="font-size: 0.88rem; margin-bottom: 1.25rem;">Upload your first PDF paper to extract sections and keywords.</p>
                    <a href="upload.html" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 0.35rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                        Upload Paper Now
                    </a>
                </div>
            `;
            return;
        }

        // Render Recent Papers Cards
        papersContainer.innerHTML = papers.map(paper => `
            <div class="paper-item">
                <a href="viewer.html?id=${paper.id}" class="paper-item-title">
                    ${escapeHtml(paper.title || paper.filename)}
                </a>
                <div class="paper-meta">
                    <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                        ${escapeHtml(paper.authors || "Authors not specified")}
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                        ${paper.total_pages || 1} Page${(paper.total_pages || 1) === 1 ? '' : 's'}
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path></svg>
                        ${formatBytes(paper.file_size_bytes || 0)}
                    </span>
                    <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                        ${formatDate(paper.uploaded_at)}
                    </span>
                </div>
                ${paper.keywords && paper.keywords.length > 0 ? `
                    <div class="tag-list">
                        ${paper.keywords.slice(0, 5).map(k => `<span class="tag">${escapeHtml(k)}</span>`).join("")}
                    </div>
                ` : ""}
            </div>
        `).join("");

    } catch (error) {
        if (papersContainer) {
            papersContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--danger);">
                    <p style="font-weight: 700;">Unable to connect to FastAPI backend.</p>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
                        Make sure your backend is running at <code>http://127.0.0.1:8000</code>.
                    </p>
                </div>
            `;
        }
    }
}

// =============================================================================
// 5. Hero Live Search Form Handler
// =============================================================================
function initHeroSearchForm() {
    const form = document.getElementById("hero-search-form");
    const input = document.getElementById("hero-search-input");
    const papersContainer = document.getElementById("papers-list-container");
    const sectionTitle = document.getElementById("papers-section-title");

    if (!form || !input) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        if (sectionTitle) {
            sectionTitle.textContent = `Search Results for: "${query}"`;
        }

        if (papersContainer) {
            papersContainer.innerHTML = `
                <p style="text-align: center; color: var(--text-muted); padding: 2rem;">
                    Searching research papers...
                </p>
            `;
        }

        try {
            const response = await fetch(`${API_BASE_URL}/search/?q=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);

            const data = await response.json();
            const results = data.results || [];

            if (results.length === 0) {
                papersContainer.innerHTML = `
                    <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
                        <p style="font-size: 1.05rem; font-weight: 700; color: var(--text-main);">No matching research papers found.</p>
                        <p style="font-size: 0.88rem; margin-top: 0.35rem;">
                            Try broader terms like "attention", "transformer", "neural", or "diffusion".
                        </p>
                    </div>
                `;
                return;
            }

            papersContainer.innerHTML = results.map(item => `
                <div class="paper-item">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
                        <a href="viewer.html?id=${item.document_id}" class="paper-item-title">
                            ${escapeHtml(item.title)}
                        </a>
                        <span class="score-badge">${item.relevance_percentage || `${Math.round(item.score * 100)}%`} Match</span>
                    </div>

                    <div class="paper-meta">
                        <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                            ${escapeHtml(item.authors || "Authors not specified")}
                        </span>
                        <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                            ${item.total_pages} Pages
                        </span>
                        <span style="display: inline-flex; align-items: center; gap: 0.3rem;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                            ${formatDate(item.uploaded_at)}
                        </span>
                    </div>

                    ${item.snippet ? `
                        <div class="paper-snippet">
                            "${escapeHtml(item.snippet)}"
                        </div>
                    ` : ""}

                    ${item.matched_keywords && item.matched_keywords.length > 0 ? `
                        <div class="tag-list">
                            ${item.matched_keywords.map(k => `<span class="tag">${escapeHtml(k)}</span>`).join("")}
                        </div>
                    ` : ""}
                </div>
            `).join("");

            // Smooth scroll to results
            papersContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });

        } catch (error) {
            papersContainer.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--danger);">
                    <p>Failed to execute search. Ensure the backend server is running.</p>
                </div>
            `;
        }
    });
}

// =============================================================================
// 6. Helper Formatting Functions
// =============================================================================
function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatBytes(bytes) {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
}

function formatDate(isoString) {
    if (!isoString) return "";
    const date = new Date(isoString);
    return isNaN(date.getTime()) ? isoString : date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric"
    });
}
