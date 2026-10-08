#!/usr/bin/env python3
"""Explicit, pinned, subtree-only bootstrap; dry-run unless --install."""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile

REPO = 'thomashuangth/hermes-toolkit'
DEFAULT_REF = 'dab1484b3f3c0dffb018b0ecbe67addb34690b0b'
LIMIT = 32 * 1024 * 1024


def extract_catalog(archive, dest, ref):
    prefix = 'hermes-toolkit-' + ref + '/'
    subtree = prefix + 'plugins/toolkit-catalog/'
    total = 0
    seen = set()
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            name = item.filename
            p = PurePosixPath(name)
            mode = item.external_attr >> 16
            if (not name.startswith(prefix) or '\\' in name or p.is_absolute()
                    or any(part in ('.', '..') or ':' in part for part in name.rstrip('/').split('/'))
                    or (mode & 0o170000) not in (0, 0o040000, 0o100000)):
                raise ValueError('Unsafe archive member: ' + name)
            if name in seen:
                raise ValueError('Duplicate archive member')
            seen.add(name)
            total += item.file_size
            if total > LIMIT:
                raise ValueError('Expanded archive exceeds limit')
            if not name.startswith(subtree) or item.is_dir():
                continue
            relative = name[len(subtree):]
            target = dest.joinpath(*PurePosixPath(relative).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(item) as src, target.open('xb') as out:
                shutil.copyfileobj(src, out)
    for required in ('plugin.yaml', '__init__.py'):
        if not (dest / required).is_file():
            raise ValueError('Archive missing catalog ' + required)


def commands(target, user, chat):
    key = 'plugins.entries.toolkit-catalog.settings.'
    return [
        ['hermes', 'plugins', 'doctor', str(target), '--ci'],
        ['hermes', 'config', 'set', key + 'allowed_users', json.dumps([user])],
        ['hermes', 'config', 'set', key + 'allowed_chats', json.dumps([chat])],
        ['hermes', 'config', 'set', key + 'opt_in', 'true'],
        ['hermes', 'plugins', 'enable', 'toolkit-catalog'],
        ['hermes', 'plugins', 'list'],
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user-id', required=True)
    parser.add_argument('--chat-id', required=True)
    parser.add_argument('--ref', default=DEFAULT_REF, help='Verified full 40-character GitHub commit SHA')
    parser.add_argument('--install', action='store_true', help='Approved copy, doctor, config and enable; otherwise plan only')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[0-9a-f]{40}', args.ref):
        parser.error('--ref must be a full lowercase commit SHA, not a branch/tag')
    if not re.fullmatch(r'[1-9][0-9]*', args.user_id) or not re.fullmatch(r'-?[1-9][0-9]*', args.chat_id):
        parser.error('Explicit numeric Telegram user/chat IDs required')
    raw_home = Path(os.environ.get('HERMES_HOME', str(Path.home() / '.hermes'))).expanduser()
    home = raw_home.resolve()
    plugins = home / 'plugins'
    target = plugins / 'toolkit-catalog'
    if plugins.is_symlink() or target.exists() or target.is_symlink():
        raise ValueError('Refusing symlink plugins directory or existing catalog; inspect manually')
    plan = commands(target, args.user_id, args.chat_id)
    print(json.dumps({'install': args.install, 'home': str(home), 'repo': REPO,
                      'ref': args.ref, 'target': str(target), 'commands': plan}, indent=2))
    if not args.install:
        return 0
    env = dict(os.environ, HERMES_HOME=str(home))
    # Staging remains outside the discoverable plugins directory.
    home.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='toolkit-stage-', dir=home) as tmp:
        stage = Path(tmp)
        archive = stage / 'source.zip'
        url = 'https://codeload.github.com/' + REPO + '/zip/' + args.ref
        with urllib.request.urlopen(url, timeout=60) as response, archive.open('xb') as out:
            if response.geturl() != url:
                raise ValueError('Unexpected archive redirect')
            data = response.read(LIMIT + 1)
            if len(data) > LIMIT:
                raise ValueError('Download exceeds limit')
            out.write(data)
        catalog = stage / 'toolkit-catalog'
        catalog.mkdir()
        extract_catalog(archive, catalog, args.ref)
        subprocess.run(['hermes', 'plugins', 'doctor', str(catalog), '--ci'], env=env, check=True)
        plugins.mkdir(exist_ok=True)
        if plugins.is_symlink():
            raise ValueError('Refusing symlink plugins directory')
        # mkdir is exclusive; never merge/overwrite an existing local plugin.
        target.mkdir()
        try:
            shutil.copytree(catalog, target, dirs_exist_ok=True)
        except BaseException:
            shutil.rmtree(target)
            raise
        # Failure leaves the installed tree for inspection, never bypasses doctor.
        for command in plan:
            subprocess.run(command, env=env, check=True)
    print('Installed. Verify native config get and send /toolkit in the approved Telegram session.')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        raise SystemExit('Bootstrap stopped: ' + str(exc))
