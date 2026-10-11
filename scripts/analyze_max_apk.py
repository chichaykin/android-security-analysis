#!/usr/bin/env python3
"""Produce a redacted, reproducible manifest evidence summary for MAX."""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

ANDROID = '{http://schemas.android.com/apk/res/android}'
INDICATORS = (
    'InstalledPackagesProvider', 'getInstalledPackages', 'DiskUsageWorker',
    'FcmMessagingService', 'RustoreMessagingService', 'PackageInstaller',
    'DexClassLoader', 'addJavascriptInterface', 'MediaProjection',
)

def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection', required=True, type=pathlib.Path)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    parser.add_argument('--apkanalyzer', required=True)
    parser.add_argument('--aapt2', required=True)
    args = parser.parse_args()
    metadata = json.loads((args.collection / 'collection-manifest.json').read_text())
    base = args.collection / 'apk' / 'base.apk'
    digest = hashlib.sha256(base.read_bytes()).hexdigest()
    if digest != next(item['sha256'] for item in metadata['apks'] if item['name'] == 'base.apk'):
        raise SystemExit('Base APK hash differs from collection manifest')
    manifest_xml = run(args.apkanalyzer, 'manifest', 'print', str(base))
    root = ET.fromstring(manifest_xml)
    app = root.find('application')
    if root.attrib['package'] != metadata['package']:
        raise SystemExit('Package name differs from collection manifest')
    permissions = sorted({
        element.get(ANDROID + 'name'):
            element.get(ANDROID + 'maxSdkVersion')
        for element in root if element.tag.startswith('uses-permission')
    }.items())
    components = []
    for kind in ('activity', 'activity-alias', 'service', 'receiver', 'provider'):
        for element in app.findall(kind):
            if element.get(ANDROID + 'exported') != 'true':
                continue
            filters = []
            for intent_filter in element.findall('intent-filter'):
                filters.append({
                    'actions': [x.get(ANDROID + 'name') for x in intent_filter.findall('action')],
                    'categories': [x.get(ANDROID + 'name') for x in intent_filter.findall('category')],
                    'data': [{key.removeprefix(ANDROID): value for key, value in x.attrib.items()}
                             for x in intent_filter.findall('data')],
                })
            components.append({
                'type': kind,
                'name': element.get(ANDROID + 'name'),
                'required_permission': element.get(ANDROID + 'permission'),
                'intent_filters': filters,
            })
    network = run(args.aapt2, 'dump', 'xmltree', '--file',
                  'res/xml/network_security_config.xml', str(base))
    network_xml = run(args.apkanalyzer, 'resources', 'xml', '--file',
                      '/res/xml/network_security_config.xml', str(base))
    policy = ET.fromstring(network_xml)
    domain_rules = []
    def read_rules(config, inherited):
        allowed = config.get('cleartextTrafficPermitted', inherited)
        for domain in config.findall('domain'):
            domain_rules.append({
                'domain': domain.text.strip(),
                'include_subdomains': domain.get('includeSubdomains', 'false') == 'true',
                'cleartext_permitted': allowed == 'true',
            })
        for child in config.findall('domain-config'):
            read_rules(child, allowed)
    base_config = policy.find('base-config')
    default = 'false' if metadata['target_sdk'] >= 28 else 'true'
    if base_config is not None:
        default = base_config.get('cleartextTrafficPermitted', default)
    for config in policy.findall('domain-config'):
        read_rules(config, default)
    cleartext_domains = [rule['domain'] for rule in domain_rules if rule['cleartext_permitted']]
    indicators = {name: {} for name in INDICATORS}
    with zipfile.ZipFile(base) as archive:
        for name in archive.namelist():
            if name.endswith('.dex'):
                data = archive.read(name)
                for indicator in INDICATORS:
                    indicators[indicator][name] = data.count(indicator.encode())
    summary = {
        'schema_version': 1,
        'base_apk_sha256': digest,
        'package': metadata['package'],
        'version_name': metadata['version_name'],
        'version_code': metadata['version_code'],
        'target_sdk': metadata['target_sdk'],
        'manifest_permissions': [
            {'name': name, 'max_sdk': limit} for name, limit in permissions
        ],
        'exported_components': components,
        'cleartext_permitted_domains': cleartext_domains,
        'network_domain_rules': domain_rules,
        'network_xmltree_sha256': hashlib.sha256(network.encode()).hexdigest(),
        'dex_string_hits': indicators,
        'interpretation': {
            'manifest_permissions': 'Declarations, not evidence of grant or use.',
            'exported_components': 'Manifest exposure, not an exploitability finding.',
            'cleartext_permitted_domains': 'Policy allowance, not observed cleartext traffic.',
            'dex_string_hits': 'Raw UTF-8 byte counts, not proof of reachability or execution.',
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + '\n')
    args.output.with_suffix('.network-policy.xml').write_text(network_xml)
    print(f'Wrote {args.output} for {digest}')

if __name__ == '__main__':
    try:
        main()
    except (FileNotFoundError, subprocess.CalledProcessError, ET.ParseError, KeyError) as error:
        print(f'Analysis failed: {error}', file=sys.stderr)
        raise SystemExit(1)
