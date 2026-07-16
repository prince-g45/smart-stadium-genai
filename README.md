# Stadium Assistant — Smart Fan Assistant for FIFA World Cup 2026

**Challenge 4: Smart Stadiums & Tournament Operations**

A multilingual, GenAI-powered fan assistant that helps fans navigate stadiums, avoid crowded gates, find accessibility support, and get real-time answers — across multiple FIFA World Cup 2026 host venues.

---

## 1. Chosen Vertical

**Navigation, Crowd Management, Accessibility & Multilingual Assistance** for fans across multiple tournament venues.

Rather than solving one narrow problem, this addresses the core operational pain points fans face on match day: *"Which gate should I use?", "Where's the nearest medical point?", "Is there wheelchair access?", "How do I get here on public transport?"* — in whichever language the fan speaks, at whichever host stadium they're attending.

## 2. Problem Statement Alignment

| Challenge requirement | How this solution addresses it |
|---|---|
| Navigation | Live gate list per stadium; assistant recommends specific gates by name |
| Crowd management | Per-gate crowd levels drive both the visual dashboard and the assistant's gate recommendations |
| Accessibility | Dedicated accessibility Q&A; ARIA-compliant UI; voice input for fans who prefer speaking |
| Transportation | Assistant answers transport/parking questions per venue |
| Multilingual assistance | Fan-selectable language; GenAI replies in that language |
| Real-time decision support | Live gate-status API + conversation memory for contextual follow-ups |
| Mandatory GenAI use | Claude (Anthropic API) powers all conversational responses, with context-aware system prompts per stadium |

## 3. Architecture & Approach

```
Browser (HTML/CSS/JS)
   │  fetch()
   ▼
Flask app (app.py)
   │  validates input, applies rate limiting & security headers
   ▼
utils/genai_assistant.py ──► Anthropic Claude API (GenAI reply)
   │                              │
   │                       (on failure/no key)
   ▼                              ▼
data/stadiums.py            Rule-based fallback
(venue + gate data)         (same stadium data, keyword matching)
```

- **Flask backend** exposes REST endpoints consumed by a vanilla JS frontend — no heavy framework, keeping the codebase small, auditable, and fast to load (important for stadium wifi conditions).
- **`data/stadiums.py`** is a structured dataset of FIFA World Cup 2026 host venues and their gates, used both by the API and by the GenAI system prompt — so the assistant always answers with the *actual* gate names for the *selected* stadium, not generic placeholders.
- **`utils/genai_assistant.py`** builds a stadium-specific system prompt, forwards recent conversation history to Claude for multi-turn context, and — critically — never lets a GenAI failure become a fan-facing failure: any exception falls back to rule-based logic using the same real gate data.
- **Session-based conversation memory** (capped at 10 turns) lets the assistant handle natural follow-ups without the fan repeating context.

## 4. How the Solution Works (Fan Flow)

1. Fan opens the page → sees the selected stadium's live gate status.
2. Fan can switch stadiums from a dropdown → gate list updates instantly via `/api/gates`.
3. Fan types or speaks a question (voice input via the browser's Web Speech API).
4. Frontend sends `{message, language, stadium_id}` to `/api/chat`.
5. Backend validates the request, loads recent session history, and asks Claude for a reply — grounded in the selected stadium's real data and the conversation so far.
6. If Claude is unavailable, the same request is answered by a rule-based engine using identical venue data, so the fan never sees a broken experience.
7. "New chat" clears both the visible conversation and server-side session history.

## 5. Tech Stack

- **Backend:** Python 3.11, Flask, Flask-Limiter
- **GenAI:** Anthropic API (Claude)
- **Frontend:** HTML, CSS, vanilla JavaScript (no build step, no framework)
- **Accessibility:** ARIA roles/labels, semantic HTML, browser Web Speech API for voice input
- **Testing:** Pytest (16 automated tests)

## 6. Security

| Measure | Implementation |
|---|---|
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`, `Referrer-Policy` on every response |
| Rate limiting | 15 requests/minute per IP on `/api/chat` via Flask-Limiter |
| Payload limits | Request body capped at 16 KB; message length capped at 500 characters |
| Input validation | Type and length checks on `message`, `language`, and `stadium_id` before any processing |
| Secret management | `ANTHROPIC_API_KEY` and `SECRET_KEY` loaded from `.env`, excluded from version control via `.gitignore` — never hardcoded |
| Session safety | `HttpOnly` and `SameSite=Lax` cookies; history capped at 10 turns to bound session size |
| Error handling | All exceptions caught and logged server-side; only generic error messages reach the client — no stack traces or internals exposed |
| Debug mode | Controlled by `FLASK_ENV`; off by default (production-safe) |

## 7. Efficiency

- Stateless per-request logic with a lightweight session (no external database required for the prototype), keeping response times low.
- Gate/stadium data is static in-memory lookups (`O(1)` dict access) rather than repeated computation or disk reads.
- Conversation history is capped, bounding both memory use and the token size of each Claude API call.
- Frontend is dependency-free vanilla JS/CSS — no bundler, no framework overhead, fast first load.

## 8. Testing

16 automated pytest tests cover:
- Page rendering and security headers
- Multi-stadium gate endpoints (valid, specific, and unknown stadium IDs)
- Chat endpoint validation (empty, missing, oversized, and invalid-language input)
- Rule-based fallback correctness (gate and medical keyword responses)
- Session reset behavior
- 404 error handling

Run with:
```bash
python -m pytest -v
```

## 9. Accessibility

- Semantic HTML with ARIA roles (`role="log"`, `aria-live="polite"` on the chat window so screen readers announce new replies)
- Visually-hidden labels for all form controls
- High-contrast dark and light themes, switchable via a header toggle (preference persisted in the browser)
- Voice input as an alternative to typing, with automatic graceful degradation in unsupported browsers

## 10. Assumptions

- Gate crowd data is simulated (in-memory) per stadium for this prototype; a real deployment would connect to live turnstile/camera sensor feeds per venue.
- Conversation history uses Flask's signed session cookie for simplicity; a production system serving many concurrent fans would likely move this to a server-side store (e.g. Redis) keyed by session ID.
- A single Anthropic API key serves all users; per-user authentication was out of scope for this challenge.
- The assistant is deliberately scoped to stadium-operations Q&A rather than open-domain chat.
- If `ANTHROPIC_API_KEY` has no active credits or the API is temporarily unreachable, the app is *designed* to fall back gracefully rather than fail — this is intentional resilience, not a defect.

## 11. Setup & Running Locally

```bash
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
python -m pip install -r requirements.txt
```

Create a `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
FLASK_ENV=development
SECRET_KEY=a-random-secret-string
```

Run:
```bash
python app.py
```
Visit `http://127.0.0.1:5000`

## 12. Project Structure

```
smart-stadium-genai/
├── app.py                    # Flask routes, security, session handling
├── data/
│   ├── stadiums.py           # Multi-venue stadium & gate dataset
│   └── __init__.py
├── utils/
│   └── genai_assistant.py    # Claude integration + rule-based fallback
├── templates/
│   └── index.html
├── static/
│   ├── css/style.css
│   └── js/script.js
├── test_app.py                # 16 pytest tests
├── requirements.txt
├── .env                        # not committed (see .gitignore)
└── README.md
```