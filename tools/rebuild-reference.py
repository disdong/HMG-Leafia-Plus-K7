#!/usr/bin/env python3
"""Rebuild private reference APKs from exact reference stock + committed deltas.

This is a HOST tool, never an installer. No downloads, device access or /system writes.
Usage: python3 tools/rebuild-reference.py --variant dl3hev --stock /private/stock \
           --out private/reference-builds/dl3hev
An exact reference-car stock collection is required; a different car is rejected.
"""
import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from port import files_dir

ROOT = Path(__file__).resolve().parents[1]
LPATCH = ROOT / 'tools/lpatch/lpatch-host'
TOKEN = re.compile(r'^[A-Za-z0-9_.-]+$')
MD5 = re.compile(r'^[0-9a-f]{32}$')


def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()


def contained_file(root, relative):
    p = root / relative
    if Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise ValueError('Unsafe manifest path: ' + relative)
    if any(x.is_symlink() for x in (p, *p.parents)) or not p.is_file():
        raise ValueError('Missing or unsafe file: ' + relative)
    return p


def rebuild(variant, stock, out, patches=ROOT / 'patches', lpatch=LPATCH):
    if not TOKEN.fullmatch(variant) or variant in ('.', '..'):
        raise ValueError('Invalid variant')
    stock, out, patches = Path(stock).absolute(), Path(out).absolute(), Path(patches).absolute()
    if out.exists() or out.is_symlink():
        raise ValueError('Output already exists; choose a new private directory')
    resolved = out.resolve()
    if ROOT in resolved.parents and ROOT / 'private' not in resolved.parents:
        raise ValueError('Inside the repo, output must be under git-ignored private/')
    # Check every source before creating an output directory or running lpatch.
    sums = contained_file(patches, variant + '/stock').read_text().splitlines()
    for line in sums:
        if not line or line.startswith('#'):
            continue
        name, expected = line.split()
        if not TOKEN.fullmatch(name) or not MD5.fullmatch(expected):
            raise ValueError('Invalid stock checksum entry')
        p = contained_file(stock, ('lib/' if name.endswith('.so') else 'app/') + name)
        if md5(p) != expected:
            raise ValueError('Not the exact reference stock: ' + name)
    entries = []
    for line in contained_file(patches, variant + '/manifest').read_text().splitlines():
        if not line or line.startswith('#'):
            continue
        part, kind, name, delta, expected = line.split()
        if part not in ('2_tbt', '3_bridge') or kind not in ('app', 'file'):
            raise ValueError('Unexpected reference manifest entry')
        if not TOKEN.fullmatch(name) or not MD5.fullmatch(expected):
            raise ValueError('Invalid output name/checksum')
        patch = contained_file(patches, delta)
        src = contained_file(stock, 'app/' + name + '.odex' if kind == 'app' else 'lib/' + name)
        apk = contained_file(stock, 'app/' + name + '.apk') if kind == 'app' else None
        entries.append((part, kind, name, patch, expected, src, apk))
    if not entries:
        raise ValueError('Empty reference manifest')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='reference-', dir=out.parent) as td:
        tmp = Path(td)
        stage = tmp / 'builds'
        stage.mkdir()
        seen = set()
        for part, kind, name, patch, expected, src, apk in entries:
            folder = stage / part / files_dir(variant)
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / (name + '.apk' if kind == 'app' else name)
            if dest in seen:
                raise ValueError('Duplicate output in manifest')
            seen.add(dest)
            delta_out = tmp / 'classes.dex' if kind == 'app' else dest
            subprocess.run([str(lpatch), 'delta', str(patch), str(src), str(delta_out)], check=True)
            if kind == 'app':
                subprocess.run([str(lpatch), 'zipadd', str(apk), str(delta_out), str(dest)], check=True)
            if md5(dest) != expected:
                raise ValueError('Reference output checksum mismatch: ' + name)
        # Publish the directory only after every reconstructed result verifies.
        if out.exists():
            raise ValueError('Output appeared during build; refusing to replace it')
        stage.rename(out)
    return len(entries)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--variant', required=True)
    ap.add_argument('--stock', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    try:
        count = rebuild(a.variant, a.stock, a.out)
    except (ValueError, OSError, subprocess.CalledProcessError) as e:
        sys.exit('STOP: ' + str(e))
    print('Rebuilt %d verified reference files. Keep full APKs private.' % count)


if __name__ == '__main__':
    main()
