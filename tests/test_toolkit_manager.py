import contextlib
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/toolkit-manager/scripts/install_catalog.py'
spec = importlib.util.spec_from_file_location('installer', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class BootstrapTests(unittest.TestCase):
    def fixture(self, root, extra=None):
        archive = root / 'fixture.zip'
        prefix = 'hermes-toolkit-' + m.DEFAULT_REF + '/'
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr(prefix + 'plugins/toolkit-catalog/plugin.yaml', 'name: toolkit-catalog')
            z.writestr(prefix + 'plugins/toolkit-catalog/__init__.py', '# fixture')
            z.writestr(prefix + 'plugins/other/private.txt', 'excluded')
            z.writestr(prefix + 'skills/other/SKILL.md', 'excluded')
            if extra:
                z.writestr(extra, 'unsafe')
        return archive

    def test_only_catalog(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            dest = root / 'out'
            m.extract_catalog(self.fixture(root), dest, m.DEFAULT_REF)
            self.assertEqual(sorted(p.name for p in dest.iterdir()), ['__init__.py', 'plugin.yaml'])

    def test_traversal_rejected_even_outside_subtree(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            with self.assertRaises(ValueError):
                m.extract_catalog(self.fixture(root, '../escape'), root / 'out', m.DEFAULT_REF)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            archive = self.fixture(root)
            with zipfile.ZipFile(archive, 'a') as z:
                item = zipfile.ZipInfo('hermes-toolkit-' + m.DEFAULT_REF + '/plugins/toolkit-catalog/link')
                item.external_attr = 0o120777 << 16
                z.writestr(item, '/outside')
            with self.assertRaises(ValueError):
                m.extract_catalog(archive, root / 'out', m.DEFAULT_REF)

    def test_dry_run_no_network_no_writes(self):
        with tempfile.TemporaryDirectory() as t:
            home = Path(t) / 'not-created'
            with patch.dict(os.environ, HERMES_HOME=str(home)), patch.object(m.urllib.request, 'urlopen') as network, patch.object(m.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(m.main(['--user-id', '123', '--chat-id', '-456']), 0)
                network.assert_not_called()
                run.assert_not_called()
                self.assertFalse(home.exists())

    def test_existing_refused(self):
        with tempfile.TemporaryDirectory() as t:
            home = Path(t)
            (home / 'plugins/toolkit-catalog').mkdir(parents=True)
            with patch.dict(os.environ, HERMES_HOME=t), self.assertRaises(ValueError):
                m.main(['--user-id', '123', '--chat-id', '456'])

    def test_doctor_failure_never_configures_or_enables(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            archive = self.fixture(root).read_bytes()
            response = io.BytesIO(archive)
            response.geturl = lambda: 'https://codeload.github.com/' + m.REPO + '/zip/' + m.DEFAULT_REF
            home = root / 'home'
            with patch.dict(os.environ, HERMES_HOME=str(home)), patch.object(m.urllib.request, 'urlopen', return_value=response), patch.object(m.subprocess, 'run', side_effect=m.subprocess.CalledProcessError(1, 'doctor')) as run, contextlib.redirect_stdout(io.StringIO()), self.assertRaises(m.subprocess.CalledProcessError):
                m.main(['--user-id', '123', '--chat-id', '456', '--install'])
            self.assertEqual(run.call_count, 1)
            self.assertEqual(list(home.iterdir()), [])

    def test_install_sequence_and_cleanup(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            response = io.BytesIO(self.fixture(root).read_bytes())
            response.geturl = lambda: 'https://codeload.github.com/' + m.REPO + '/zip/' + m.DEFAULT_REF
            home = root / 'home'
            with patch.dict(os.environ, HERMES_HOME=str(home)), patch.object(m.urllib.request, 'urlopen', return_value=response), patch.object(m.subprocess, 'run') as run, contextlib.redirect_stdout(io.StringIO()):
                m.main(['--user-id', '123', '--chat-id', '-456', '--install'])
            calls = [c.args[0] for c in run.call_args_list]
            self.assertEqual(len(calls), 7)
            self.assertEqual(calls[0][1:3], ['plugins', 'doctor'])
            self.assertEqual(calls[-2], ['hermes', 'plugins', 'enable', 'toolkit-catalog'])
            self.assertEqual(list(home.iterdir()), [home / 'plugins'])
            self.assertTrue((home / 'plugins/toolkit-catalog/plugin.yaml').is_file())

    def test_bad_inputs(self):
        for args in (['--user-id', '1;evil', '--chat-id', '2'], ['--user-id', '1', '--chat-id', '2', '--ref', 'main']):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                m.main(args)
