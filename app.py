"""
Smart Fan Assistant - Flask application.
FIFA World Cup 2026 Smart Stadium Challenge (Challenge 4).
"""

import os
import logging
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from utils.genai_assistant import get_assistant_reply
from data.stadiums import get_stadium, get_all_stadiums_summary, DEFAULT_STADIUM_ID

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Security & config ---
app.secret_key = os.getenv("SECRET_KEY", os.urandom(24).hex())
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024  # 16 KB max request body
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
DEBUG_MODE = os.getenv("FLASK_ENV", "production") == "development"

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per hour"],
    storage_uri="memory://",
)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'"
    )
    response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
    return response


@app.route("/")
def index():
    stadium = get_stadium(DEFAULT_STADIUM_ID)
    stadiums = get_all_stadiums_summary()
    return render_template(
        "index.html",
        gates=stadium["gates"],
        stadiums=stadiums,
        current_stadium_id=DEFAULT_STADIUM_ID,
    )


@app.route("/api/stadiums", methods=["GET"])
def stadiums():
    return jsonify(get_all_stadiums_summary())


@app.route("/api/gates", methods=["GET"])
def gates():
    stadium_id = request.args.get("stadium_id", DEFAULT_STADIUM_ID)
    stadium = get_stadium(stadium_id)

    if stadium is None:
        return jsonify({"error": "Unknown stadium_id"}), 404

    return jsonify(stadium["gates"])


@app.route("/api/chat", methods=["POST"])
@limiter.limit("15 per minute")
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    language = data.get("language", "English")
    stadium_id = data.get("stadium_id", DEFAULT_STADIUM_ID)

    if not isinstance(message, str) or len(message.strip()) == 0:
        return jsonify({"error": "Message cannot be empty"}), 400

    if len(message) > 500:
        return jsonify({"error": "Message too long"}), 400

    if not isinstance(language, str) or len(language) > 30:
        language = "English"

    stadium = get_stadium(stadium_id) or get_stadium(DEFAULT_STADIUM_ID)

    history = session.get("history", [])

    try:
        reply = get_assistant_reply(message, language, stadium, history)
    except Exception:
        logger.exception("Failed to get assistant reply")
        return jsonify({"error": "Something went wrong. Please try again."}), 500

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    session["history"] = history[-10:]  # keep last 10 turns to bound session size

    return jsonify({"reply": reply})


@app.route("/api/reset", methods=["POST"])
def reset_conversation():
    session.pop("history", None)
    return jsonify({"status": "reset"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(429)
def rate_limit_exceeded(e):
    return jsonify({"error": "Too many requests. Please slow down."}), 429


@app.errorhandler(500)
def server_error(e):
    logger.exception("Internal server error")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(debug=DEBUG_MODE)