#!/usr/bin/env python3
"""Inspect an unpacked LEAFIA directory on the host; never writes to the car.

Usage: python3 tools/k7-intake.py /path/to/LEAFIA > private/k7-intake.json
Exit 0 means collection checks passed, NOT that a port is ready to install.
Keys and private logs are neither opened nor included in the output.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
APPS = ('HKMC_GPM', 'HKMC_DiPO', 'Iap2ServerApp', 'HKMC_Navi_ExSL')
LIB = 'libautoreceiver_infobank.so'
CORE = [f'app/{n}.{ext}' for n in APPS for ext in ('apk', 'odex')] + ['lib/' + LIB]
EXTRA = [f'app/{n}.{ext}' for n in ('PhoneProjection', 'HKMC_BtSettings')
         for ext in ('apk', 'odex')]
EXTRA += ['lib/' + n for n in ('libCarPlayCore.so', 'libCarPlayAudio.so',
                             'libCarPlayUtils.so', 'libopus.so', 'libstagefright_soft_aacdec.so')]
BCP = ('core conscrypt okhttp core-junit bouncycastle ext framework framework2 telephony-common '
       'voip-common mms-common android.policy services apache-xml webviewchromium automotive').split()
HASH_LINE = re.compile(r'^file /system/(\S+) md5=([0-9a-fA-F]{32})$')
SAFE_TOKEN = re.compile(r'^[A-Za-z0-9_.-]+$')


def digest(path, algorithm):
    h = hashlib.new(algorithm)
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def regular(root, relative):
    p = root / relative
    # Do not follow links outside (or inside) an uploaded collection.
    if any(x.is_symlink() for x in (p, *p.parents)):
        return False
    return p.is_file() and p.stat().st_size > 0


def inspect(leafia, patches=ROOT / 'patches'):
    leafia = Path(leafia).absolute()
    stock = leafia / 'private/stock'
    errors, warnings, props, recorded = [], [], {}, {}
    report_path = leafia / 'public/LEAFIA-REPORT.txt'
    text = report_path.read_text(encoding='utf-8', errors='replace') if regular(leafia, 'public/LEAFIA-REPORT.txt') else ''
    if not text.startswith('leafia-report 1') or not text.rstrip().endswith('end'):
        errors.append('Missing, unsupported or incomplete public/LEAFIA-REPORT.txt')
    for line in text.splitlines():
        if line.startswith('prop ') and '=' in line:
            key, value = line[5:].split('=', 1)
            if key in ('ro.build.product', 'ro.mobis.targetdir', 'ro.build.version.incremental'):
                props[key] = value
        m = HASH_LINE.fullmatch(line)
        if m:
            if m[1] in recorded and recorded[m[1]] != m[2].lower():
                errors.append('Conflicting report checksum: ' + m[1])
            recorded[m[1]] = m[2].lower()
    product = props.get('ro.build.product', '')
    if not product or not SAFE_TOKEN.fullmatch(product):
        errors.append('Missing or invalid ro.build.product; never substitute the Settings model name')
    targetdir = props.get('ro.mobis.targetdir', '')
    if not targetdir or not re.fullmatch(r'/system/onebin/[A-Za-z0-9_.-]+', targetdir):
        errors.append('Missing or unexpected ro.mobis.targetdir; inspect manually')
    # The build property must agree with the live report, if both were collected.
    if regular(stock, 'build.prop'):
        bp = dict(line.split('=', 1) for line in (stock / 'build.prop').read_text(
            encoding='utf-8', errors='replace').splitlines() if '=' in line and not line.startswith('#'))
        if bp.get('ro.build.product') != product:
            errors.append('build.prop and public report identify different firmware')
    else:
        errors.append('Missing private/stock/build.prop')
    inventory = {}
    required = CORE + [f'framework/{n}.odex' for n in BCP] + ['onebin/featurexml.cfg']
    for relative in required + EXTRA:
        if not regular(stock, relative):
            (errors if relative in required else warnings).append('Missing or unsafe stock file: ' + relative)
            continue
        p = stock / relative
        entry = {'bytes': p.stat().st_size, 'md5': digest(p, 'md5'), 'sha256': digest(p, 'sha256')}
        inventory[relative] = entry
        if relative in recorded and recorded[relative] != entry['md5']:
            errors.append('Collected bytes differ from live report: ' + relative)
        elif relative in CORE and relative not in recorded:
            errors.append('No live-report checksum for: ' + relative)
    candidates = []
    for sums in sorted(Path(patches).glob('*/stock')):
        expected = dict(line.split() for line in sums.read_text().splitlines() if line and not line.startswith('#'))
        matched, different, missing = [], [], []
        for relative in CORE:
            name = Path(relative).name
            if relative not in inventory or name not in expected:
                missing.append(name)
            elif inventory[relative]['md5'] == expected[name]:
                matched.append(name)
            else:
                different.append(name)
        candidates.append({'variant': sums.parent.name, 'matched': matched, 'different': different, 'missing': missing,
                           'exact_stock_match': not different and not missing})
    warnings += [
        'Collection success does not verify Wi-Fi, package compatibility, Dalvik execution or Kia Connect.',
        'A port may also require exact reference-car stock/framework and rebuilt reference APKs.',
        'Do not publish this collection or complete APK builds. Keys/logs were not inspected.',
        'Review installed NEMESIS packages and Wi-Fi driver evidence in public/summary.txt before installing.'
    ]
    return {'schema': 1, 'collection_complete': not errors, 'install_ready': False,
            'identity': props, 'stock': inventory, 'reference_candidates': candidates,
            'errors': errors, 'warnings': warnings}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('leafia', type=Path)
    a = ap.parse_args()
    result = inspect(a.leafia)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result['collection_complete'] else 2


if __name__ == '__main__':
    sys.exit(main())
