"""Opt-in Telegram catalog. Installation remains in the native interactive CLI."""
import asyncio
import secrets
import time

CATALOG = {
    'session-context-recovery': 'Retrouver un contexte antérieur sans deviner le référent ni exposer un historique brut.',
    'usage-cost-audit': 'Auditer les coûts et la consommation Hermes à partir de preuves locales.',
    'runtime-config-audit': 'Vérifier la configuration effective sans révéler les secrets ni modifier le profil.',
    'scheduled-task-watchdog': 'Contrôler ponctuellement un export de tâches planifiées ; aucun cron automatique.',
    'backup-and-recovery': 'Sauvegarder une sélection approuvée et vérifier une restauration temporaire ; archives non chiffrées.',
}

def state(name):
    if name not in CATALOG:
        raise ValueError('Unknown catalog skill')
    from tools.skills_tool import _find_all_skills
    from hermes_cli.config import load_config_readonly
    from hermes_cli.skills_config import get_disabled_skills
    installed = any(s['name'] == name for s in _find_all_skills(skip_disabled=True))
    cfg = load_config_readonly()
    return {'installed': installed, 'enabled': installed and name not in get_disabled_skills(cfg, 'telegram'),
            'global_disabled': name in get_disabled_skills(cfg)}


def toggle(name, enabled):
    from hermes_cli.config import load_config, load_config_readonly
    from hermes_cli.skills_config import get_disabled_skills, save_disabled_skills
    status = state(name)
    if not status['installed']:
        raise ValueError('Skill absent : installer via le terminal natif.')
    if enabled and status['global_disabled']:
        raise ValueError('Désactivation globale : modifier la portée globale via hermes skills au terminal.')
    cfg = load_config()
    disabled = set((cfg.get('skills') or {}).get('platform_disabled', {}).get('telegram') or [])
    if enabled:
        disabled.discard(name)
    else:
        disabled.add(name)
    save_disabled_skills(cfg, disabled, platform='telegram')
    if (name not in get_disabled_skills(load_config_readonly(), 'telegram')) != enabled:
        raise RuntimeError('Configuration non confirmée')
    return 'Chargement Telegram ' + ('activé' if enabled else 'désactivé') + '. Nouvelle session recommandée ; aucun fichier supprimé.'


class Tickets:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.entries = {}

    def issue(self, owner, message_id):
        now = self.clock()
        self.entries = {k: v for k, v in self.entries.items() if now - v[2] < 600}
        if len(self.entries) >= 512:
            self.entries.clear()
        token = secrets.token_hex(8)
        self.entries[token] = (owner, message_id, now)
        return token

    def valid(self, token, owner, message_id):
        entry = self.entries.get(token)
        return bool(entry and entry[0] == owner and entry[1] == message_id and self.clock() - entry[2] < 600)


def register(ctx):
    users = ctx.get_config('allowed_users', [])
    chats = ctx.get_config('allowed_chats', [])
    if ctx.get_config('opt_in', False) is not True:
        return
    if not isinstance(users, list) or not isinstance(chats, list) or not users or not chats:
        return
    if any(isinstance(v, bool) or not str(v).lstrip('-').isdigit() for v in users + chats):
        return
    users, chats = set(map(str, users)), set(map(str, chats))
    live = [True]
    ctx.on_unload(lambda: live.__setitem__(0, False))

    def telegram_catalog(application, adapter):
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import CommandHandler, CallbackQueryHandler, ApplicationHandlerStop
        tickets = Tickets()
        lock = asyncio.Lock()

        async def owner(update):
            message = update.effective_message
            user = update.effective_user
            if not live[0] or message is None or user is None:
                return None
            current_users = ctx.get_config('allowed_users', [])
            current_chats = ctx.get_config('allowed_chats', [])
            if ctx.get_config('opt_in', False) is not True or not isinstance(current_users, list) or not isinstance(current_chats, list):
                return None
            if any(isinstance(v, bool) or not str(v).lstrip('-').isdigit() for v in current_users + current_chats):
                return None
            if str(user.id) not in set(map(str, current_users)) or str(message.chat_id) not in set(map(str, current_chats)):
                return None
            # Callback messages belong to the bot; authorize the clicking user, not its author.
            if update.callback_query is None and not adapter._is_user_authorized_from_message(message):
                return None
            from gateway.run import _gateway_runner_ref
            from gateway.platforms.base import MessageType
            runner = _gateway_runner_ref()
            if runner is None:
                return None
            event = adapter._build_message_event(message, MessageType.TEXT)
            if update.callback_query is not None and not adapter._is_callback_user_authorized(
                str(user.id), chat_id=str(message.chat_id), chat_type=event.source.chat_type,
                thread_id=event.source.thread_id, user_name=getattr(user, 'full_name', None)):
                return None
            event.source.user_id = str(user.id)
            event.source.is_bot = bool(getattr(user, 'is_bot', False))
            entry = await runner.async_session_store.get_or_create_session(event.source)
            return (str(user.id), str(message.chat_id), str(message.message_thread_id or ''), str(entry.session_id))

        def keyboard(token, name=None):
            def button(label, action, index):
                return InlineKeyboardButton(label, callback_data=f'tkc:{token}:{action}:{index}')
            if name is None:
                return InlineKeyboardMarkup([[button(n, 'detail', i)] for i, n in enumerate(CATALOG)])
            i = list(CATALOG).index(name)
            status = state(name)
            rows = [[button('Actualiser', 'detail', i)], [button('Catalogue', 'list', 0)]]
            if status['installed']:
                rows.insert(0, [button('Désactiver Telegram' if status['enabled'] else 'Activer Telegram',
                                       'disable' if status['enabled'] else 'enable', i)])
            else:
                rows.insert(0, [button('Installer : procédure native', 'install', i)])
            return InlineKeyboardMarkup(rows)

        async def command(update, context):
            bound = await owner(update)
            if bound is not None:
                sent = await update.effective_message.reply_text('Toolkit : sélectionner un skill. Réglages pour tout Telegram du profil, pas seulement ce chat.')
                token = tickets.issue(bound, sent.message_id)
                await sent.edit_reply_markup(reply_markup=keyboard(token))
            raise ApplicationHandlerStop

        async def callback(update, context):
            query = update.callback_query
            try:
                async with lock:
                    bound = await owner(update)
                    parts = (query.data or '').split(':')
                    if len(parts) != 4 or bound is None or not tickets.valid(parts[1], bound, query.message.message_id):
                        await query.answer('Carte expirée ou accès refusé. Relancer /toolkit.', show_alert=True)
                        raise ApplicationHandlerStop
                    _, token, action, index = parts
                    if not index.isdigit() or int(index) >= len(CATALOG):
                        raise ValueError('Action invalide')
                    name = list(CATALOG)[int(index)]
                    await query.answer()
                    if action == 'list':
                        text, markup = 'Toolkit : sélectionner un skill.', keyboard(token)
                    elif action in ('detail', 'install', 'enable', 'disable'):
                        result = toggle(name, action == 'enable') if action in ('enable', 'disable') else ''
                        status = state(name)
                        text = name + '\n' + CATALOG[name] + '\n' + ('Installé (nom détecté, provenance non garantie)' if status['installed'] else 'Non installé')
                        text += '\nChargement Telegram : ' + ('actif' if status['enabled'] else 'inactif')
                        text += '\nPortée : tout Telegram du profil.\n' + result
                        if action == 'install':
                            text += '\n' + install_instructions(name)
                        markup = keyboard(token, name)
                    else:
                        raise ValueError('Action inconnue')
                    await query.edit_message_text(text, reply_markup=markup)
            except ApplicationHandlerStop:
                raise
            except Exception as exc:
                await query.answer('Opération refusée ou indisponible : ' + (str(exc) if isinstance(exc, ValueError) else type(exc).__name__)[:150], show_alert=True)
            raise ApplicationHandlerStop

        for old in list(application.handlers.get(-20, [])):
            if getattr(getattr(old, 'callback', None), '_toolkit_catalog_owned', False):
                application.remove_handler(old, group=-20)
        command._toolkit_catalog_owned = True
        callback._toolkit_catalog_owned = True
        application.add_handler(CommandHandler('toolkit', command), group=-20)
        application.add_handler(CallbackQueryHandler(callback, pattern=r'^tkc:'), group=-20)

    # SDK deduplicates factories by qualname. A new generation replaces only our own
    # PTB handlers, while unload immediately makes the previous generation inert.
    telegram_catalog.__qualname__ += '_' + secrets.token_hex(8)
    ctx.register_telegram_handler(telegram_catalog)


def install_instructions(name):
    if name not in CATALOG:
        raise ValueError('Unknown catalog skill')
    identifier = 'thomashuangth/hermes-toolkit/skills/' + name
    return ('Installation NON effectuée. Dans un terminal interactif du même profil Hermes :\n'
            'hermes skills inspect ' + identifier + '\n'
            'hermes skills install ' + identifier + '\n'
            'Lire le rapport du scanner natif puis accepter ou refuser sa confirmation. '
            'Aucun contournement des alertes. Une collision locale doit être examinée, pas écrasée. '
            'Revenir à /toolkit après installation.')
