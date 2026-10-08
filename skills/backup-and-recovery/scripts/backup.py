"""Explicit allowlist backup and isolated verification; Python stdlib only."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import sqlite3
import tarfile
import tempfile

MAX_BYTES = 64 * 1024 * 1024
DENIED = {'.env', 'auth.json', 'credentials.json', 'secrets.json'}


def safe_name(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe archive path')
    if any(part.lower() in DENIED or any(word in part.lower() for word in ('secret', 'credential', 'token', 'private_key')) for part in p.parts):
        raise ValueError('Credential-like path refused')
    return p


def source_file(root, name):
    p = safe_name(name)
    target = root
    for part in p.parts:
        target = target / part
        if target.is_symlink():
            raise ValueError('Symlink refused')
    if not target.is_file():
        raise ValueError('Regular file required')
    return target


def sqlite_check(path):
    with sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True) as db:
        if db.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('SQLite integrity failure')


def create(root, archive, names):
    root, archive = Path(root), Path(archive)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Regular source directory required')
    if archive.exists() or archive.is_symlink():
        raise ValueError('Archive already exists')
    if not names or len(set(names)) != len(names) or 'manifest.json' in names:
        raise ValueError('Nonempty unique allowlist required')
    payload = {}
    with tempfile.TemporaryDirectory() as scratch:
        for i, name in enumerate(names):
            src = source_file(root, name)
            if src.stat().st_size > MAX_BYTES:
                raise ValueError('File too large')
            if src.suffix == '.db':
                dst = Path(scratch) / str(i)
                with sqlite3.connect(src.resolve().as_uri() + '?mode=ro', uri=True) as live, sqlite3.connect(dst) as copy:
                    live.backup(copy)
                sqlite_check(dst)
                data = dst.read_bytes()
            else:
                data = src.read_bytes()
            payload[name] = data
        if sum(map(len, payload.values())) > MAX_BYTES:
            raise ValueError('Backup too large')
        manifest = {n: {'sha256': hashlib.sha256(d).hexdigest(), 'size': len(d)} for n, d in payload.items()}
        payload['manifest.json'] = json.dumps(manifest, sort_keys=True).encode()
        fd = os.open(archive, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'wb') as out, tarfile.open(fileobj=out, mode='w:gz') as tar:
                for n, d in payload.items():
                    info = tarfile.TarInfo(n)
                    info.size, info.mode = len(d), 0o600
                    tar.addfile(info, io.BytesIO(d))
            verify(archive)
        except Exception:
            archive.unlink(missing_ok=True)
            raise
    return {'files': len(manifest), 'verified': True}


def verify(archive):
    payload = {}
    with tarfile.open(archive, 'r:gz') as tar:
        total = 0
        for member in tar:
            safe_name(member.name)
            total += member.size
            if not member.isfile() or member.name in payload or member.size < 0 or total > MAX_BYTES + 1024 * 1024:
                raise ValueError('Invalid archive member or size')
            payload[member.name] = tar.extractfile(member).read()
    manifest = json.loads(payload.pop('manifest.json'))
    if not manifest or set(manifest) != set(payload):
        raise ValueError('Manifest mismatch')
    with tempfile.TemporaryDirectory() as scratch:
        for i, (name, data) in enumerate(payload.items()):
            if manifest[name] != {'sha256': hashlib.sha256(data).hexdigest(), 'size': len(data)}:
                raise ValueError('Hash mismatch')
            # Materialize only opaque filenames in a private isolated directory.
            restored = Path(scratch) / str(i)
            restored.write_bytes(data)
            restored.chmod(0o600)
            if PurePosixPath(name).suffix == '.db':
                sqlite_check(restored)
    return {'files': len(payload), 'verified': True, 'production_restored': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    backup = commands.add_parser('create')
    backup.add_argument('--source', required=True)
    backup.add_argument('--archive', required=True)
    backup.add_argument('--include', action='append', required=True)
    check = commands.add_parser('restore-check')
    check.add_argument('--archive', required=True)
    args = parser.parse_args()
    try:
        result = create(args.source, args.archive, args.include) if args.command == 'create' else verify(args.archive)
        print(json.dumps(result))
    except Exception:
        print(json.dumps({'verified': False, 'error': 'Backup or verification failed; inspect locally without sharing sensitive data.'}))
        raise SystemExit(2)
