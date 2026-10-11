#!/usr/bin/env bash
set -euo pipefail
# Build a local-only accessibility probe using the Android SDK; no network dependencies.
[[ $# == 3 ]] || { echo "Usage: $0 ANDROID_SDK JAVA_HOME OUTPUT_DIRECTORY" >&2; exit 2; }
sdk="$1"
java_home="$2"
out="$3"
root="$(cd "$(dirname "$0")/.." && pwd)"
tools="$sdk/build-tools/36.0.0"
android="$sdk/platforms/android-37.0/android.jar"
[[ ! -e "$out" ]] || { echo "Output directory already exists" >&2; exit 1; }
mkdir -p "$out/classes" "$out/dex"
"$java_home/bin/javac" -source 8 -target 8 -classpath "$android" -d "$out/classes" "$root/tooling/ui-probe/src/org/maxresearch/probe/Probe.java"
JAVA_HOME="$java_home" "$tools/d8" --lib "$android" --min-api 26 --output "$out/dex" "$out/classes/org/maxresearch/probe/Probe.class"
"$tools/aapt2" link -I "$android" --manifest "$root/tooling/ui-probe/AndroidManifest.xml" -o "$out/probe-unsigned.apk"
python3 - "$out" <<'PY'
import pathlib,sys,zipfile
root=pathlib.Path(sys.argv[1])
with zipfile.ZipFile(root/'probe-unsigned.apk','a') as apk:
    apk.write(root/'dex/classes.dex','classes.dex')
PY
"$java_home/bin/keytool" -genkeypair -keystore "$out/local-test.keystore" -storepass local-test-only -keypass local-test-only -alias probe -keyalg RSA -validity 30 -dname 'CN=Local Research Probe' >/dev/null 2>&1
JAVA_HOME="$java_home" "$tools/apksigner" sign --ks "$out/local-test.keystore" --ks-pass pass:local-test-only --out "$out/probe.apk" "$out/probe-unsigned.apk"
JAVA_HOME="$java_home" "$tools/apksigner" verify "$out/probe.apk"
echo "Built $out/probe.apk"
