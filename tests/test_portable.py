import importlib.util
import io
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'skills' / name / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

backup = load('backup-and-recovery', 'backup.py')
watchdog = load('scheduled-task-watchdog', 'watchdog.py')

class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'note.txt').write_text('fixture')
        self.archive = self.root / 'archive.tar.gz'

    def test_roundtrip_and_no_production_write(self):
        self.assertTrue(backup.create(self.source, self.archive, ['note.txt'])['verified'])
        self.assertFalse(backup.verify(self.archive)['production_restored'])
        self.assertEqual((self.source / 'note.txt').read_text(), 'fixture')

    def test_sqlite(self):
        with sqlite3.connect(self.source / 'sample.db') as db:
            db.execute('create table fixture(value)')
            db.execute('insert into fixture values (1)')
        self.assertEqual(backup.create(self.source, self.archive, ['sample.db'])['files'], 1)

    def test_existing_destination(self):
        self.archive.write_text('keep')
        with self.assertRaises(ValueError):
            backup.create(self.source, self.archive, ['note.txt'])
        self.assertEqual(self.archive.read_text(), 'keep')

    def test_denied_and_traversal(self):
        for name in ['../note.txt', '/note.txt', '.env', 'auth.json', 'x\\y', 'tokens.txt']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                backup.create(self.source, self.archive, [name])

    def test_symlink(self):
        try:
            (self.source / 'link').symlink_to(self.source / 'note.txt')
        except OSError:
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(ValueError):
            backup.create(self.source, self.archive, ['link'])

    def test_corrupt_archive(self):
        self.archive.write_bytes(b'not gzip')
        with self.assertRaises(tarfile.ReadError):
            backup.verify(self.archive)

    def malicious(self, name, link=False, data=b'fixture'):
        with tarfile.open(self.archive, 'w:gz') as tar:
            info = tarfile.TarInfo(name)
            if link:
                info.type = tarfile.SYMTYPE
                info.linkname = 'outside'
                tar.addfile(info)
            else:
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))

    def test_archive_traversal(self):
        self.malicious('../outside')
        with self.assertRaises(ValueError):
            backup.verify(self.archive)
        self.assertFalse((self.root / 'outside').exists())

    def test_archive_link(self):
        self.malicious('link', True)
        with self.assertRaises(ValueError):
            backup.verify(self.archive)

    def test_hash_mismatch(self):
        with tarfile.open(self.archive, 'w:gz') as tar:
            for name, data in [('note.txt', b'changed'), ('manifest.json', json.dumps({'note.txt': {'sha256': 'wrong', 'size': 7}}).encode())]:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        with self.assertRaises(ValueError):
            backup.verify(self.archive)

    def test_cli(self):
        script = ROOT / 'skills/backup-and-recovery/scripts/backup.py'
        result = subprocess.run([sys.executable, str(script), 'create', '--source', str(self.source), '--archive', str(self.archive), '--include', 'note.txt'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run([sys.executable, str(script), 'restore-check', '--archive', str(self.archive)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)['verified'])

class WatchdogTests(unittest.TestCase):
    def job(self, **kwargs):
        return dict(id='fixture', enabled=True, status='ok', last_success=90, max_age_seconds=20, **kwargs)

    def test_healthy(self):
        self.assertEqual(watchdog.inspect([self.job()], 100), [])

    def test_stale(self):
        self.assertEqual(watchdog.inspect([self.job()], 111)[0]['reason'], 'stale')

    def test_failed_never_future(self):
        for changes, expected in [({'status': 'failed'}, 'failed'), ({'last_success': None}, 'never_succeeded'), ({'last_success': 101}, 'future_timestamp')]:
            job = self.job(); job.update(changes)
            self.assertEqual(watchdog.inspect([job], 100)[0]['reason'], expected)

    def test_exclusions(self):
        for change in [{'enabled': False}, {'status': 'completed'}]:
            job = self.job(); job.update(change)
            self.assertEqual(watchdog.inspect([job], 999), [])
        self.assertEqual(watchdog.inspect([self.job()], 999, 'fixture'), [])

    def test_invalid(self):
        for value in [float('nan'), -1, True, '20']:
            job = self.job(); job['max_age_seconds'] = value
            with self.assertRaises(ValueError):
                watchdog.inspect([job], 100)
        with self.assertRaises(ValueError):
            watchdog.inspect([self.job(), self.job()], 100)

    def test_cli_codes_and_silence(self):
        script = ROOT / 'skills/scheduled-task-watchdog/scripts/watchdog.py'
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'receipts.json'
            for content, code in [([self.job()], 0), ([dict(self.job(), status='failed')], 1), ({}, 2)]:
                source.write_text(json.dumps(content))
                result = subprocess.run([sys.executable, str(script), '--input', str(source), '--now', '100'], capture_output=True, text=True)
                self.assertEqual(result.returncode, code)
                if code == 0:
                    self.assertEqual(result.stdout, '')

class FormatTests(unittest.TestCase):
    def test_five_skill_frontmatters(self):
        files = sorted((ROOT / 'skills').glob('*/SKILL.md'))
        self.assertEqual(len(files), 5)
        for path in files:
            text = path.read_text()
            match = re.match(r'^---\n(.*?)\n---\n(.+)', text, re.S)
            self.assertIsNotNone(match)
            front, body = match.groups()
            self.assertIn('name: ' + path.parent.name + '\n', front)
            description = re.search(r'^description: "(.+)"$', front, re.M).group(1)
            self.assertLessEqual(len(description), 60)
            self.assertTrue(description.endswith('.'))
            for field in ['version:', 'author:', 'license: MIT', 'platforms:', 'metadata:', 'related_skills: []']:
                self.assertIn(field, front)
            for section in ['## When to Use', '## Pitfalls', '## Verification']:
                self.assertIn(section, body)

    def test_no_local_identifiers(self):
        for path in (ROOT / 'skills').rglob('*'):
            if path.is_file() and path.suffix in {'.md', '.py'}:
                text = path.read_text()
                self.assertNotRegex(text, r'/home/|/volume\d/|\b(?:\d{1,3}\.){3}\d{1,3}\b')

if __name__ == '__main__':
    unittest.main()
