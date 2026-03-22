#!/usr/bin/env bash
set -euo pipefail

# Collects ru.oneme.app artifacts from a connected Android device into
# a timestamped folder under analysis_artifacts/.
#
# What it tries to collect:
# 1) Installed APKs (base + splits) via "pm path"
# 2) /data/data/ru.oneme.app (private app data) via:
#    - run-as (debuggable builds)
#    - su (rooted device)
#    - adb root + direct tar (userdebug/eng builds)
# 3) /sdcard/Android/data/ru.oneme.app (external app data)

PKG="ru.oneme.app"
ADB_DEFAULT="/Users/mikhail.chichaykin/Library/Android/sdk/platform-tools/adb"
ADB_BIN="${ADB_BIN:-$ADB_DEFAULT}"
ROOT_OUT_DIR="${1:-analysis_artifacts/device_pull}"
TS="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="${ROOT_OUT_DIR}/${PKG}_${TS}"

log() { printf '[*] %s\n' "$*"; }
warn() { printf '[!] %s\n' "$*"; }
err() { printf '[x] %s\n' "$*"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing command: $1"
    exit 1
  fi
}

if [[ ! -x "$ADB_BIN" ]]; then
  if command -v adb >/dev/null 2>&1; then
    ADB_BIN="$(command -v adb)"
  else
    err "adb not found. Set ADB_BIN or install platform-tools."
    exit 1
  fi
fi

require_cmd tar
require_cmd sed
require_cmd tr
require_cmd date

log "Using adb: $ADB_BIN"
"$ADB_BIN" start-server >/dev/null

DEVICE_LINE="$($ADB_BIN devices | sed -n '2p' || true)"
if [[ -z "${DEVICE_LINE// /}" ]]; then
  err "No device detected. Connect device and enable USB debugging."
  exit 1
fi

mkdir -p "$OUT_DIR" "$OUT_DIR/apk" "$OUT_DIR/data"

log "Output folder: $OUT_DIR"

# 1) Pull APK splits
log "Collecting APK paths from installed package: $PKG"
APK_PATHS="$($ADB_BIN shell pm path "$PKG" 2>/dev/null | tr -d '\r' | sed -n 's/^package://p')"
if [[ -z "${APK_PATHS// /}" ]]; then
  err "Package '$PKG' is not installed on the device."
  exit 1
fi

i=0
while IFS= read -r remote_apk; do
  [[ -z "$remote_apk" ]] && continue
  i=$((i + 1))
  local_name="$(basename "$remote_apk")"
  log "Pulling APK [$i]: $remote_apk"
  "$ADB_BIN" pull "$remote_apk" "$OUT_DIR/apk/$local_name" >/dev/null
  log "Saved: $OUT_DIR/apk/$local_name"
done <<< "$APK_PATHS"

# 2) Pull /data/data/ru.oneme.app
PRIVATE_TAR="$OUT_DIR/data/${PKG}_data.tar"
PRIVATE_METHOD=""

log "Trying private data via run-as"
if "$ADB_BIN" exec-out "run-as $PKG sh -c 'cd /data/data/$PKG && tar -cf - .'" > "$PRIVATE_TAR" 2>/dev/null; then
  PRIVATE_METHOD="run-as"
else
  rm -f "$PRIVATE_TAR"
fi

if [[ -z "$PRIVATE_METHOD" ]]; then
  log "Trying private data via su"
  if "$ADB_BIN" exec-out "su -c 'cd /data/data/$PKG && tar -cf - .'" > "$PRIVATE_TAR" 2>/dev/null; then
    PRIVATE_METHOD="su"
  else
    rm -f "$PRIVATE_TAR"
  fi
fi

if [[ -z "$PRIVATE_METHOD" ]]; then
  log "Trying private data via adb root"
  "$ADB_BIN" root >/dev/null 2>&1 || true
  sleep 1
  if "$ADB_BIN" exec-out "cd /data/data/$PKG && tar -cf - ." > "$PRIVATE_TAR" 2>/dev/null; then
    PRIVATE_METHOD="adb-root"
  else
    rm -f "$PRIVATE_TAR"
  fi
fi

if [[ -n "$PRIVATE_METHOD" ]]; then
  log "Private data dump succeeded via: $PRIVATE_METHOD"
  mkdir -p "$OUT_DIR/data/private"
  tar -xf "$PRIVATE_TAR" -C "$OUT_DIR/data/private" || warn "Could not extract private tar locally; raw tar kept"
else
  warn "Could not read /data/data/$PKG (expected on non-rooted production builds)."
fi

# 3) Pull external app data if present
EXT_DIR="/sdcard/Android/data/$PKG"
log "Trying external app data: $EXT_DIR"
if "$ADB_BIN" shell "[ -d '$EXT_DIR' ]" 2>/dev/null; then
  "$ADB_BIN" pull "$EXT_DIR" "$OUT_DIR/data/external" >/dev/null 2>&1 || warn "External data pull failed"
  log "External data saved (if available)"
else
  warn "External app data folder not found"
fi

# Metadata for traceability
{
  echo "package=$PKG"
  echo "collected_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "adb_bin=$ADB_BIN"
  echo "private_data_method=${PRIVATE_METHOD:-none}"
  echo "device_serial=$($ADB_BIN get-serialno 2>/dev/null || true)"
  echo "device_model=$($ADB_BIN shell getprop ro.product.model 2>/dev/null | tr -d '\r' || true)"
  echo "android_release=$($ADB_BIN shell getprop ro.build.version.release 2>/dev/null | tr -d '\r' || true)"
} > "$OUT_DIR/collection_info.txt"

log "Done. Collected artifacts are in: $OUT_DIR"
log "Tip: compare APK hash with 'shasum -a 256 $OUT_DIR/apk/*.apk'"
