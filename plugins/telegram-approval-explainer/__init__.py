"""Display-only native Telegram approval explanation. No approval-state mutations."""
import html
import json
import os
from functools import wraps

VERSION = 'fr-native-v1'


def render(adapter, command, description, smart_denied, actions):
    from gateway.platforms.base_exec_approval import approval_timeout_seconds
    from agent.redact import redact_sensitive_text
    command = redact_sensitive_text(str(command or ''), force=True)
    reason = redact_sensitive_text(str(description or ''), force=True)
    reason = adapter._ea_fit(reason, 850)
    # The native pipeline carries detector findings, NOT the terminal tool's purpose.
    purpose = 'Exécuter la commande ci-dessous. Le but métier n’est pas transmis par cette demande ; je ne peux pas le confirmer.'
    risks = 'Les effets exacts dépendent de la commande et de son environnement ; ils ne sont pas vérifiés ici.'
    lowered = command.lower()
    if 'rm ' in lowered or 'remove-item' in lowered:
        risks = 'Suppression possible de fichiers ou dossiers ciblés, potentiellement irréversible.'
    elif 'git reset' in lowered or 'git clean' in lowered:
        risks = 'Perte possible de modifications locales ou de fichiers non suivis dans le dépôt ciblé.'
    elif 'systemctl' in lowered or 'reboot' in lowered or 'shutdown' in lowered:
        risks = 'Interruption possible du service ou de la machine ciblée.'
    elif 'curl ' in lowered or 'wget ' in lowered:
        risks = 'Accès réseau ; données transmises ou code téléchargé selon les options de la commande.'
    body = ('<b>But</b>\n' + html.escape(purpose)
            + '\n\n<b>Pourquoi ton accord</b>\nLe contrôle de sécurité exige une décision humaine. Signal transmis : '
            + html.escape(reason or 'aucun détail disponible.')
            + '\n\n<b>Risques</b>\n' + html.escape(risks)
            + '\n\n<b>Portée</b>\nLa commande peut agir sur toutes les cibles et permissions accessibles à son environnement shell, pas seulement le dossier courant.')
    choices = {a[1] for a in actions}
    if 'session' in choices:
        body += '\nSession : autorise les commandes reconnues par les mêmes règles de détection pendant cette session.'
    if 'always' in choices:
        body += '\nToujours : mémorise ces règles dans le profil actif pour les prochaines sessions ; ce n’est PAS une correspondance exacte de la commande. D’autres commandes couvertes peuvent passer sans nouvelle demande.'
    if smart_denied:
        body += '\n\n<b>Le contrôle automatique a refusé : autorisation exceptionnelle pour cette opération uniquement.</b>'
    body += f'\n\nSans réponse sous {approval_timeout_seconds()} secondes : la commande ne sera pas exécutée.'
    framing = '⚠️ <b>Accord requis</b>\n\n<pre></pre>\n\n' + body
    budget = max(0, adapter.MAX_MESSAGE_LENGTH - adapter.message_len_fn(framing) - 8)
    preview = adapter._ea_fit(command, budget)
    return '⚠️ <b>Accord requis</b>\n\n<pre>' + html.escape(preview) + '</pre>\n\n' + body


def register(ctx):
    allowed = _settings(ctx)
    if allowed is None: return
    from plugins.platforms.telegram.adapter import TelegramAdapter
    from hermes_constants import get_hermes_home
    original = TelegramAdapter.send_exec_approval
    original = getattr(original, '_fr_approval_original', original)

    @wraps(original)
    async def wrapped(self, chat_id, command, session_key, description=None, metadata=None,
                      allow_permanent=True, allow_session=True, smart_denied=False):
        from gateway.session_context import get_session_env
        if (str(chat_id) not in allowed[1]
            or str(get_session_env("HERMES_SESSION_USER_ID")) not in allowed[0]):
            return await original(self, chat_id, command, session_key, description, metadata,
                                  allow_permanent, allow_session, smart_denied)
        from gateway.platforms.base import ExecApprovalPrompt
        actions = self._exec_approval_actions(allow_permanent=allow_permanent,
                                             allow_session=allow_session, smart_denied=smart_denied)
        prompt = ExecApprovalPrompt(chat_id=chat_id, session_key=session_key, metadata=metadata,
                                    command=str(command or ''), description=description,
                                    smart_denied=smart_denied, actions=actions,
                                    text=render(self, command, description, smart_denied, actions))
        return await self._send_exec_approval_prompt(prompt)

    wrapped._fr_approval_original = original
    TelegramAdapter.send_exec_approval = wrapped
    def unload():
        if TelegramAdapter.send_exec_approval is wrapped:
            TelegramAdapter.send_exec_approval = original
    ctx.on_unload(unload)

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

