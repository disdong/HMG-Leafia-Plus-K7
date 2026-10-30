"""Host-only porting checks; all binary fixtures are invented, never OEM files."""
import hashlib
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import port


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


intake = load('intake', 'k7-intake.py')
reference = load('reference', 'rebuild-reference.py')


def md5(data):
    return hashlib.md5(data).hexdigest()


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.leafia = self.root / 'LEAFIA'
        self.stock = self.leafia / 'private/stock'
        self.patches = self.root / 'patches'
        report = ['leafia-report 1', 'prop ro.build.product=TEST.KOR.0000.260902',
                  'prop ro.mobis.targetdir=/system/onebin/test_kr']
        for rel in intake.CORE + [f'framework/{n}.odex' for n in intake.BCP] + ['onebin/featurexml.cfg']:
            p = self.stock / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(('fixture:' + rel).encode())
            report.append('file /system/%s md5=%s' % (rel, md5(p.read_bytes())))
        (self.stock / 'build.prop').write_text('ro.build.product=TEST.KOR.0000.260902\n')
        (self.leafia / 'public').mkdir()
        self.report = self.leafia / 'public/LEAFIA-REPORT.txt'
        self.report.write_text('\n'.join(report + ['end']) + '\n')
        (self.patches / 'test').mkdir(parents=True)
        (self.patches / 'test/stock').write_text('\n'.join(
            Path(r).name + ' ' + md5((self.stock / r).read_bytes()) for r in intake.CORE))

    def inspect(self):
        return intake.inspect(self.leafia, self.patches)

    def test_complete_is_not_install_ready(self):
        r = self.inspect()
        self.assertTrue(r['collection_complete'])
        self.assertFalse(r['install_ready'])
        self.assertTrue(r['reference_candidates'][0]['exact_stock_match'])

    def test_missing_framework_blocks_collection(self):
        (self.stock / 'framework/automotive.odex').unlink()
        self.assertFalse(self.inspect()['collection_complete'])

    def test_corrupted_copy_does_not_match_report(self):
        (self.stock / intake.CORE[0]).write_bytes(b'changed after collection')
        r = self.inspect()
        self.assertFalse(r['collection_complete'])
        self.assertTrue(any('differ from live report' in e for e in r['errors']))
        self.assertFalse(r['reference_candidates'][0]['exact_stock_match'])

    def test_mixed_vehicle_report_is_rejected(self):
        (self.stock / 'build.prop').write_text('ro.build.product=OTHER.KOR\n')
        self.assertFalse(self.inspect()['collection_complete'])

    def test_brand_wide_product_with_same_build_is_allowed(self):
        report = self.report.read_text().replace('prop ro.build.product=',
            'prop ro.build.branch=fixture-branch\nprop ro.build.version.incremental=fixture-incremental\nprop ro.build.product=')
        self.report.write_text(report)
        (self.stock / 'build.prop').write_text('ro.build.product=KIA.KOR.0000.260902\n'
            'ro.build.branch=fixture-branch\nro.build.version.incremental=fixture-incremental\n')
        self.assertTrue(self.inspect()['collection_complete'])
        (self.stock / 'build.prop').write_text('ro.build.product=KIA.KOR.0000.260206\n'
            'ro.build.branch=fixture-branch\nro.build.version.incremental=fixture-incremental\n')
        self.assertFalse(self.inspect()['collection_complete'])

    def test_unrelated_generic_firmware_is_not_accepted(self):
        (self.stock / 'build.prop').write_text('ro.build.product=KIA.KOR.0000.260902\n')
        self.assertFalse(self.inspect()['collection_complete'])

    def test_missing_wifi_adapter_does_not_claim_physical_absence(self):
        (self.leafia / 'public/summary.txt').write_text('wl: wl driver adapter not found\n')
        r = self.inspect()
        self.assertTrue(r['collection_complete'])
        self.assertEqual(r['wifi']['state'], 'not-detected')
        self.assertEqual(r['wifi']['physical_module_presence'], 'not-established-by-this-test')
        self.assertFalse(r['install_ready'])

    def test_truncated_report_is_rejected(self):
        self.report.write_text(self.report.read_text().replace('\nend\n', '\n'))
        self.assertFalse(self.inspect()['collection_complete'])

    def test_private_keys_and_logs_not_read(self):
        for folder in ('keys', 'logs'):
            p = self.leafia / 'private' / folder
            p.mkdir()
            (p / 'secret').write_text('DO-NOT-READ-THIS-SECRET')
        self.assertNotIn('DO-NOT-READ-THIS-SECRET', str(self.inspect()))

    def test_symlink_stock_rejected(self):
        p = self.stock / intake.CORE[0]
        outside = self.root / 'outside'
        p.rename(outside)
        p.symlink_to(outside)
        self.assertFalse(self.inspect()['collection_complete'])


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.lpatch = Path(cls.tmp.name) / 'lpatch-host'
        subprocess.run(['cc', '-DHOST', '-O2', '-o', str(cls.lpatch),
                        str(ROOT / 'tools/lpatch/lpatch.c')], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.tmp_case = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_case.cleanup)
        self.root = Path(self.tmp_case.name)
        self.stock = self.root / 'stock'
        self.patches = self.root / 'patches'
        (self.stock / 'lib').mkdir(parents=True)
        (self.patches / 'test').mkdir(parents=True)
        self.source, self.target = b'original own fixture', b'patched own fixture'
        (self.stock / 'lib/libtest.so').write_bytes(self.source)
        (self.patches / 'test/stock').write_text('libtest.so ' + md5(self.source) + '\n')
        # Valid LPD1 with one extra-only control record, generated from our own data.
        body = (struct.pack('<IiiiI', 1, 0, len(self.target), 0, 0)
                + struct.pack('<I', len(self.target)) + self.target)
        comp = zlib.compressobj(9, zlib.DEFLATED, -15)
        payload = comp.compress(body) + comp.flush()
        hdr = (b'LPD1' + struct.pack('<I', len(self.source)) + hashlib.md5(self.source).digest()
               + struct.pack('<I', len(self.target)) + hashlib.md5(self.target).digest()
               + struct.pack('<II', 1, len(payload)))
        (self.patches / 'test/libtest.lpd').write_bytes(hdr + payload)
        self.manifest = self.patches / 'test/manifest'
        self.manifest.write_text('2_tbt file libtest.so test/libtest.lpd ' + md5(self.target) + '\n')
        self.out = self.root / 'private-builds'

    def rebuild(self):
        return reference.rebuild('test', self.stock, self.out, self.patches, self.lpatch)

    def test_reference_reconstruction_verifies_bytes(self):
        self.assertEqual(self.rebuild(), 1)
        self.assertEqual((self.out / '2_tbt/files_test/libtest.so').read_bytes(), self.target)
        self.assertEqual((self.stock / 'lib/libtest.so').read_bytes(), self.source)

    def test_apk_reconstruction_preserves_stock_entries(self):
        (self.stock / 'app').mkdir()
        apk = self.stock / 'app/Demo.apk'
        with zipfile.ZipFile(apk, 'w') as z:
            z.writestr('AndroidManifest.xml', b'invented manifest')
            z.writestr('res/raw/demo', b'invented resource')
        (self.stock / 'app/Demo.odex').write_bytes(self.source)
        with (self.patches / 'test/stock').open('a') as f:
            f.write('Demo.apk ' + md5(apk.read_bytes()) + '\n')
            f.write('Demo.odex ' + md5(self.source) + '\n')
        expected = self.root / 'expected.apk'
        dex = self.root / 'dex'
        dex.write_bytes(self.target)
        subprocess.run([str(self.lpatch), 'zipadd', str(apk), str(dex), str(expected)],
                       check=True, stdout=subprocess.DEVNULL)
        with self.manifest.open('a') as f:
            f.write('3_bridge app Demo test/libtest.lpd ' + md5(expected.read_bytes()) + '\n')
        self.assertEqual(self.rebuild(), 2)
        rebuilt = self.out / '3_bridge/files_test/Demo.apk'
        self.assertEqual(rebuilt.read_bytes(), expected.read_bytes())
        with zipfile.ZipFile(rebuilt) as z:
            self.assertEqual(z.read('classes.dex'), self.target)
            self.assertEqual(z.read('res/raw/demo'), b'invented resource')
            self.assertEqual(z.read('AndroidManifest.xml'), b'invented manifest')
        with zipfile.ZipFile(apk) as z:
            self.assertNotIn('classes.dex', z.namelist())

    def test_wrong_reference_stock_is_rejected_before_output(self):
        (self.stock / 'lib/libtest.so').write_bytes(b'wrong car')
        with self.assertRaisesRegex(ValueError, 'exact reference stock'):
            self.rebuild()
        self.assertFalse(self.out.exists())

    def test_output_hash_mismatch_leaves_no_build_directory(self):
        self.manifest.write_text(self.manifest.read_text().replace(md5(self.target), '0' * 32))
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.rebuild()
        self.assertFalse(self.out.exists())

    def test_manifest_cannot_escape_patches(self):
        self.manifest.write_text(self.manifest.read_text().replace('test/libtest.lpd', '../outside.lpd'))
        with self.assertRaisesRegex(ValueError, 'Unsafe manifest path'):
            self.rebuild()
        self.assertFalse(self.out.exists())

    def test_existing_build_never_overwritten(self):
        self.out.mkdir()
        (self.out / 'keep').write_text('keep')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.rebuild()
        self.assertEqual((self.out / 'keep').read_text(), 'keep')


class PortRegressionTests(unittest.TestCase):
    def test_framework_tool_failure_is_fatal(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, 'framework.odex').write_bytes(b'own fixture')
            result = subprocess.CompletedProcess([], 1, '', 'decode error')
            with patch.object(port.subprocess, 'run', return_value=result):
                with self.assertRaisesRegex(SystemExit, 'framework disassembly failed'):
                    port.framework_defs(td, td + '/out')

    def test_framework_success_without_classes_is_fatal(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, 'framework.odex').write_bytes(b'own fixture')
            result = subprocess.CompletedProcess([], 0, '', '')
            with patch.object(port.subprocess, 'run', return_value=result):
                with self.assertRaisesRegex(SystemExit, 'framework disassembly failed'):
                    port.framework_defs(td, td + '/out')

    def test_smali_assembly_matches_documented_gen5w_options(self):
        with patch.object(port, 'run') as run:
            port.assemble('input', 'output.dex')
        run.assert_called_once_with('smali', 'a', '-j', '1', '--api', '18', 'input', '-o', 'output.dex')

    def test_old_work_cannot_skip_new_firmware_analysis(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, 'stale.smali').write_text('old firmware')
            args = [sys.executable, str(ROOT / 'tools/port.py'), '--work', td]
            for key in ('variant', 'prefix', 'name', 'new-stock', 'new-fw', 'ref-stock', 'ref-fw', 'ref-builds', 'out-builds'):
                args += ['--' + key, {'variant': 'k7pe_kr', 'prefix': 'TEST.KOR.'}.get(key, 'unused')]
            r = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn('work directory must be empty', r.stderr)


if __name__ == '__main__':
    unittest.main()
