import os
import tempfile
# Isolate before ANY Hermes import.
_home = tempfile.TemporaryDirectory(prefix='approval-test-', dir=os.environ.get('TMPDIR'))
os.environ['HERMES_HOME'] = _home.name
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from plugins.platforms.telegram.adapter import TelegramAdapter
from gateway.platforms.base import SendResult
from unittest.mock import patch
_scope = patch("gateway.session_context.get_session_env", return_value="1001")
_scope.start()
def settings(key, default=None):
    return {"opt_in": True, "allowed_users": ["1001"], "allowed_chats": ["1001"]}.get(key, default)
spec = importlib.util.spec_from_file_location('explainer', Path(__file__).parents[1] / '__init__.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

class ExplainerTests(unittest.TestCase):
    def setUp(self):
        self.cleanup = []
        p.register(SimpleNamespace(get_config=settings, on_unload=self.cleanup.append))
        self.adapter = object.__new__(TelegramAdapter)
        self.adapter._approval_state = {}
        self.adapter._reply_to_mode = 'off'
        self.sent = []
        async def send(name, chat, metadata, build, **kwargs):
            text, keyboard, callback = build()
            self.sent.append((text, keyboard, kwargs))
            callback(SimpleNamespace(message_id=77))
            return SendResult(success=True, message_id='77')
        self.adapter._send_prompt = send
    def tearDown(self):
        for f in reversed(self.cleanup): f()
    def send(self, **kwargs):
        return asyncio.run(self.adapter.send_exec_approval('1001', kwargs.pop('command', 'rm -rf /example'),
            'test-session', metadata={'thread_id': '7'}, **kwargs))
    def test_real_native_renderer_and_callbacks(self):
        result = self.send(description='Deletes files recursively')
        self.assertTrue(result.success)
        text, keyboard, opts = self.sent[0]
        for heading in ('But', 'Pourquoi ton accord', 'Risques', 'Portée'): self.assertIn('<b>'+heading+'</b>', text)
        self.assertIn('Deletes files recursively', text)
        self.assertIn('ne peux pas le confirmer', text)
        self.assertIn('PAS une correspondance exacte', text)
        self.assertNotIn('<blockquote', text)
        self.assertEqual([b.callback_data for row in keyboard.inline_keyboard for b in row],
                         ['ea:once:1','ea:session:1','ea:always:1','ea:deny:1'])
        self.assertEqual(self.adapter._approval_state[1], 'test-session')
        self.assertEqual(opts['parse_mode'], 'HTML')
    def test_smart_deny_preserves_choice_set(self):
        self.send(description='High risk', smart_denied=True)
        text, keyboard, _ = self.sent[0]
        self.assertNotIn('Toujours :', text)
        self.assertNotIn('Session :', text)
        self.assertEqual([b.callback_data for row in keyboard.inline_keyboard for b in row], ['ea:once:1','ea:deny:1'])
    def test_long_html_utf16(self):
        self.send(command='printf '+ '<&😀'*5000, description='<script>'+ '😀&'*2000)
        text = self.sent[0][0]
        self.assertLessEqual(self.adapter.message_len_fn(text), 4096)
        self.assertNotIn('<script>', text)
        self.assertIn('<b>Portée</b>', text)
    def test_no_permanent(self):
        self.send(allow_permanent=False)
        self.assertNotIn('Toujours :', self.sent[0][0])
    def test_other_chat_native(self):
        asyncio.run(self.adapter.send_exec_approval('999', 'printf ok', 'session', description='Native'))
        self.assertNotIn('<b>But</b>', self.sent[0][0])
    def test_reload_does_not_stack(self):
        before = TelegramAdapter.send_exec_approval._fr_approval_original
        p.register(SimpleNamespace(get_config=settings, on_unload=self.cleanup.append))
        self.assertIs(TelegramAdapter.send_exec_approval._fr_approval_original, before)
        self.send()
        self.assertEqual(len(self.sent), 1)
    def test_other_profile_is_inert(self):
        before = TelegramAdapter.send_exec_approval
        p.register(SimpleNamespace(get_config=lambda key, default=None: default, on_unload=lambda cb: self.fail('must be inert')))
        self.assertIs(TelegramAdapter.send_exec_approval, before)
    def test_unload_restores(self):
        patched = TelegramAdapter.send_exec_approval
        self.cleanup.pop()()
        self.assertIs(TelegramAdapter.send_exec_approval, patched._fr_approval_original)

if __name__ == '__main__': unittest.main()
