"""Scoped deterministic topic shortening; internal sanitizer seam only."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MAX_CHARS = 24
MAX_WORDS = 4

STOPWORDS = {
    "le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "dans", "pour", "et", "à", "au",
    "aux", "en", "sur", "via", "par", "avec", "mon", "ma", "mes", "ton", "ta", "tes", "son", "sa",
    "ses", "ce", "cet", "cette", "que", "qui", "est", "plus", "ou", "on", "il", "elle",
}

_PROMPT_MARKER = "- 3 to 7 words, sentence case"
_PROMPT_REPLACEMENT = "- 3 to 4 words (24 characters maximum), sentence case"


def shorten(title: str) -> str:
    """Titre tronqué au début signifiant : ≤ 4 mots et ≤ 24 caractères, sans mot vide final."""
    text = " ".join(str(title or "").split())
    if not text:
        return ""
    if len(text) <= MAX_CHARS and len(text.split()) <= MAX_WORDS:
        return text
    words = text.split()
    kept: list[str] = []
    for word in words:
        if len(kept) >= MAX_WORDS:
            break
        candidate = " ".join(kept + [word])
        if kept and len(candidate) > MAX_CHARS:
            break
        kept.append(word)
    while kept and kept[-1].strip(".,;:!?()[]").lower() in STOPWORDS:
        kept.pop()
    return (" ".join(kept) or words[0])[:MAX_CHARS]


def _settings(ctx):
    users = ctx.get_config("allowed_users", [])
    chats = ctx.get_config("allowed_chats", [])
    if ctx.get_config("opt_in", False) is not True:
        return None
    if not isinstance(users, list) or not isinstance(chats, list) or not users or not chats:
        return None
    if any(not str(v).lstrip("-").isdigit() for v in users + chats):
        return None
    return {str(v) for v in users}, {str(v) for v in chats}

def register(ctx):
    allowed = _settings(ctx)
    if allowed is None: return
    from gateway.run_topics import GatewayTopicThreadsMixin
    from gateway.session_context import get_session_env
    current = GatewayTopicThreadsMixin._sanitize_telegram_topic_title
    original = getattr(current, "_portable_original", current)
    def patched(self, title):
        cleaned = original(self, title)
        users, chats = allowed
        if (get_session_env("HERMES_SESSION_PLATFORM") == "telegram"
            and str(get_session_env("HERMES_SESSION_USER_ID")) in users
            and str(get_session_env("HERMES_SESSION_CHAT_ID")) in chats):
            return shorten(cleaned) or cleaned
        return cleaned
    patched._portable_original = original
    GatewayTopicThreadsMixin._sanitize_telegram_topic_title = patched
    def unload():
        if GatewayTopicThreadsMixin._sanitize_telegram_topic_title is patched:
            GatewayTopicThreadsMixin._sanitize_telegram_topic_title = original
    ctx.on_unload(unload)
