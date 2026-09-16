/**
 * PaperIntel AI - Client-side Application Logic (Vanilla JavaScript)
 * Communicates with FastAPI Backend at http://127.0.0.1:8000
 */

const API_BASE_URL = "http://127.0.0.1:8000";

// =============================================================================
// 1. Initialization on DOM Content Loaded
// =============================================================================
document.addEventListener("DOMContentLoaded", () => {
    checkSystemHealth();
    loadDashboardStatsAndRecentPapers();
    initHeroSearchForm();
});

// =============================================================================
// 2. Health Check Indicator
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
// 3. Load Stats & Recent Uploaded Papers
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
                <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
                    <p style="font-size: 1.1rem; margin-bottom: 0.5rem;">📂 No research papers indexed yet.</p>
                    <p style="font-size: 0.9rem; margin-bottom: 1.25rem;">Upload your first PDF paper to extract sections and keywords.</p>
                    <a href="upload.html" class="btn btn-primary">Upload Paper Now</a>
                </div>
            `;
            return;
        }

        // Render Recent Papers Cards
        papersContainer.innerHTML = papers.map(paper => `
            <div class="paper-item">
                <a href="viewer.html?id=${paper.id}" class="paper-item-title">
                    📄 ${escapeHtml(paper.title || paper.filename)}
                </a>
                <div class="paper-meta">
                    <span>✍️ ${escapeHtml(paper.authors || "Authors not specified")}</span>
                    <span>📑 ${paper.total_pages || 1} Page(s)</span>
                    <span>📦 ${formatBytes(paper.file_size_bytes || 0)}</span>
                    <span>🕒 ${formatDate(paper.uploaded_at)}</span>
                </div>
                ${paper.keywords && paper.keywords.length > 0 ? `
                    <div class="tag-list">
                        ${paper.keywords.map(k => `<span class="tag">🏷️ ${escapeHtml(k)}</span>`).join("")}
                    </div>
                ` : ""}
            </div>
        `).join("");

    } catch (error) {
        if (papersContainer) {
            papersContainer.innerHTML = `
                <div style="text-align: center; padding: 1.5rem; color: var(--danger);">
                    <p>⚠️ Unable to connect to FastAPI backend.</p>
                    <p style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
                        Make sure your backend is running at <code>http://127.0.0.1:8000</code>.
                    </p>
                </div>
            `;
        }
    }
}

// =============================================================================
// 4. Hero Live Search Form Handler
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
            sectionTitle.textContent = `🔍 Search Results for: "${query}"`;
        }

        if (papersContainer) {
            papersContainer.innerHTML = `
                <p style="text-align: center; color: var(--text-muted); padding: 1.5rem;">
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
                    <div style="text-align: center; padding: 2rem; color: var(--text-muted);">
                        <p style="font-size: 1.1rem; font-weight: 600;">No matching research papers found.</p>
                        <p style="font-size: 0.9rem; margin-top: 0.35rem;">
                            Try broader keywords like "attention", "network", "transformer", or "convolutional".
                        </p>
                    </div>
                `;
                return;
            }

            papersContainer.innerHTML = results.map(item => `
                <div class="paper-item">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem;">
                        <a href="viewer.html?id=${item.document_id}" class="paper-item-title">
                            📄 ${escapeHtml(item.title)}
                        </a>
                        <span class="score-badge">Relevance: ${item.score}</span>
                    </div>

                    <div class="paper-meta">
                        <span>✍️ ${escapeHtml(item.authors || "Authors not specified")}</span>
                        <span>📑 ${item.total_pages} Pages</span>
                        <span>🕒 ${formatDate(item.uploaded_at)}</span>
                    </div>

                    ${item.snippet ? `
                        <div class="paper-snippet">
                            "...${escapeHtml(item.snippet)}..."
                        </div>
                    ` : ""}

                    ${item.matched_keywords && item.matched_keywords.length > 0 ? `
                        <div class="tag-list">
                            ${item.matched_keywords.map(k => `<span class="tag">✓ ${escapeHtml(k)}</span>`).join("")}
                        </div>
                    ` : ""}
                </div>
            `).join("");

            // Smooth scroll to results
            papersContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });

        } catch (error) {
            papersContainer.innerHTML = `
                <div style="text-align: center; padding: 1.5rem; color: var(--danger);">
                    <p>Failed to execute search. Ensure the backend server is running.</p>
                </div>
            `;
        }
    });
}

// =============================================================================
// 5. Helper Formatting Functions
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
    if (bytes === 0) return "0 B";
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
