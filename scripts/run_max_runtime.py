#!/usr/bin/env python3
"""Run bounded MAX scenarios exclusively on an explicitly named research emulator."""
import argparse
import datetime
import hashlib
import json
import pathlib
import re
import shlex
import subprocess
import time
import xml.etree.ElementTree as ET
from pcap_metadata import summarize

PACKAGE = 'ru.oneme.app'
ACTIVITY = PACKAGE + '/one.me.android.MainActivity'
PROBE = 'org.maxresearch.probe/.Probe'
LOGIN_MARKER = PACKAGE + ':id/oneme_login_phone_edit_text'
PERMISSIONS = {'camera': 'android.permission.CAMERA', 'microphone': 'android.permission.RECORD_AUDIO',
               'media': 'android.permission.READ_MEDIA_IMAGES'}
DENY_IDS = ['com.android.permissioncontroller:id/permission_deny_button',
            'com.google.android.permissioncontroller:id/permission_deny_button']

class Blocked(Exception):
    pass

class RestoreFailed(Exception):
    pass

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def permission_state(package_dump, appops):
    if 'runtime permissions:' not in package_dump:
        raise ValueError('Runtime permission state unavailable')
    section = package_dump.split('runtime permissions:', 1)[1]
    section = re.split(r'\n\s*(?:disabledComponents:|enabledComponents:|Queries:|Package Changes:)', section)[0]
    grants = {name: {'granted': value == 'true', 'flags': flags}
              for name, value, flags in re.findall(r'(android\.permission\.[A-Z_]+): granted=(true|false), flags=\[([^\]]*)\]', section)}
    if not grants:
        raise ValueError('No runtime permissions parsed')
    modes = sorted(re.findall(r'^(?:Uid mode: )?([A-Z_]+): ([a-z_]+)', appops, re.M))
    if not modes:
        raise ValueError('AppOps modes unavailable')
    return {'grants': grants, 'appops_modes': modes}

def selector_node(xml, resource_id):
    root = ET.fromstring(xml)
    criteria = {'resource-id': resource_id} if isinstance(resource_id, str) else resource_id
    attributes = {key: value for key, value in criteria.items() if key != 'click_parent'}
    matches = [node for node in root.iter('node')
               if all(node.get(key) == value for key, value in attributes.items())
               and node.get('enabled') == 'true']
    if len(matches) != 1:
        raise Blocked('Expected exactly one enabled element: ' + str(resource_id))
    node = matches[0]
    if criteria.get('click_parent'):
        parents = {child: parent for parent in root.iter() for child in parent}
        while node.get('clickable') != 'true' and node in parents:
            node = parents[node]
        if node.get('enabled') != 'true' or node.get('package') != attributes.get('package'):
            raise Blocked('Clickable ancestor is not an enabled element in the selected package')
    bounds = re.fullmatch(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', node.get('bounds', ''))
    if not bounds:
        raise Blocked('Invalid element bounds')
    left, top, right, bottom = map(int, bounds.groups())
    if right <= left or bottom <= top:
        raise Blocked('Element has no tappable area')
    return node, ((left + right) // 2, (top + bottom) // 2)

class Runner:
    def __init__(self, args):
        self.args = args
        self.events = []
        self.results = []
        self.output = args.output.resolve()
        if not re.fullmatch(r'emulator-\d+', args.serial):
            raise SystemExit('Physical devices are prohibited by this runner')
        if self.output.exists():
            raise SystemExit('Output directory already exists')
        if self.adb('shell', 'getprop', 'ro.kernel.qemu').strip() != '1':
            raise SystemExit('Target did not identify as an emulator')
        name = self.emu('avd', 'name').splitlines()[0].strip()
        if name != args.expected_avd:
            raise SystemExit('Target AVD name differs from the explicitly selected research AVD')
        self.output.mkdir(parents=True)
        self.collection = json.loads((args.collection / 'collection-manifest.json').read_text())
        dump = self.adb('shell', 'dumpsys', 'package', PACKAGE)
        version = re.search(r'versionName=([^\s]+)', dump)
        code = re.search(r'versionCode=(\d+)', dump)
        if not version or not code or version.group(1) != self.collection['version_name'] or int(code.group(1)) != self.collection['version_code']:
            raise SystemExit('Installed version differs from the recorded collection')
        expected = {item['name']: item['sha256'] for item in self.collection['apks']}
        observed = {}
        for line in self.adb('shell', 'pm', 'path', PACKAGE).splitlines():
            if not line.startswith('package:'):
                continue
            remote = line[len('package:'):].strip()
            digest = self.adb('shell', 'sha256sum ' + shlex.quote(remote)).split()[0]
            observed[pathlib.PurePosixPath(remote).name] = digest
        if observed != expected:
            raise SystemExit('Installed APK hashes differ from the collection')
        uid_match = re.search(r'(?:userId|appId)=(\d+)', dump)
        if not uid_match:
            raise SystemExit('Application UID unavailable')
        current_user = int(self.adb('shell', 'am', 'get-current-user').strip())
        self.uid = str(current_user * 100000 + int(uid_match.group(1)))
        self.environment = {
            'type': 'Isolated research emulator; separate from the personal Pixel',
            'android_release': self.adb('shell', 'getprop', 'ro.build.version.release').strip(),
            'api_level': self.adb('shell', 'getprop', 'ro.build.version.sdk').strip(),
            'android_build_fingerprint': self.adb('shell', 'getprop', 'ro.build.fingerprint').strip(),
            'wifi_enabled_setting': self.adb('shell', 'settings', 'get', 'global', 'wifi_on').strip(),
        }
        self.baseline = self.state('baseline')
        self.config = json.loads(args.permission_config.read_text()) if args.permission_config else {}
        self.current_dir = None
        self.capture_active = False

    def adb(self, *args, timeout=30):
        result = subprocess.run([self.args.adb, '-s', self.args.serial, *args],
                                check=True, capture_output=True, text=True, timeout=timeout)
        return result.stdout.replace('\r', '')

    def emu(self, *args):
        result = self.adb('emu', *args)
        if 'KO:' in result or 'OK' not in result:
            raise RuntimeError('Emulator console rejected command: ' + ' '.join(args))
        return result

    def restore_snapshot(self, name):
        self.emu('avd', 'snapshot', 'load', name)
        # The console acknowledges a load before ADB and package services reconnect.
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                self.adb('wait-for-device', timeout=5)
                if self.adb('shell', 'getprop', 'sys.boot_completed', timeout=5).strip() == '1':
                    if 'package:' in self.adb('shell', 'pm', 'path', PACKAGE, timeout=5):
                        return
            except subprocess.SubprocessError:
                pass
            time.sleep(0.5)
        raise RestoreFailed('Emulator package service did not reconnect after snapshot load')

    def state(self, label):
        package = self.adb('shell', 'dumpsys', 'package', PACKAGE)
        appops = self.adb('shell', 'cmd', 'appops', 'get', PACKAGE)
        directory = self.current_dir if getattr(self, 'current_dir', None) else self.output
        (directory / (label + '.package.private.txt')).write_text(package)
        (directory / (label + '.appops.private.txt')).write_text(appops)
        return permission_state(package, appops)

    def ui(self, label):
        result = self.adb('shell', 'am', 'instrument', '-w', PROBE, timeout=20)
        match = re.search(r'^INSTRUMENTATION_RESULT: hierarchy=(.*)$', result, re.M)
        if not match:
            raise Blocked('Accessibility probe could not read the current screen')
        xml = match.group(1)
        ET.fromstring(xml)
        (self.current_dir / (label + '.ui.private.xml')).write_text(xml + '\n')
        return xml

    def tap(self, resource_id):
        # Only explicit resource IDs from reviewed routes are accepted; never guess a coordinate.
        package_ok = (resource_id.get('package') == PACKAGE if isinstance(resource_id, dict) else
                      resource_id.startswith((PACKAGE + ':id/', 'com.android.permissioncontroller:id/', 'com.google.android.permissioncontroller:id/')))
        if not package_ok:
            raise Blocked('Selector belongs to an unapproved package')
        xml = self.ui('selector-' + str(len(self.events)))
        node, (x, y) = selector_node(xml, resource_id)
        if node.get('clickable') != 'true':
            raise Blocked('Selected element is not clickable')
        self.events.append({'at_utc': utc(), 'action': 'tap_resource', 'resource_id': resource_id})
        self.adb('shell', 'input', 'tap', str(x), str(y))
        time.sleep(1)

    def screenshot(self, label):
        result = subprocess.run([self.args.adb, '-s', self.args.serial, 'exec-out', 'screencap', '-p'],
                                check=True, capture_output=True, timeout=15)
        (self.current_dir / (label + '.screen.private.png')).write_bytes(result.stdout)

    def launch(self):
        output = self.adb('shell', 'am', 'start', '-W', '-n', ACTIVITY)
        (self.current_dir / 'launch.private.txt').write_text(output)
        if 'Status: ok' not in output:
            raise RuntimeError('Activity launch did not report success')
        metrics = {}
        for key in ('LaunchState', 'TotalTime', 'WaitTime'):
            match = re.search(r'^' + key + r': (.*)$', output, re.M)
            if match:
                metrics[key] = match.group(1)
        return metrics

    def deny_dialog(self):
        xml = self.ui('permission-dialog')
        for resource in DENY_IDS:
            try:
                selector_node(xml, resource)
            except Blocked:
                continue
            self.tap(resource)
            return
        raise Blocked('Expected system permission-denial button was not present')

    def reviewed_route(self, feature):
        route = self.config.get(feature)
        if not route or not route.get('route') or not route.get('denied_marker') or not route.get('allowed_marker'):
            raise Blocked('Feature route and allowed/denied assertions have not been reviewed: ' + feature)
        if not isinstance(route['route'], list):
            raise Blocked('Feature route must be a list of explicit selectors')
        if not isinstance(route.get('back_steps', 0), int) or not 0 <= route.get('back_steps', 0) <= 5:
            raise Blocked('Invalid reviewed back-navigation count')
        if not isinstance(route.get('request_route', []), list):
            raise Blocked('Permission request route must be a list')
        for key in ('companion_permissions', 'setup_grants'):
            if not isinstance(route.get(key, []), list) or any(p not in {
                    'android.permission.CAMERA', 'android.permission.READ_MEDIA_IMAGES',
                    'android.permission.READ_MEDIA_VIDEO', 'android.permission.READ_MEDIA_VISUAL_USER_SELECTED'}
                    for p in route.get(key, [])):
                raise Blocked('Unreviewed permission group or setup grant')
        for resource in route['route'] + route.get('request_route', []):
            if isinstance(resource, dict):
                if (resource.get('package') != PACKAGE or not resource.get('class') or
                    resource.get('text') not in {'Devices', 'Link device', 'Connect device', 'Sign in with QR code', 'Take photo', 'Upload from gallery', 'Allow access'} or
                    set(resource) - {'package', 'class', 'text', 'click_parent', 'resource-id'}):
                    raise Blocked('Text selector has not been approved as a non-transmitting entry action')
                continue
            if not isinstance(resource, str):
                raise Blocked('Invalid route selector')
            if not resource.startswith(PACKAGE + ':id/'):
                raise Blocked('Feature route contains an unapproved package')
            if any(word in resource.lower() for word in ('send', 'share', 'call', 'record', 'capture', 'publish', 'submit')):
                raise Blocked('Route contains a transmission or recording action requiring separate review')
        return route

    def feature_route(self, feature):
        route = self.reviewed_route(feature)
        for resource in route['route']:
            self.tap(resource)
        return route

    def permission_scenario(self, feature, mode):
        initial = self.state('before-permission')
        xml = self.ui('account-state')
        if LOGIN_MARKER in xml:
            raise Blocked('Test-account authentication is required before this feature scenario')
        reviewed = self.reviewed_route(feature)
        permission = PERMISSIONS[feature]
        permissions = [permission] + reviewed.get('companion_permissions', [])
        if any(p not in initial['grants'] for p in permissions + reviewed.get('setup_grants', [])):
            raise Blocked('Permission does not appear in the runtime baseline')
        # A full emulator snapshot preserves grants, flags and AppOps across mutations.
        snapshot = 'max-runtime-restore'
        self.emu('avd', 'snapshot', 'save', snapshot)
        try:
            for setup in reviewed.get('setup_grants', []):
                self.adb('shell', 'pm', 'grant', PACKAGE, setup)
            if mode == 'deny':
                for target in permissions:
                    self.adb('shell', 'pm', 'revoke', PACKAGE, target)
                    self.adb('shell', 'pm', 'clear-permission-flags', PACKAGE, target, 'user-set', 'user-fixed')
                self.adb('shell', 'am', 'force-stop', PACKAGE)
                self.launch()
                route = self.feature_route(feature)
                for selector in route.get('request_route', []):
                    self.tap(selector)
                self.deny_dialog()
            else:
                for target in permissions:
                    self.adb('shell', 'pm', 'grant', PACKAGE, target)
                self.adb('shell', 'am', 'force-stop', PACKAGE)
                self.launch()
                route = self.feature_route(feature)
                selector_node(self.ui('allowed-result'), route['allowed_marker'])
                for _ in range(route.get('back_steps', 0)):
                    self.adb('shell', 'input', 'keyevent', 'KEYCODE_BACK')
                    time.sleep(0.5)
                for target in permissions:
                    self.adb('shell', 'pm', 'revoke', PACKAGE, target)
                self.launch()
                self.feature_route(feature)
                for selector in route.get('request_route', []):
                    self.tap(selector)
                if any(resource in self.ui('after-revoke') for resource in DENY_IDS):
                    self.deny_dialog()
            after = self.state('denied-result')
            if any(after['grants'][p]['granted'] for p in permissions):
                raise RuntimeError('Permission remained granted after the denial/revocation scenario')
            selector_node(self.ui('denied-result'), route['denied_marker'])
            self.screenshot('denied-result')
            return {'permissions': permissions, 'setup_grants': reviewed.get('setup_grants', []),
                    'permission_denied_verified': True,
                    'expected_fallback_marker_verified': route['denied_marker']}
        finally:
            self.restore_snapshot(snapshot)
            if self.state('restored-permission') != initial:
                raise RestoreFailed('Snapshot restoration did not restore grants, flags and AppOps modes')

    def scenario(self, name, action):
        print('Running ' + name, flush=True)
        self.current_dir = self.output / name
        self.current_dir.mkdir()
        result = {'id': name, 'started_at_utc': utc()}
        pcap = self.current_dir / 'traffic.private.pcap'
        try:
            self.emu('network', 'capture', 'start', str(pcap))
            self.capture_active = True
            result['observations'] = action()
            result['status'] = 'passed'
        except Blocked as error:
            result.update(status='blocked', reason=str(error))
        except RestoreFailed:
            result.update(status='failed', reason='Permission restoration failed; further execution aborted')
            raise
        except (RuntimeError, ValueError, subprocess.SubprocessError) as error:
            result.update(status='failed', reason=str(error))
        finally:
            if self.capture_active:
                try:
                    self.emu('network', 'capture', 'stop')
                except Exception as error:
                    result.update(status='failed', reason='Capture stop failed: ' + str(error))
                self.capture_active = False
            if pcap.exists():
                try:
                    network = summarize(pcap)
                    (self.current_dir / 'network-metadata.json').write_text(json.dumps(network, indent=2) + '\n')
                    result['network_metadata'] = name + '/network-metadata.json'
                except ValueError as error:
                    result.update(status='failed', reason=str(error))
            else:
                result.update(status='failed', reason='No capture file produced')
            result['ended_at_utc'] = utc()
            self.results.append(result)
            print(name + ': ' + result['status'], flush=True)
            self.write_results()

    def control(self):
        self.adb('shell', 'am', 'force-stop', PACKAGE)
        self.adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        time.sleep(self.args.observe_seconds)
        present = bool(self.adb('shell', 'pidof', PACKAGE).strip()) if self.pid_exists() else False
        if present:
            raise RuntimeError('MAX process present during stopped-app control')
        return {'max_process_present': False, 'observation_seconds': self.args.observe_seconds}

    def pid_exists(self):
        try:
            return bool(self.adb('shell', 'pidof', PACKAGE).strip())
        except subprocess.CalledProcessError as error:
            if error.returncode == 1:
                return False
            raise

    def startup(self, cold):
        if cold:
            self.adb('shell', 'am', 'force-stop', PACKAGE)
        self.adb('logcat', '-c')
        metrics = self.launch()
        time.sleep(self.args.observe_seconds)
        if not self.pid_exists():
            raise RuntimeError('MAX process absent after the observation interval')
        xml = self.ui('startup-result')
        self.screenshot('startup-result')
        logs = self.adb('logcat', '-d', '--uid=' + self.uid)
        (self.current_dir / 'logcat.private.txt').write_text(logs)
        fatal_markers = logs.count('FATAL EXCEPTION')
        if fatal_markers:
            raise RuntimeError('Fatal exception marker in app-UID log during startup')
        return {'launch_metrics': metrics, 'max_process_present': True,
                'login_screen_present': LOGIN_MARKER in xml,
                'fatal_exception_markers_in_app_uid_log': fatal_markers,
                'observation_seconds': self.args.observe_seconds}

    def background(self):
        self.adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
        time.sleep(self.args.observe_seconds)
        return {'home_key_sent': True, 'max_process_present_after_interval': self.pid_exists(),
                'observation_seconds': self.args.observe_seconds}

    def write_results(self):
        summary = {'schema_version': 1, 'package': PACKAGE,
                   'version_name': self.collection['version_name'], 'version_code': self.collection['version_code'],
                   'base_apk_sha256': next(x['sha256'] for x in self.collection['apks'] if x['name'] == 'base.apk'),
                   'environment': self.environment,
                   'results': self.results, 'permission_baseline': self.baseline,
                   'transmission_policy': 'No message, contact, file, call or diagnostic submission actions are scripted.',
                   'network_limits': 'Whole-emulator WAN capture; no automatic app attribution or TLS decryption.'}
        (self.output / 'runtime-results.json').write_text(json.dumps(summary, indent=2) + '\n')
        (self.output / 'actions.private.json').write_text(json.dumps(self.events, indent=2) + '\n')

    def run(self):
        self.emu('avd', 'snapshot', 'save', 'max-run-baseline')
        try:
            self.adb('shell', 'am', 'force-stop', PACKAGE)
            self.adb('shell', 'input', 'keyevent', 'KEYCODE_HOME')
            if self.pid_exists():
                raise RuntimeError('MAX must be stopped before the control capture starts')
            self.scenario('S00-stopped-control', self.control)
            self.scenario('S01-cold-start', lambda: self.startup(True))
            self.scenario('S02-repeat-start', lambda: self.startup(False))
            self.scenario('S03-background', self.background)
            self.current_dir = self.output
            self.launch()
            for feature in PERMISSIONS:
                for mode in ('deny', 'revoke'):
                    self.scenario('S04-' + feature + '-' + mode,
                                  lambda feature=feature, mode=mode: self.permission_scenario(feature, mode))
        finally:
            self.current_dir = self.output
            restored = False
            try:
                self.restore_snapshot('max-run-baseline')
                restored = self.state('final') == self.baseline
            finally:
                self.write_results()
                path = self.output / 'runtime-results.json'
                result = json.loads(path.read_text())
                result['permission_and_appops_modes_restored'] = restored
                path.write_text(json.dumps(result, indent=2) + '\n')
            if not restored:
                raise RestoreFailed('Final permission state differs from baseline')
        return 1 if any(item['status'] == 'failed' for item in self.results) else 0

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--expected-avd', default='max-research')
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--collection', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    parser.add_argument('--permission-config', type=pathlib.Path)
    parser.add_argument('--observe-seconds', type=int, default=15)
    args = parser.parse_args()
    if not 5 <= args.observe_seconds <= 60:
        parser.error('Observation interval must be between 5 and 60 seconds')
    runner = Runner(args)
    raise SystemExit(runner.run())

if __name__ == '__main__':
    main()
