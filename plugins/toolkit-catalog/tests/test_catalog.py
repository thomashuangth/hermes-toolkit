import importlib.util
from pathlib import Path
import unittest
import os

def setUpModule():
    home = os.environ.get('HERMES_HOME')
    if not home or home != os.environ.get('HERMES_TOOLKIT_TEST_HOME'):
        raise RuntimeError('Run via plugins/run_tests.py: an isolated test home is required before Hermes imports')

class RuntimeButtons(unittest.IsolatedAsyncioTestCase):
    async def test_command_detail_install_toggle_and_ownership(self):
        from unittest.mock import Mock, AsyncMock, patch
        from types import SimpleNamespace as NS
        from telegram.ext import ApplicationHandlerStop
        from hermes_constants import get_hermes_home
        from hermes_cli.config import load_config, save_config
        mod = module()
        target = get_hermes_home() / 'skills' / 'usage-cost-audit'
        target.mkdir(parents=True, exist_ok=True)
        (target / 'SKILL.md').write_text('---\nname: usage-cost-audit\ndescription: test\n---\nTest\n')
        cfg = load_config(); cfg['skills'] = {}; save_config(cfg)
        ctx = Mock(); settings = {'opt_in': True, 'allowed_users': ['101'], 'allowed_chats': ['202']}
        ctx.get_config.side_effect = lambda k, d=None: settings.get(k, d)
        mod.register(ctx)
        app = Mock(); app.handlers = {}; handlers = []
        app.add_handler.side_effect = lambda h, group: handlers.append(h)
        adapter = Mock(); adapter._is_user_authorized_from_message.return_value = True
        adapter._build_message_event.side_effect = lambda *a: NS(source=NS(user_id='101', chat_type='dm', thread_id='5'))
        ctx.register_telegram_handler.call_args.args[0](app, adapter)
        sent = NS(message_id=42, edit_reply_markup=AsyncMock())
        msg = NS(chat_id=202, message_thread_id=5, message_id=42, reply_text=AsyncMock(return_value=sent))
        update = NS(effective_message=msg, effective_user=NS(id=101), callback_query=None)
        store = NS(get_or_create_session=AsyncMock(return_value=NS(session_id='session-a')))
        runner = NS(async_session_store=store)
        with patch('gateway.run._gateway_runner_ref', return_value=runner):
            with self.assertRaises(ApplicationHandlerStop): await handlers[0].callback(update, None)
            markup = sent.edit_reply_markup.call_args.kwargs['reply_markup']
            self.assertEqual(len(markup.inline_keyboard), 5)
            data = markup.inline_keyboard[1][0].callback_data
            query = NS(data=data, message=msg, answer=AsyncMock(), edit_message_text=AsyncMock())
            update.callback_query = query
            async def click(action, index=1):
                query.data = ':'.join(data.split(':')[:2] + [action, str(index)])
                with self.assertRaises(ApplicationHandlerStop): await handlers[1].callback(update, None)
            await click('detail')
            self.assertIn('Installé', query.edit_message_text.call_args.args[0])
            await click('disable'); self.assertFalse(mod.state('usage-cost-audit')['enabled'])
            await click('enable'); self.assertTrue(mod.state('usage-cost-audit')['enabled'])
            await click('install', 4)
            self.assertIn('Installation NON effectuée', query.edit_message_text.call_args.args[0])
            before = query.edit_message_text.call_count
            update.effective_user.id = 999
            await click('disable'); self.assertEqual(query.edit_message_text.call_count, before)
            update.effective_user.id = 101
            settings['allowed_users'] = []
            await click('disable'); self.assertEqual(query.edit_message_text.call_count, before)
            settings['allowed_users'] = ['101']
            adapter._is_callback_user_authorized.return_value = False
            await click('disable'); self.assertEqual(query.edit_message_text.call_count, before)
            adapter._is_callback_user_authorized.return_value = True
            store.get_or_create_session.return_value = NS(session_id='session-b')
            await click('disable'); self.assertEqual(query.edit_message_text.call_count, before)
            self.assertTrue(mod.state('usage-cost-audit')['enabled'])
            ctx.on_unload.call_args.args[0]()
            await click('enable'); self.assertEqual(query.edit_message_text.call_count, before)

PATH = Path(__file__).resolve().parents[1] / '__init__.py'

def module():
    spec = importlib.util.spec_from_file_location('catalog', PATH)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

class CatalogTests(unittest.TestCase):
    def test_native_registry_and_platform_persistence(self):
        from hermes_constants import get_hermes_home
        from hermes_cli.config import load_config, save_config
        from hermes_cli.skills_config import get_disabled_skills
        home = get_hermes_home()
        target = home / 'skills' / 'usage-cost-audit'
        target.mkdir(parents=True, exist_ok=True)
        (target / 'SKILL.md').write_text('---\nname: usage-cost-audit\ndescription: test audit\n---\n# Test\n')
        cfg = load_config()
        cfg['skills'] = {'disabled': ['another-global'], 'platform_disabled': {'discord': ['another-discord'], 'telegram': ['another-telegram']}}
        save_config(cfg)
        mod = module()
        self.assertTrue(mod.state('usage-cost-audit')['installed'])
        mod.toggle('usage-cost-audit', False)
        cfg = load_config()
        self.assertIn('usage-cost-audit', get_disabled_skills(cfg, 'telegram'))
        self.assertEqual(cfg['skills']['platform_disabled']['discord'], ['another-discord'])
        self.assertEqual(cfg['skills']['disabled'], ['another-global'])
        mod.toggle('usage-cost-audit', True)
        self.assertNotIn('usage-cost-audit', get_disabled_skills(load_config(), 'telegram'))
        self.assertIn('another-telegram', get_disabled_skills(load_config(), 'telegram'))
        cfg = load_config(); cfg['skills']['disabled'].append('usage-cost-audit'); save_config(cfg)
        with self.assertRaises(ValueError): mod.toggle('usage-cost-audit', True)
        with self.assertRaises(ValueError): mod.toggle('backup-and-recovery', False)

    def test_native_plugin_context_registers_factory(self):
        from hermes_cli.plugins import PluginContext, PluginManager
        from hermes_cli.plugins_manifest import PluginManifest
        from hermes_cli.config import load_config, save_config
        cfg = load_config()
        cfg.setdefault('plugins', {}).setdefault('entries', {})['toolkit-catalog'] = {'settings': {'opt_in': True, 'allowed_users': ['101'], 'allowed_chats': ['202']}}
        save_config(cfg)
        manager = PluginManager()
        ctx = PluginContext(PluginManifest(name='toolkit-catalog'), manager)
        module().register(ctx)
        self.assertEqual(len(manager.get_platform_handler_factories('telegram')), 1)

    def test_fail_closed_registration(self):
        from unittest.mock import Mock
        ctx = Mock(); ctx.get_config.side_effect = lambda key, default=None: default
        module().register(ctx)
        ctx.register_telegram_handler.assert_not_called()

    def test_ticket_owner_and_expiry(self):
        mod = module()
        tickets = mod.Tickets(clock=lambda: 10)
        owner = ('1', '2', '3', 'session-one')
        token = tickets.issue(owner, 7)
        self.assertTrue(tickets.valid(token, owner, 7))
        for bad in [('9', '2', '3', 'session-one'), ('1', '9', '3', 'session-one'), ('1', '2', '9', 'session-one'), ('1', '2', '3', 'session-two')]:
            self.assertFalse(tickets.valid(token, bad, 7))
        self.assertFalse(tickets.valid(token, owner, 8))
        tickets.clock = lambda: 1000
        self.assertFalse(tickets.valid(token, owner, 7))

    def test_reload_factories_replace_only_owned_handlers(self):
        from unittest.mock import Mock
        mod = module()
        cfg = {'opt_in': True, 'allowed_users': ['101'], 'allowed_chats': ['202']}
        ctx = Mock(); ctx.get_config.side_effect = lambda k, d=None: cfg.get(k, d)
        app = Mock(); foreign = object(); app.handlers = {-20: [foreign]}
        def add(handler, group): app.handlers.setdefault(group, []).append(handler)
        def remove(handler, group): app.handlers[group].remove(handler)
        app.add_handler.side_effect = add; app.remove_handler.side_effect = remove
        mod.register(ctx); factory = ctx.register_telegram_handler.call_args.args[0]
        factory(app, Mock())
        self.assertEqual(len(app.handlers[-20]), 3)
        ctx.on_unload.call_args.args[0]()
        mod.register(ctx); new = ctx.register_telegram_handler.call_args.args[0]
        self.assertNotEqual(factory.__qualname__, new.__qualname__)
        new(app, Mock())
        self.assertEqual(len(app.handlers[-20]), 3)
        self.assertIn(foreign, app.handlers[-20])

    def test_catalog_has_five_native_install_instructions(self):
        self.assertTrue(PATH.exists(), 'catalog implementation missing')
        spec = importlib.util.spec_from_file_location('catalog', PATH)
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertEqual(len(mod.CATALOG), 5)
        for name in mod.CATALOG:
            text = mod.install_instructions(name)
            self.assertIn('hermes skills install thomashuangth/hermes-toolkit/skills/' + name, text)
            self.assertNotIn('--yes', text)
            self.assertNotIn('--force', text)
