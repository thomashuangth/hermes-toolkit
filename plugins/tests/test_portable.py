import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class Portable(unittest.TestCase):
    def load(self, name):
        spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT/name/'__init__.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_unconfigured_register_is_inert(self):
        class Context:
            def get_config(self, key, default=None): return default
        for name in ('short-topic-names', 'telegram-title', 'telegram-approval-explainer', 'runtime-status-footer'):
            with self.subTest(name=name):
                self.load(name).register(Context())

    def test_short_long_single_word(self):
        self.assertLessEqual(len(self.load('short-topic-names').shorten('x'*80)), 24)

    def test_scoped_shortening_and_unload(self):
        import sys
        from types import ModuleType
        from unittest.mock import patch
        module=self.load('short-topic-names')
        topics=ModuleType('gateway.run_topics')
        session=ModuleType('gateway.session_context')
        class Mixin:
            def _sanitize_telegram_topic_title(self, title): return title
        topics.GatewayTopicThreadsMixin=Mixin
        values={'HERMES_SESSION_PLATFORM':'telegram','HERMES_SESSION_USER_ID':'1001','HERMES_SESSION_CHAT_ID':'1001'}
        session.get_session_env=values.get
        cleanup=[]
        class Context:
            def get_config(self, key, default=None):
                return {'opt_in':True,'allowed_users':['1001'],'allowed_chats':['1001']}.get(key,default)
            def on_unload(self, callback): cleanup.append(callback)
        with patch.dict(sys.modules, {'gateway.run_topics':topics,'gateway.session_context':session}):
            original=Mixin._sanitize_telegram_topic_title
            module.register(Context())
            self.assertLessEqual(len(Mixin()._sanitize_telegram_topic_title('x'*80)),24)
            values['HERMES_SESSION_USER_ID']='1002'
            self.assertEqual(Mixin()._sanitize_telegram_topic_title('x'*80),'x'*80)
            cleanup.pop()()
            self.assertIs(Mixin._sanitize_telegram_topic_title,original)

    def test_title_explicit_preserved(self):
        import asyncio
        module=self.load('telegram-title')
        seen=[]
        async def rename(title): seen.append(title); return {'ok':True}
        async def persist(title): return True
        async def generate(): raise AssertionError('must not generate')
        asyncio.run(module.apply_title('un  titre',rename,persist,generate))
        self.assertEqual(seen,['un  titre'])

    def test_provider_unknown_fails_closed(self):
        self.assertFalse(self.load('runtime-status-footer')._same_provider(None,'codex'))

if __name__ == '__main__': unittest.main()
