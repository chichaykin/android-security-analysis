#!/usr/bin/env python3
"""Extract version-specific bytecode excerpts for the reviewed MAX build."""
import argparse
import hashlib
import pathlib
import subprocess

METHODS = [
    ('E04A', 'Tracker provider setter', 'com.my.tracker.MyTrackerConfig',
     'setInstalledPackagesProvider(Le5c;)Lcom/my/tracker/MyTrackerConfig;', [(1, 20)]),
    ('E04B', 'Disk roots and conditional sample scheduling', 'ru.ok.tracer.disk.usage.DiskUsageWorker',
     'd()Loz9;', [(61, 120), (156, 195)]),
    ('E04C', 'Package query', 'n16', 'a(Ld55;)Ljava/lang/Object;', [(64, 80)]),
    ('E04D', 'Fixed logcat command', 'bi6', 'C(Ljava/lang/Object;)Ljava/lang/Object;', [(29, 51)]),
    ('E04E', 'JavaScript bridges', 'pil', 'd(Ljava/lang/Object;)Ljava/lang/Object;', [(698, 738)]),
    ('E04G', 'FCM coroutine dispatch', 'one.me.sdk.vendor.push.FcmMessagingService',
     'd(Lkxf;)V', [(271, 291)]),
    ('E04F', 'Sample upload worker scheduling', 'rug',
     'q(Landroid/content/Context;Lc0c;Ljava/io/File;Ljava/lang/String;Ljava/lang/Long;Ljava/util/Map;I)V',
     [(234, 248), (286, 302)]),
]
EXPECTED_BASE_SHA256 = 'a9a76d5b15f1ed13f0fd368ebbc2cf0bb3c8567d15e4d229944865358d31c5a9'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', required=True, type=pathlib.Path)
    parser.add_argument('--apkanalyzer', required=True)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    digest = hashlib.sha256(args.apk.read_bytes()).hexdigest()
    if digest != EXPECTED_BASE_SHA256:
        raise SystemExit('This evidence recipe applies only to the reviewed 26.35.1 base APK')
    parts = ['# Bytecode evidence excerpts\n',
             f'Base APK SHA-256: `{digest}`.\n',
             'Generated with Android SDK apkanalyzer. Names are raw DEX names; JADX may display obfuscated classes under `defpackage`. Each range refers to lines in the complete method disassembly. Excerpts omit surrounding instructions and do not establish runtime execution.\n']
    for evidence_id, title, cls, method, ranges in METHODS:
        result = subprocess.run([args.apkanalyzer, 'dex', 'code', '--class', cls,
                                 '--method', method, str(args.apk)],
                                check=True, text=True, capture_output=True)
        text = result.stdout
        if not text.startswith('.method') or '.end method' not in text:
            raise SystemExit(f'Missing disassembly: {cls}.{method}')
        parts += [f'## {evidence_id}: {title}\n', f'Class: `{cls}`\n\nMethod: `{method}`\n',
                  f'Full method disassembly SHA-256: `{hashlib.sha256(text.encode()).hexdigest()}`\n']
        lines = text.splitlines()
        for start, end in ranges:
            end = min(end, len(lines))
            parts += [f'Disassembly lines {start}–{end}:\n',
                      '```smali\n' + '\n'.join(lines[start-1:end]) + '\n```\n']
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text('\n'.join(parts))
    print(f'Wrote {len(METHODS)} bytecode evidence sections')

if __name__ == '__main__':
    main()
