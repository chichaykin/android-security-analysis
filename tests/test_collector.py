"""Exercise collector failures without connecting to a real device."""
import json
import os
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'scripts/pull_oneme_for_analysis.sh'
ADB = '''#!/usr/bin/env python3
import os, pathlib, sys
args = sys.argv[1:]
mode = os.environ['MOCK_MODE']
if args == ['devices']:
    print('List of devices attached')
    if mode != 'no-device': print('test-device\\tdevice')
    if mode == 'multiple': print('other-device\\tdevice')
elif args == ['version']:
    print('Android Debug Bridge version mock')
else:
    assert args[:2] == ['-s', 'test-device']
    args = args[2:]
    if args[:3] == ['shell', 'pm', 'path']:
        if mode != 'missing-package':
            print('package:/data/app/example/base.apk')
            print('package:/data/app/example/split_config.arm64_v8a.apk')
    elif args[0] == 'pull':
        if mode == 'pull-error': sys.exit(1)
        pathlib.Path(args[2]).write_bytes(b'mock APK ' + args[1].encode())
    elif args[:3] == ['shell', 'getprop', 'ro.build.fingerprint']: print('mock-build')
    elif args[:3] == ['shell', 'getprop', 'ro.build.version.release']: print('17')
    elif args[:3] == ['shell', 'dumpsys', 'package']:
        print('versionName=26.35.1')
        print('versionCode=6867 minSdk=26 targetSdk=37')
        print('installerPackageName=ru.vk.store')
    elif args[:3] == ['shell', 'cmd', 'appops']: print('CAMERA: foreground')
    else: sys.exit(9)
'''
SIGNER = '''#!/usr/bin/env python3
import os, sys
if sys.argv[1] == 'version': print('mock')
elif os.environ['MOCK_MODE'] == 'signature-error': sys.exit(1)
else: print('Signer #1 certificate SHA-256 digest: ' + 'a' * 64)
'''

class CollectorTests(unittest.TestCase):
    def run_collector(self, mode, serial=True):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            # Spaces in executable paths must work.
            adb = root / 'mock adb'
            signer = root / 'mock signer'
            adb.write_text(ADB)
            signer.write_text(SIGNER)
            adb.chmod(0o755)
            signer.chmod(0o755)
            output = root / 'result'
            args = ['bash', str(SCRIPT), '--output', str(output), '--adb', str(adb), '--apksigner', str(signer)]
            if serial: args += ['--serial', 'test-device']
            env = dict(os.environ, MOCK_MODE=mode)
            result = subprocess.run(args, env=env, capture_output=True, text=True)
            manifest = json.loads((output / 'collection-manifest.json').read_text()) if output.exists() else None
            leftovers = list(root.glob('.max-collection.*'))
            return result, manifest, leftovers

    def test_no_device(self):
        result, manifest, leftovers = self.run_collector('no-device')
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(manifest)
        self.assertFalse(leftovers)

    def test_multiple_devices_require_explicit_selection(self):
        result, manifest, _ = self.run_collector('multiple', serial=False)
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(manifest)
        result, manifest, _ = self.run_collector('multiple')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(manifest['apks']), 2)

    def test_missing_package(self):
        result, manifest, _ = self.run_collector('missing-package')
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(manifest)

    def test_split_apks(self):
        result, manifest, leftovers = self.run_collector('splits')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([x['name'] for x in manifest['apks']], ['base.apk', 'split_config.arm64_v8a.apk'])
        self.assertTrue(all(len(x['sha256']) == 64 for x in manifest['apks']))
        self.assertNotIn('serial', manifest)
        self.assertFalse(leftovers)

    def test_pull_failure_leaves_no_completed_output(self):
        result, manifest, leftovers = self.run_collector('pull-error')
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(manifest)
        self.assertFalse(leftovers)

    def test_invalid_signature_leaves_no_completed_output(self):
        result, manifest, leftovers = self.run_collector('signature-error')
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(manifest)
        self.assertFalse(leftovers)

if __name__ == '__main__':
    unittest.main()
