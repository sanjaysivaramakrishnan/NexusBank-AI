/**
 * NexusBank AI — Frontend Application
 * Handles chat interaction, message rendering, and API communication.
 */

(() => {
    "use strict";

    // --- Configuration ---
    const API_BASE = "";
    const MAX_CHARS = 2000;

    // --- Agent display metadata ---
    const AGENT_META = {
        supervisor: { label: "Supervisor", icon: "🤖", css: "supervisor" },
        customer_agent: { label: "Customer Agent", icon: "🏦", css: "customer_agent" },
        risk_agent: { label: "Risk & Fraud Agent", icon: "🛡️", css: "risk_agent" },
        credit_agent: { label: "Credit & Loan Agent", icon: "💳", css: "credit_agent" },
    };

    // --- State ---
    let sessionId = null;
    let isProcessing = false;

    // --- DOM refs ---
    const chatArea = document.getElementById("chat-area");
    const messageInput = document.getElementById("message-input");
    const btnSend = document.getElementById("btn-send");
    const btnReset = document.getElementById("btn-reset");
    const charCount = document.getElementById("char-count");
    const quickActions = document.getElementById("quick-actions");
    const agentStatus = document.getElementById("agent-status");

    // --- Initialise ---
    function init() {
        renderWelcome();
        bindEvents();
        messageInput.focus();
    }

    // --- Event binding ---
    function bindEvents() {
        btnSend.addEventListener("click", handleSend);

        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });

        messageInput.addEventListener("input", () => {
            autoResizeTextarea();
            charCount.textContent = `${messageInput.value.length} / ${MAX_CHARS}`;
        });

        btnReset.addEventListener("click", handleReset);

        document.querySelectorAll(".quick-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                const msg = btn.dataset.message;
                if (msg && !isProcessing) {
                    messageInput.value = msg;
                    handleSend();
                }
            });
        });
    }

    // --- Auto-resize textarea ---
    function autoResizeTextarea() {
        messageInput.style.height = "auto";
        messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
    }

    // --- Welcome screen ---
    function renderWelcome() {
        chatArea.innerHTML = `
            <div class="welcome-container">
                <div class="welcome-icon">🏦</div>
                <h2 class="welcome-title">Welcome to NexusBank AI</h2>
                <p class="welcome-subtitle">
                    Your intelligent banking assistant powered by multiple specialized AI agents.
                    Ask me about accounts, transactions, fraud detection, or loans.
                </p>
                <div class="welcome-agents">
                    <div class="welcome-agent-card">
                        <span class="agent-card-icon">🏦</span>
                        <div class="agent-card-info">
                            <h3>Customer Agent</h3>
                            <p>Accounts, balances, transactions</p>
                        </div>
                    </div>
                    <div class="welcome-agent-card">
                        <span class="agent-card-icon">🛡️</span>
                        <div class="agent-card-info">
                            <h3>Risk & Fraud Agent</h3>
                            <p>Fraud detection, risk analysis</p>
                        </div>
                    </div>
                    <div class="welcome-agent-card">
                        <span class="agent-card-icon">💳</span>
                        <div class="agent-card-info">
                            <h3>Credit & Loan Agent</h3>
                            <p>Eligibility, EMI, loan status</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // --- Send message ---
    async function handleSend() {
        const text = messageInput.value.trim();
        if (!text || isProcessing) return;

        // Clear welcome on first message
        const welcome = chatArea.querySelector(".welcome-container");
        if (welcome) welcome.remove();

        // Render user message
        appendMessage("user", text);

        // Clear input
        messageInput.value = "";
        messageInput.style.height = "auto";
        charCount.textContent = `0 / ${MAX_CHARS}`;

        // Hide quick actions after first use
        quickActions.style.display = "none";

        // Show typing indicator
        const typingEl = showTyping();
        setProcessing(true);

        try {
            const data = await sendChat(text);
            removeTyping(typingEl);
            appendMessage("bot", data.response, data.agent, data.routing_reasoning);
            sessionId = data.session_id;
        } catch (err) {
            removeTyping(typingEl);
            appendMessage("bot", `⚠️ Error: ${err.message}. Please check that the server is running and try again.`, "supervisor");
        } finally {
            setProcessing(false);
            messageInput.focus();
        }
    }

    // --- API call ---
    async function sendChat(message) {
        const res = await fetch(`${API_BASE}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Server error (${res.status})`);
        }

        return res.json();
    }

    // --- Render messages ---
    function appendMessage(role, text, agent = null, reasoning = null) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role === "user" ? "user-message" : "bot-message"}`;

        const avatarEmoji = role === "user" ? "👤" : (AGENT_META[agent]?.icon || "🤖");
        const avatarClass = role === "user" ? "user-avatar" : "bot-avatar";

        let badgeHTML = "";
        if (role === "bot" && agent) {
            const meta = AGENT_META[agent] || { label: agent, css: "supervisor" };
            let tooltipHTML = "";
            if (reasoning) {
                tooltipHTML = `
                    <span class="routing-info" data-tooltip="${escapeHtml(reasoning)}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                        </svg>
                    </span>`;
            }
            badgeHTML = `
                <div class="agent-badge ${meta.css}">
                    <span class="badge-dot"></span>
                    <span class="badge-text">${meta.label}</span>
                    ${tooltipHTML}
                </div>`;
        }

        const formattedText = role === "bot" ? formatBotText(text) : escapeHtml(text);

        msgDiv.innerHTML = `
            <div class="message-avatar ${avatarClass}"><span>${avatarEmoji}</span></div>
            <div class="message-content">
                ${badgeHTML}
                <div class="message-text">${formattedText}</div>
            </div>
        `;

        chatArea.appendChild(msgDiv);
        scrollToBottom();
    }

    // --- Format bot text (basic markdown) ---
    function formatBotText(text) {
        if (!text) return "";

        let html = escapeHtml(text);

        // Bold: **text**
        html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

        // Italic: *text*
        html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, "<em>$1</em>");

        // Inline code: `text`
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

        // Bullet lists: lines starting with - or •
        html = html.replace(/^[\-•]\s+(.+)$/gm, "<li>$1</li>");
        html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");

        // Numbered lists: lines starting with 1. 2. etc
        html = html.replace(/^\d+\.\s+(.+)$/gm, "<li>$1</li>");

        // Headings: ### text
        html = html.replace(/^###\s+(.+)$/gm, "<strong>$1</strong>");
        html = html.replace(/^##\s+(.+)$/gm, "<strong>$1</strong>");

        // Paragraphs: double newlines
        html = html.replace(/\n\n/g, "</p><p>");
        html = html.replace(/\n/g, "<br>");

        // Wrap in paragraph
        html = `<p>${html}</p>`;

        // Clean up empty paragraphs
        html = html.replace(/<p>\s*<\/p>/g, "");

        return html;
    }

    // --- Escape HTML ---
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    // --- Typing indicator ---
    function showTyping() {
        const template = document.getElementById("typing-template");
        const clone = template.content.cloneNode(true);
        const el = clone.querySelector(".message");
        chatArea.appendChild(clone);
        scrollToBottom();
        return chatArea.querySelector(".typing-indicator-msg");
    }

    function removeTyping(el) {
        if (el && el.parentNode) {
            el.remove();
        }
    }

    // --- Processing state ---
    function setProcessing(state) {
        isProcessing = state;
        btnSend.disabled = state;
        messageInput.disabled = state;

        const statusDot = agentStatus.querySelector(".status-dot");
        const statusText = agentStatus.querySelector(".status-text");

        if (state) {
            statusDot.className = "status-dot";
            statusDot.style.background = "var(--agent-supervisor)";
            statusDot.style.boxShadow = "0 0 8px var(--agent-supervisor)";
            statusDot.style.animation = "pulse-dot 0.8s ease-in-out infinite";
            statusText.textContent = "Processing...";
        } else {
            statusDot.className = "status-dot online";
            statusDot.style = "";
            statusText.textContent = "System Online";
        }
    }

    // --- Reset ---
    async function handleReset() {
        if (sessionId) {
            try {
                await fetch(`${API_BASE}/api/reset?session_id=${sessionId}`, { method: "POST" });
            } catch (_) {
                // Ignore
            }
        }
        sessionId = null;
        renderWelcome();
        quickActions.style.display = "";
        messageInput.value = "";
        charCount.textContent = `0 / ${MAX_CHARS}`;
        messageInput.focus();
    }

    // --- Scroll ---
    function scrollToBottom() {
        requestAnimationFrame(() => {
            chatArea.scrollTop = chatArea.scrollHeight;
        });
    }

    // --- Boot ---
    document.addEventListener("DOMContentLoaded", init);
})();
