"""Test runtime guardrails, exact selectors and payload-free PCAP metadata."""
import argparse
import pathlib
import struct
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from run_max_runtime import Runner, Blocked, permission_state, selector_node
from pcap_metadata import summarize, visible_tls_sni
from test_microphone_denial import run as run_microphone_denial

class RuntimeTests(unittest.TestCase):
    def test_microphone_test_rejects_granted_permission_before_snapshot(self):
        runner = mock.Mock()
        runner.output = pathlib.Path('/unused')
        runner.ui.return_value = '<hierarchy><node resource-id="ru.oneme.app:id/oneme_toolbar_title" text="Synthetic recipient"/><node resource-id="ru.oneme.app:id/oneme_message_input_edit_text" text="Message"/></hierarchy>'
        runner.baseline = {'grants': {'android.permission.RECORD_AUDIO': {'granted': True}}}
        with self.assertRaisesRegex(RuntimeError, 'must already be denied'):
            run_microphone_denial(runner, 'Synthetic recipient')
        runner.emu.assert_not_called()
        runner.adb.assert_not_called()

    def test_microphone_test_rejects_wrong_recipient_before_snapshot(self):
        runner = mock.Mock()
        runner.output = pathlib.Path('/unused')
        runner.ui.return_value = '<hierarchy><node resource-id="ru.oneme.app:id/oneme_toolbar_title" text="Different recipient"/></hierarchy>'
        with self.assertRaisesRegex(RuntimeError, 'not the current chat'):
            run_microphone_denial(runner, 'Synthetic recipient')
        runner.emu.assert_not_called()
        runner.adb.assert_not_called()

    def test_physical_device_is_rejected_before_adb(self):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(serial='physical-device', output=pathlib.Path(directory)/'out', adb='must-not-execute')
            with mock.patch('run_max_runtime.subprocess.run') as command:
                with self.assertRaisesRegex(SystemExit, 'Physical devices'):
                    Runner(args)
                command.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_other_avd_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            args = argparse.Namespace(serial='emulator-5580', expected_avd='max-research', output=pathlib.Path(directory)/'out')
            with mock.patch.object(Runner, 'adb', return_value='1'), mock.patch.object(Runner, 'emu', return_value='personal-avd\nOK\n'):
                with self.assertRaisesRegex(SystemExit, 'AVD name differs'):
                    Runner(args)
            self.assertFalse(args.output.exists())

    def test_selector_ambiguity_is_blocked(self):
        xml = '<hierarchy><node resource-id="test" enabled="true" bounds="[0,0][10,10]"/><node resource-id="test" enabled="true" bounds="[20,0][30,10]"/></hierarchy>'
        with self.assertRaises(Blocked):
            selector_node(xml, 'test')

    def test_exact_text_selects_nearest_clickable_ancestor(self):
        xml = '<hierarchy><node package="ru.oneme.app" class="android.view.ViewGroup" enabled="true" clickable="true" bounds="[0,0][100,40]"><node package="ru.oneme.app" class="android.widget.TextView" text="Devices" enabled="true" clickable="false" bounds="[10,10][60,30]"/></node></hierarchy>'
        node, point = selector_node(xml, {'package':'ru.oneme.app', 'class':'android.widget.TextView', 'text':'Devices', 'click_parent':True})
        self.assertEqual(point, (50,20))
        self.assertEqual(node.get('class'), 'android.view.ViewGroup')
        with self.assertRaises(Blocked):
            selector_node(xml.replace('text="Devices"','text="Other"'), {'package':'ru.oneme.app','class':'android.widget.TextView','text':'Devices'})

    def test_unapproved_text_action_is_rejected(self):
        runner = object.__new__(Runner)
        runner.config = {'camera': {'route': [{'package':'ru.oneme.app','class':'android.widget.Button','text':'Send'}], 'allowed_marker':'a','denied_marker':'d'}}
        with self.assertRaisesRegex(Blocked, 'non-transmitting'):
            runner.reviewed_route('camera')

    def test_missing_or_invalid_selector_is_blocked(self):
        with self.assertRaises(Blocked):
            selector_node('<hierarchy/>', 'missing')
        with self.assertRaises(Blocked):
            selector_node('<hierarchy><node resource-id="test" enabled="true" bounds="[10,0][0,10]"/></hierarchy>', 'test')

    def test_permission_flags_preserved_but_access_times_ignored(self):
        dump = 'runtime permissions:\n android.permission.CAMERA: granted=false, flags=[ USER_SET|USER_FIXED]\nQueries:\n private-package-details'
        one = permission_state(dump, 'Uid mode: CAMERA: ignore\nWAKE_LOCK: allow; time=10s ago\n')
        two = permission_state(dump, 'Uid mode: CAMERA: ignore\nWAKE_LOCK: allow; time=20s ago\n')
        self.assertEqual(one, two)
        self.assertEqual(one['grants']['android.permission.CAMERA']['flags'], ' USER_SET|USER_FIXED')
        self.assertNotIn('private-package-details', str(one))
        changed = permission_state(dump.replace('granted=false', 'granted=true'), 'Uid mode: CAMERA: ignore\nWAKE_LOCK: allow\n')
        self.assertNotEqual(one, changed)

    def test_authentication_blocks_before_permission_mutation(self):
        runner = object.__new__(Runner)
        runner.state = mock.Mock(return_value={'grants': {}})
        runner.ui = mock.Mock(return_value='<hierarchy><node resource-id="ru.oneme.app:id/oneme_login_phone_edit_text"/></hierarchy>')
        runner.adb = mock.Mock()
        runner.emu = mock.Mock()
        with self.assertRaisesRegex(Blocked, 'authentication'):
            runner.permission_scenario('camera', 'deny')
        runner.adb.assert_not_called()
        runner.emu.assert_not_called()

    def test_unreviewed_route_blocks_before_permission_mutation(self):
        runner = object.__new__(Runner)
        runner.config = {'camera': {'route': ['ru.oneme.app:id/send_button'],
                                    'allowed_marker': 'allowed', 'denied_marker': 'denied'}}
        runner.state = mock.Mock(return_value={'grants': {'android.permission.CAMERA': {}}})
        runner.ui = mock.Mock(return_value='<hierarchy/>')
        runner.adb = mock.Mock()
        runner.emu = mock.Mock()
        with self.assertRaisesRegex(Blocked, 'transmission'):
            runner.permission_scenario('camera', 'deny')
        runner.adb.assert_not_called()
        runner.emu.assert_not_called()

    def test_snapshot_waits_for_package_service(self):
        runner = object.__new__(Runner)
        runner.emu = mock.Mock()
        runner.adb = mock.Mock(side_effect=['', '1', '', '', '1', 'package:base.apk'])
        with mock.patch('run_max_runtime.time.sleep'):
            runner.restore_snapshot('test-baseline')
        self.assertEqual(runner.adb.call_count, 6)
        runner.emu.assert_called_once_with('avd', 'snapshot', 'load', 'test-baseline')

class PcapTests(unittest.TestCase):
    def test_visible_sni_and_truncation(self):
        name = b'example.test'
        entry = b'\x00' + len(name).to_bytes(2, 'big') + name
        value = len(entry).to_bytes(2, 'big') + entry
        extension = b'\x00\x00' + len(value).to_bytes(2, 'big') + value
        body = b'\x03\x03' + b'\x00'*32 + b'\x00\x00\x02\x13\x01\x01\x00' + len(extension).to_bytes(2, 'big') + extension
        hello = b'\x01' + len(body).to_bytes(3, 'big') + body
        packet = b'\x16\x03\x01' + len(hello).to_bytes(2, 'big') + hello
        self.assertEqual(visible_tls_sni(packet), 'example.test')
        self.assertIsNone(visible_tls_sni(packet[:-1]))
        self.assertIsNone(visible_tls_sni(b'not TLS'))

    @staticmethod
    def capture(payload):
        ethernet = b'\x00'*12 + b'\x08\x00'
        ip = bytearray(20)
        ip[0] = 0x45
        ip[9] = 6
        ip[12:16] = b'\x0a\x00\x02\x0f'
        ip[16:20] = b'\xcb\x00\x71\x05'
        tcp = bytearray(20)
        tcp[:4] = struct.pack('!HH', 12345, 80)
        tcp[12] = 0x50
        packet = ethernet + bytes(ip) + bytes(tcp) + payload
        header = struct.pack('<IHHIIII', 0xa1b2c3d4, 2, 4, 0, 0, 65535, 1)
        return header + struct.pack('<IIII', 100, 10, len(packet), len(packet)) + packet

    def test_no_payload_or_token_is_exported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'test.pcap'
            path.write_bytes(self.capture(b'GET /private?token=synthetic-secret HTTP/1.1\r\nHost: example.test\r\nCookie: sensitive-value\r\n\r\n'))
            result = summarize(path)
            self.assertEqual(result['packet_count'], 1)
            self.assertEqual(result['http_request_signatures'], [{'host':'example.test','packets':1}])
            self.assertNotIn('synthetic-secret', str(result))
            self.assertNotIn('sensitive-value', str(result))
            self.assertIn('not UID-filtered', result['capture_scope'])

    def test_truncated_capture_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)/'test.pcap'
            path.write_bytes(self.capture(b'test')[:-1])
            with self.assertRaisesRegex(ValueError, 'Truncated'):
                summarize(path)

if __name__ == '__main__':
    unittest.main()
