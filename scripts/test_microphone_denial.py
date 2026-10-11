#!/usr/bin/env python3
"""Test microphone refusal in an already selected test chat without granting audio access."""
import argparse
import json
import pathlib
import time
import xml.etree.ElementTree as ET
from run_max_runtime import Runner, PACKAGE, selector_node, RestoreFailed

PERMISSION = 'android.permission.RECORD_AUDIO'

def run(runner, expected_recipient):
    runner.current_dir = runner.output
    root = ET.fromstring(runner.ui('preconditions'))
    headers = [n for n in root.iter('node') if n.get('resource-id') == PACKAGE + ':id/oneme_toolbar_title'
               and n.get('text') == expected_recipient]
    if len(headers) != 1:
        raise RuntimeError('The explicitly selected test recipient is not the current chat')
    # This build exposes the empty input's "Message" hint as accessibility text.
    drafts = [n for n in root.iter('node') if n.get('resource-id') == PACKAGE + ':id/oneme_message_input_edit_text']
    if len(drafts) != 1 or drafts[0].get('text') not in {'', 'Message'}:
        raise RuntimeError('An empty message input is required')
    if runner.baseline['grants'][PERMISSION]['granted']:
        raise RuntimeError('Microphone permission must already be denied; this test never grants it')
    runner.emu('avd', 'snapshot', 'save', 'max-microphone-denial-baseline')
    def action():
        runner.adb('shell', 'pm', 'revoke', PACKAGE, PERMISSION)
        runner.adb('shell', 'pm', 'clear-permission-flags', PACKAGE, PERMISSION, 'user-set', 'user-fixed')
        runner.launch()
        xml = runner.ui('before-press')
        current = ET.fromstring(xml)
        if not any(n.get('resource-id') == PACKAGE + ':id/oneme_toolbar_title' and n.get('text') == expected_recipient
                   for n in current.iter('node')):
            raise RuntimeError('The current chat changed after permission preparation')
        if runner.state('immediately-before-press')['grants'][PERMISSION]['granted']:
            raise RuntimeError('Microphone unexpectedly granted; no press performed')
        node, (x, y) = selector_node(xml, PACKAGE + ':id/oneme_message_input_right_outer_icon')
        if node.get('content-desc') != 'Record voice message' or node.get('package') != PACKAGE:
            raise RuntimeError('Expected voice entry control was not present')
        # This app handles touch on a control reporting clickable=false. Bounds are derived
        # only after exact ID, package, enabled state and action description are verified.
        runner.events.append({'action': 'hold_voice_entry_with_microphone_denied', 'duration_ms': 900})
        runner.adb('shell', 'input', 'swipe', str(x), str(y), str(x), str(y), '900')
        time.sleep(1)
        dialog = ET.fromstring(runner.ui('microphone-system-prompt'))
        messages = [n.get('text', '') for n in dialog.iter('node')
                    if n.get('resource-id', '').endswith(':id/permission_message')]
        if len(messages) != 1 or 'record audio' not in messages[0].lower():
            raise RuntimeError('Expected microphone system prompt was not observed')
        runner.deny_dialog()
        time.sleep(1)
        after = runner.state('denied-result')
        if after['grants'][PERMISSION]['granted']:
            raise RuntimeError('Microphone permission unexpectedly granted')
        fallback = ET.fromstring(runner.ui('microphone-fallback'))
        texts = [n.get('text', '') for n in fallback.iter('node')]
        explanation = [t for t in texts if 'microphone' in t.lower()]
        field, _ = selector_node(ET.tostring(fallback, encoding='unicode'), PACKAGE + ':id/oneme_message_input_edit_text')
        control, _ = selector_node(ET.tostring(fallback, encoding='unicode'), PACKAGE + ':id/oneme_message_input_right_outer_icon')
        if field.get('text') not in {'', 'Message'} or control.get('content-desc') != 'Record voice message':
            raise RuntimeError('The app did not return to the expected empty composer')
        runner.screenshot('microphone-fallback')
        return {'permission': PERMISSION, 'system_microphone_prompt_verified': True,
                'permission_denied_verified': True, 'returned_to_empty_composer_verified': True,
                'microphone_explanation_observed': bool(explanation),
                'audio_permission_granted_by_test': False, 'send_action_performed': False}
    restored = False
    try:
        runner.scenario('S05-microphone-denial', action)
    finally:
        runner.current_dir = runner.output
        runner.restore_snapshot('max-microphone-denial-baseline')
        restored = runner.state('final') == runner.baseline
        runner.write_results()
        path = runner.output / 'runtime-results.json'
        data = json.loads(path.read_text())
        data['permission_and_appops_modes_restored'] = restored
        path.write_text(json.dumps(data, indent=2) + '\n')
        if not restored:
            raise RestoreFailed('Microphone scenario baseline restoration failed')
    return 1 if any(x['status'] == 'failed' for x in runner.results) else 0

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--serial', required=True)
    parser.add_argument('--expected-avd', default='max-research')
    parser.add_argument('--adb', default='adb')
    parser.add_argument('--collection', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    parser.add_argument('--expected-recipient', required=True)
    args = parser.parse_args()
    args.permission_config = None
    args.observe_seconds = 15
    runner = Runner(args)
    raise SystemExit(run(runner, args.expected_recipient))

if __name__ == '__main__':
    main()
