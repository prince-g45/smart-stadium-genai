"""
GenAI Assistant module for Smart Stadium Fan Assistant.
Uses Anthropic's Claude API when an API key is available.
Falls back to rule-based responses when no key is configured,
so the app remains fully functional for demos/testing.
"""

import os
import re
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = "claude-sonnet-4-6"
MAX_HISTORY_TURNS = 10  # matches app.py session cap

_client = None
if ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your_api_key_here":
    _client = Anthropic(api_key=ANTHROPIC_API_KEY)


def _build_system_prompt(stadium: dict | None) -> str:
    stadium_name = stadium["name"] if stadium else "the stadium"
    stadium_city = stadium["city"] if stadium else ""
    gates_list = ", ".join(stadium["gates"].keys()) if stadium else "the available gates"

    return (
        f"You are 'Stadium Assistant', a helpful multilingual assistant for fans "
        f"at {stadium_name} ({stadium_city}) during the FIFA World Cup 2026. "
        f"This stadium's gates are: {gates_list}. "
        "Answer questions about navigation, seating, restrooms, food stalls, "
        "medical points, accessibility (wheelchair access, assistance points), "
        "transportation, and crowd guidance. Use the conversation history to "
        "understand follow-up questions. Keep answers short, clear, and friendly. "
        "If the user writes in a language other than English, reply in that "
        "same language."
    )


def _rule_based_reply(message: str, stadium: dict | None) -> str:
    """Simple keyword-based fallback so the app works without an API key."""
    text = message.lower()
    gates = list(stadium["gates"].items()) if stadium else []

    quietest_gate = None
    if gates:
        priority = {"Low crowd": 0, "Moderate crowd": 1, "High crowd": 2}
        quietest_gate = min(gates, key=lambda g: priority.get(g[1], 1))[0]

    rules = [
        (r"\b(gate|entry|entrance)\b",
         f"The quietest gate right now is {quietest_gate}. I'd recommend using that one."
         if quietest_gate else "Please check the gate status panel for current crowd levels."),
        (r"\b(washroom|toilet|restroom|bathroom)\b", "Restrooms are located "
         "near every gate and on each concourse level, marked with blue signs."),
        (r"\b(food|snack|eat|restaurant)\b", "Food stalls are available on "
         "the main concourse, close to the entry gates."),
        (r"\b(medical|doctor|first aid|emergency)\b", "Medical assistance "
         "points are located near the main gates — look for the red cross sign, "
         "or ask any steward nearby for immediate help."),
        (r"\b(wheelchair|accessib|disab)\b", "Accessible seating and ramps "
         "are available near the main gates, with dedicated assistance staff on site."),
        (r"\b(parking|transport|bus|metro|taxi)\b", "Shuttle buses and metro "
         "access points are located near the main plaza, a short walk from the gates."),
        (r"\b(crowd|busy|rush|line|queue)\b",
         f"{quietest_gate} currently has the shortest wait time."
         if quietest_gate else "Please check the gate status panel for live crowd levels."),
    ]

    for pattern, reply in rules:
        if re.search(pattern, text):
            return reply

    return ("I'm here to help with navigation, food, restrooms, medical "
            "assistance, accessibility, and transport info at the stadium. "
            "Could you tell me a bit more about what you need?")


def get_assistant_reply(
    message: str,
    language: str = "English",
    stadium: dict | None = None,
    history: list[dict] | None = None,
) -> str:
    """
    Returns a reply for the given fan message, in the requested language,
    aware of the selected stadium and recent conversation history.
    Uses Claude API if configured, otherwise falls back to rule-based logic
    (fallback replies stay in English, since keyword rules aren't translated).
    """
    if not message or not message.strip():
        return "Please type your question so I can help you."

    if _client is None:
        logger.warning("No Anthropic client configured - using fallback replies.")
        return _rule_based_reply(message, stadium)

    history = history or []
    messages = list(history[-(MAX_HISTORY_TURNS * 2):])
    messages.append({
        "role": "user",
        "content": f"[Reply in {language}] {message}",
    })

    try:
        response = _client.messages.create(
            model=MODEL_NAME,
            max_tokens=300,
            system=_build_system_prompt(stadium),
            messages=messages,
        )
        return response.content[0].text.strip()
    except Exception:
        logger.exception("Claude API call failed - falling back to rule-based reply.")
        return _rule_based_reply(message, stadium)