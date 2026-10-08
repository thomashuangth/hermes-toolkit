"""Experimental pure footer formatting. No gateway or pin installation."""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

NATIVE_FIELDS = ("model", "served_model", "context_pct", "latency", "cwd")
EXTRA_FIELDS = ("effort", "ctx", "quota")
_SEP = " · "
FORMAT_VERSION = "compact-mono-v2"

def format_bar(percent: int) -> str:
    """Five segments, nearest 20%, with half segments rounded up."""
    filled = max(0, min(5, (int(percent) + 10) // 20))
    return "▰" * filled + "▱" * (5 - filled)

# Au-delà de FRESH_SECONDS le cache porte un « ~ » ; au-delà de MAX_AGE_SECONDS le champ disparaît.
FRESH_SECONDS = 30 * 60
MAX_AGE_SECONDS = 6 * 3600
CACHE_NAME = "provider_usage_cache.json"

# Le relevé ne vaut que pour le fournisseur qu'il a interrogé : un tour servi par un autre
# fournisseur ne doit pas afficher ces pourcentages-là (nom de provider → alias acceptés).
_PROVIDER_ALIASES = {"codex": "openai-codex", "chatgpt": "openai-codex", "openai": "openai-codex"}


def _same_provider(turn_provider: Any, cache_provider: Any) -> bool:
    """True quand le tour et le relevé désignent le même fournisseur (ou qu'on ne peut pas trancher)."""
    left = str(turn_provider or "").strip().lower()
    right = str(cache_provider or "").strip().lower()
    if not left or not right:
        return False
    return _PROVIDER_ALIASES.get(left, left) == _PROVIDER_ALIASES.get(right, right)


def _hermes_home() -> Path:
    from hermes_constants import get_hermes_home
    return get_hermes_home()


def _paris_tz():
    try:
        from zoneinfo import ZoneInfo

        return ZoneInfo("Europe/Paris")
    except Exception:  # pas de base tzdata : heure d'été fixe, jamais d'exception
        return timezone(timedelta(hours=2))


def load_quota_cache(path: Optional[Path] = None) -> Optional[dict]:
    """Cache local facultatif. None si illisible."""
    target = path or (_hermes_home() / "state" / CACHE_NAME)
    try:
        with open(target, encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _remaining(window: Any) -> Optional[int]:
    if not isinstance(window, dict):
        return None
    used = window.get("used_percent")
    if not isinstance(used, (int, float)):
        return None
    return max(0, min(100, int(round(100 - float(used)))))


def _reset_label(raw: Any, *, with_date: bool) -> str:
    if not raw:
        return ""
    try:
        moment = datetime.fromisoformat(str(raw))
    except Exception:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    local = moment.astimezone(_paris_tz())
    return local.strftime("%d/%m %H:%M") if with_date else local.strftime("%H:%M")


def format_quota(cache: Optional[dict], *, now: Optional[float] = None, provider: Any = None) -> str:
    """`5h ▰▰▱▱▱ 36% 04:30 · 7j ▰▰▰▱▱ 60% 14/10 09:08`, « ~ » si le relevé a plus de 30 min, "" si illisible,
    périmé, ou relevé pour un autre fournisseur que celui du tour."""
    if not isinstance(cache, dict):
        return ""
    if not _same_provider(provider, cache.get("provider")):
        return ""
    fetched = cache.get("fetched_at")
    if not isinstance(fetched, (int, float)):
        return ""
    age = (now if now is not None else time.time()) - float(fetched)
    if age > MAX_AGE_SECONDS or age < -60:
        return ""
    windows = cache.get("windows") or {}
    if not isinstance(windows, dict):
        return ""
    session = windows.get("session")
    weekly = windows.get("weekly")
    parts: list[str] = []
    session_left = _remaining(session)
    if session_left is not None:
        reset = _reset_label((session or {}).get("resets_at"), with_date=False)
        parts.append(f"5h {format_bar(session_left)} {session_left}%" + (f" {reset}" if reset else ""))
    weekly_left = _remaining(weekly)
    if weekly_left is not None:
        reset = _reset_label((weekly or {}).get("resets_at"), with_date=True)
        parts.append(f"7j {format_bar(weekly_left)} {weekly_left}%" + (f" {reset}" if reset else ""))
    if not parts:
        return ""
    return _SEP.join(("~" if age > FRESH_SECONDS else "") + part for part in parts)


def format_effort(reasoning_config: Any) -> str:
    """Effort effectif : « none », le niveau réglé, ou « défaut » quand rien n'est configuré."""
    if reasoning_config is None:
        return "défaut"
    if not isinstance(reasoning_config, dict):
        return ""
    if reasoning_config.get("enabled") is False:
        return "none"
    effort = str(reasoning_config.get("effort") or "").strip()
    return effort or "défaut"


def format_ctx(context_tokens: Any, context_length: Any) -> str:
    """`ctx 42%` ; "" quand la fenêtre n'est pas connue (jamais de pourcentage inventé)."""
    try:
        length = int(context_length or 0)
        tokens = int(context_tokens or 0)
    except (TypeError, ValueError):
        return ""
    if length <= 0 or tokens < 0:
        return ""
    percent = max(0, min(100, round(tokens / length * 100)))
    return f"ctx {percent}%"


def compose_line(
    *, fields: Any, native_render, effort_report: Any, context_tokens: Any,
    context_length: Any, quota_cache: Optional[dict], now: Optional[float] = None,
    quota_provider: Any = None,
) -> str:
    """Assemble la ligne dans l'ordre de `fields` : champs natifs délégués, champs ajoutés ici."""
    renderers = {
        "effort": lambda: format_effort(effort_report),
        "ctx": lambda: format_ctx(context_tokens, context_length),
        "quota": lambda: format_quota(quota_cache, now=now, provider=quota_provider),
    }
    parts: list[str] = []
    header: list[str] = []
    has_extras = any(f in EXTRA_FIELDS for f in (fields or ()))
    def flush_header():
        if header:
            parts.insert(0, _SEP.join(header))
            header.clear()
    for field in list(fields or ()):
        name = str(field)
        render = renderers.get(name)
        if render is not None:
            value = render()
        elif name in NATIVE_FIELDS:
            value = native_render(name)
        else:
            continue
        if value:
            if has_extras and name == "quota":
                parts.append(str(value))
            else:
                header.append(str(value))
    flush_header()
    if not has_extras:
        return _SEP.join(parts)
    # Each logical line is an inline-code span supported by Telegram MarkdownV2.
    # Dynamic native fields may contain backticks: replace only that delimiter.
    return "\n".join("`" + part.replace("`", "ˋ") + "`" for part in parts)


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
    # Formatting module only: the private pin implementation is not portable.
    return
