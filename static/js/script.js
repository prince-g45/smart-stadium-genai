const chatForm = document.getElementById("chat-form");
const chatWindow = document.getElementById("chat-window");
const userInput = document.getElementById("user-input");
const langSelect = document.getElementById("lang-select");
const stadiumSelect = document.getElementById("stadium-select");
const typingIndicator = document.getElementById("typing-indicator");
const themeToggle = document.getElementById("theme-toggle");
const themeLabel = document.getElementById("theme-label");
const newChatBtn = document.getElementById("new-chat");
const micBtn = document.getElementById("mic-btn");
const gateList = document.getElementById("gate-list");

function appendMessage(text, sender) {
    const div = document.createElement("div");
    div.className = sender === "user" ? "user-message" : "bot-message";
    div.textContent = text;
    chatWindow.appendChild(div);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

function showTyping(show) {
    typingIndicator.hidden = !show;
    if (show) {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }
}

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    themeLabel.textContent = theme === "dark" ? "Light mode" : "Dark mode";
}

function localStorageSafeGet(key) {
    try {
        return window.localStorage.getItem(key);
    } catch (e) {
        return null;
    }
}

function localStorageSafeSet(key, value) {
    try {
        window.localStorage.setItem(key, value);
    } catch (e) {
        // ignore - theme just won't persist across reloads
    }
}

function initTheme() {
    const saved = localStorageSafeGet("theme") || "dark";
    applyTheme(saved);
}

themeToggle.addEventListener("click", function () {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    applyTheme(next);
    localStorageSafeSet("theme", next);
});

function statusToClass(status) {
    return "status-" + status.toLowerCase().replace(/\s+/g, "-");
}

async function refreshGates(stadiumId) {
    try {
        const response = await fetch(`/api/gates?stadium_id=${encodeURIComponent(stadiumId)}`);
        if (!response.ok) return;

        const gates = await response.json();
        gateList.innerHTML = "";

        Object.entries(gates).forEach(([gate, status]) => {
            const li = document.createElement("li");

            const nameSpan = document.createElement("span");
            nameSpan.className = "gate-name";
            nameSpan.textContent = gate;

            const statusSpan = document.createElement("span");
            statusSpan.className = "gate-status " + statusToClass(status);
            statusSpan.textContent = status;

            li.appendChild(nameSpan);
            li.appendChild(statusSpan);
            gateList.appendChild(li);
        });
    } catch (error) {
        // Gate panel simply keeps its last known state on failure
    }
}

stadiumSelect.addEventListener("change", function () {
    refreshGates(stadiumSelect.value);
});

newChatBtn.addEventListener("click", async function () {
    try {
        await fetch("/api/reset", { method: "POST" });
    } catch (error) {
        // even if reset fails server-side, clear the visible chat
    }
    chatWindow.innerHTML = "";
    appendMessage("Hello. How can I help you today?", "bot");
});

chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    const preferredLanguage = langSelect.value;
    const stadiumId = stadiumSelect.value;

    appendMessage(message, "user");
    userInput.value = "";
    userInput.disabled = true;
    showTyping(true);

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message, language: preferredLanguage, stadium_id: stadiumId }),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            appendMessage(err.error || "Something went wrong. Please try again.", "bot");
            return;
        }

        const data = await response.json();
        appendMessage(data.reply, "bot");
    } catch (error) {
        appendMessage("Network error. Please check your connection.", "bot");
    } finally {
        showTyping(false);
        userInput.disabled = false;
        userInput.focus();
    }
});

// --- Voice input (Web Speech API) ---
// Gracefully degrades: button hides if the browser doesn't support it.
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    let listening = false;

    micBtn.addEventListener("click", function () {
        if (listening) {
            recognition.stop();
            return;
        }
        try {
            recognition.lang = "en-US";
            recognition.start();
        } catch (error) {
            // recognition may throw if already started; ignore
        }
    });

    recognition.addEventListener("start", function () {
        listening = true;
        micBtn.classList.add("listening");
    });

    recognition.addEventListener("end", function () {
        listening = false;
        micBtn.classList.remove("listening");
    });

    recognition.addEventListener("result", function (event) {
        const transcript = event.results[0][0].transcript;
        userInput.value = transcript;
        userInput.focus();
    });

    recognition.addEventListener("error", function () {
        listening = false;
        micBtn.classList.remove("listening");
    });
} else {
    micBtn.hidden = true;
}

initTheme();