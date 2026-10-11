#!/usr/bin/env bash
set -euo pipefail

# Collect installed MAX APKs and build metadata. Do not read application data.
usage() {
  echo "Usage: $0 --serial DEVICE_SERIAL --output DIRECTORY [--adb PATH] [--apksigner PATH]" >&2
  exit 2
}
serial=""
output=""
adb_bin="${ADB_BIN:-adb}"
apksigner_bin="${APKSIGNER_BIN:-apksigner}"
while (($#)); do
  case "$1" in
    --serial) (($# >= 2)) || usage; serial="$2"; shift 2 ;;
    --output) (($# >= 2)) || usage; output="$2"; shift 2 ;;
    --adb) (($# >= 2)) || usage; adb_bin="$2"; shift 2 ;;
    --apksigner) (($# >= 2)) || usage; apksigner_bin="$2"; shift 2 ;;
    *) usage ;;
  esac
done
[[ -n "$serial" && -n "$output" ]] || usage
command -v "$adb_bin" >/dev/null || { echo "adb not found" >&2; exit 1; }
command -v "$apksigner_bin" >/dev/null || { echo "apksigner not found" >&2; exit 1; }
command -v python3 >/dev/null || { echo "python3 not found" >&2; exit 1; }
[[ ! -e "$output" ]] || { echo "Output already exists: $output" >&2; exit 1; }

# Require an explicit, currently connected device; never guess among devices.
devices="$("$adb_bin" devices)"
state="$(printf '%s\n' "$devices" | awk -v s="$serial" '$1==s {print $2}')"
[[ "$state" == device ]] || { echo "Selected device is not connected and authorized" >&2; exit 1; }
paths="$("$adb_bin" -s "$serial" shell pm path ru.oneme.app | tr -d '\r' | sed -n 's/^package://p')"
[[ -n "$paths" ]] || { echo "ru.oneme.app is not installed" >&2; exit 1; }

parent="$(dirname "$output")"
mkdir -p "$parent"
staging="$(mktemp -d "$parent/.max-collection.XXXXXXXX")"
trap 'rm -rf "$staging"' EXIT
mkdir -p "$staging/apk"
: > "$staging/apk-paths.txt"
while IFS= read -r remote; do
  [[ -n "$remote" ]] || continue
  name="$(basename "$remote")"
  [[ "$name" == *.apk && ! -e "$staging/apk/$name" ]] || { echo "Invalid or duplicate APK name" >&2; exit 1; }
  "$adb_bin" -s "$serial" pull "$remote" "$staging/apk/$name" >/dev/null
  [[ -s "$staging/apk/$name" ]] || { echo "APK pull returned an empty file" >&2; exit 1; }
  printf '%s\n' "$name" >> "$staging/apk-paths.txt"
done <<< "$paths"
[[ -s "$staging/apk-paths.txt" ]] || { echo "No APKs collected" >&2; exit 1; }

"$adb_bin" -s "$serial" shell getprop ro.build.fingerprint | tr -d '\r' > "$staging/android-build.txt"
"$adb_bin" -s "$serial" shell getprop ro.build.version.release | tr -d '\r' > "$staging/android-version.txt"
"$adb_bin" -s "$serial" shell dumpsys package ru.oneme.app > "$staging/package-dump.private.txt"
"$adb_bin" -s "$serial" shell cmd appops get ru.oneme.app > "$staging/appops-baseline.private.txt"
"$adb_bin" version > "$staging/adb-version.txt"
"$apksigner_bin" version > "$staging/apksigner-version.txt"
for file in "$staging"/apk/*.apk; do
  "$apksigner_bin" verify --print-certs "$file" > "${file%.apk}.signature.txt"
done
python3 - "$staging" <<'PY'
import datetime, hashlib, json, pathlib, re, sys
root = pathlib.Path(sys.argv[1])
dump = (root / 'package-dump.private.txt').read_text()
def field(pattern):
    match = re.search(pattern, dump)
    if not match:
        raise SystemExit(f'Missing package metadata: {pattern}')
    return match.group(1)
apks = []
for path in sorted((root / 'apk').glob('*.apk')):
    signature = path.with_suffix('.signature.txt').read_text()
    digest = re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)', signature)
    if not digest:
        raise SystemExit(f'Missing signer digest: {path.name}')
    apks.append({'name': path.name, 'size_bytes': path.stat().st_size,
                 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                 'signer_certificate_sha256': digest.group(1)})
manifest = {
    'schema_version': 1,
    'collected_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'package': 'ru.oneme.app',
    'version_name': field(r'versionName=([^\s]+)'),
    'version_code': int(field(r'versionCode=(\d+)')),
    'min_sdk': int(field(r'minSdk=(\d+)')),
    'target_sdk': int(field(r'targetSdk=(\d+)')),
    'installer_package': field(r'installerPackageName=([^\s]+)'),
    'android_release': (root / 'android-version.txt').read_text().strip(),
    'android_build': (root / 'android-build.txt').read_text().strip(),
    'apks': apks,
    'tools': {
        'adb': (root / 'adb-version.txt').read_text().splitlines()[0],
        'apksigner': (root / 'apksigner-version.txt').read_text().strip(),
    },
    'limits': 'Installed APKs only; no application data or behavioral evidence.'
}
(root / 'collection-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
PY
mv "$staging" "$output"
trap - EXIT
printf 'Collected %s APK(s) in %s\n' "$(wc -l < "$output/apk-paths.txt" | tr -d ' ')" "$output"
