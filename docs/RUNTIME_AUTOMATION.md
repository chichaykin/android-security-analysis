# Isolated runtime automation

The runtime runner accepts only an explicitly selected emulator whose AVD name matches `--expected-avd`. It verifies the installed package version and every APK SHA-256 against the collection manifest before running scenarios. It rejects physical serials before executing ADB. The personal Pixel remains outside this runner.

## Environment and setup

The completed runs used a fresh `max-research` AVD, the installed Android 17 ARM64 image `system-images;android-37.2;google_apis_ps16k;arm64-v8a`, and emulator 36.6.11. Its APK set is identical to the collected Pixel APKs; its account state, hardware, Android build and network environment are different. These observations must not be presented as personal-Pixel behavior.

Create a separate AVD and install all APKs with `adb -s EMULATOR_SERIAL install-multiple`. Never reuse an AVD containing personal accounts. The Android SDK, Java 21, Python 3 and the emulator console are required. Build and install the small accessibility probe only in the isolated emulator:

```bash
./scripts/build_ui_probe.sh /path/to/Android/sdk /path/to/java-home /private/tmp/max-ui-probe
adb -s emulator-5580 install /private/tmp/max-ui-probe/probe.apk
```

The probe reads the active accessibility tree. Its later version can also fill one explicitly selected, editable MAX field through `ACTION_SET_TEXT`, which was used for a separately authorized text-message action. It does not hook MAX code or bypass TLS. Android instrumentation runs the helper in its own package. Its output can contain account information, so the runner retains trees and screenshots privately. Build signing uses an ephemeral local test key that is unrelated to MAX's signer.

Disable emulator Wi-Fi and enable cellular data before this capture method. Android emulator console capture observes the guest WAN interface; Wi-Fi capture uses a different backend in recent emulator versions. See the [emulator console documentation](https://developer.android.com/studio/run/emulator-console) and [command-line reference](https://developer.android.com/studio/run/emulator-commandline).

```bash
adb -s emulator-5580 shell svc wifi disable
adb -s emulator-5580 shell svc data enable
python3 scripts/run_max_runtime.py \
  --serial emulator-5580 --expected-avd max-research \
  --adb /path/to/Android/sdk/platform-tools/adb \
  --collection /private/tmp/max-review-collection \
  --output /private/tmp/max-runtime-new-run --observe-seconds 15
```

Use a new output directory for every run. Signing into a user-supplied account designated for testing is a manual prerequisite for authenticated feature tests. The supplied account contained pre-existing conversations; it was not an empty synthetic account. Enter the number and verification code directly in the emulator, never in a research log or public artifact. The generic startup/permission runner submits no messages, contacts, files, calls or diagnostic reports. A separate user-authorized single text send was performed outside those routes; its recipient, text and screenshots remain private.

## Scenarios and assertions

| Scenario | Action and success criteria | Interpretation limits |
| --- | --- | --- |
| S00 | Force-stop MAX before capture; verify no main process after 15 seconds | Whole-guest control, not a zero-traffic guarantee |
| S01 | Force-stop, launch the explicit activity, observe 15 seconds, require process presence, readable UI and no `FATAL EXCEPTION` marker in app-UID log | Synthetic cold start; short interval, not a performance benchmark or exhaustive crash check |
| S02 | Reissue the activity launch and repeat startup assertions | Preserve Android's reported launch state, including `UNKNOWN (0)` |
| S03 | Send Home, wait 15 seconds and record process presence | Completion means the observation ran; process presence does not demonstrate all background jobs |
| S04 | Enter a reviewed feature route, deny a system prompt or revoke a previously granted permission, verify denied grant and expected fallback element | Requires authenticated test account, exact selectors and meaningful feature assertions |

For S04, an optional JSON configuration maps `camera`, `microphone` and `media` to a `route` list of exact selectors plus `allowed_marker` and `denied_marker`. A selector is either a MAX resource ID or a reviewed package/class/text match; an optional `click_parent` selects the nearest enabled clickable ancestor when the label itself is not clickable. The researcher must inspect the actual build's screens and review every action before writing this file. Selectors must match exactly one enabled element with valid bounds. Ambiguous, missing, unreviewed or transmission-related selectors block execution. Configuration validation occurs before permission changes. A media picker may work without broad media permission: this must be tested with appropriate expectations rather than treated as an automatic failure.

A reviewed `request_route` opens an app rationale button when the system prompt is not automatic; `back_steps` leaves the allowed feature before revocation. For media, the reviewed configuration treats image/video/selected-media permissions as a group and temporarily grants CAMERA to isolate visual-media refusal. Fresh launch after a grant avoids reusing a permission-dependent screen from the prior state. These setup grants and grouped targets are explicit in E08.

Permission refusal uses `pm revoke` followed by clearing the `user-set` and `user-fixed` flags to permit a fresh system prompt. Revocation first exercises the allowed route, then revokes the permission and reopens the feature. These ADB steps simulate states and are not evidence that an ordinary user can change flags in the same way. [Android permission testing guidance](https://developer.android.com/training/permissions/requesting).

A full emulator snapshot is saved before each permission scenario and restored in `finally`. The runner waits for ADB and the package service to reconnect, compares grants, flags and AppOps modes, and aborts further scenarios if restoration fails. A separate run-baseline snapshot restores the overall state. Snapshot restoration also resets the test-account app state; it must never be used on a personal device.

## Evidence and network limits

[The completed pre-authentication results](../evidence/2026-10-11/runtime-preauth.json) include exact intervals, launch metrics, process assertions, capture hashes and reviewed metadata. Six permission scenarios were blocked at the login screen before any permission mutation. They are not counted as passes.

Raw PCAPs, app-UID logs, screenshots, accessibility dumps and action journals are retained outside Git. [The PCAP summarizer](../scripts/pcap_metadata.py) exports flow metadata and only HTTP host names and visible TLS SNI; it omits request paths, queries, cookies and bodies. Public metadata requires manual review because a host name could itself contain an identifier.

Capture covers the entire emulator, including system services. A stopped-app control provides context but does not establish per-packet attribution. The parser performs no TCP reassembly, TLS decryption, encrypted-DNS decoding or IPv6 extension traversal. SNI is recognized only when its complete extension occurs in one segment, and can be an outer name under ECH. [RFC 9849, section 10.5](https://www.rfc-editor.org/rfc/rfc9849.html#section-10.5) explains this visibility limit. No HTTP signature in a short capture does not prove absence of cleartext communication. No CA, pinning bypass or instrumentation of MAX is part of this stage.

Run guardrail and parser tests with `python3 -m unittest discover -s tests -v`. Automated unit tests validate the tooling; actual feature scenarios require real execution and evidence.

## Completed authenticated checks

The [reviewed routes](../tooling/max-26.35.1-permission-routes.json) cover camera access through Settings → Devices → Sign in with QR code, and visual-media access through profile editing → avatar → Upload from gallery. No code was scanned, no device was linked, and no profile was saved. The camera assertion is presence of the preview UI element; successful frame decoding is outside that assertion.

Generate the only gallery fixture with [create_media_fixture.py](../scripts/create_media_fixture.py), push it to the isolated emulator's Pictures directory and request a media scan before saving the test baseline:

```bash
python3 scripts/create_media_fixture.py --output /private/tmp/max-research-fixture.png
adb -s emulator-5580 push /private/tmp/max-research-fixture.png /sdcard/Pictures/max-research-fixture.png
adb -s emulator-5580 shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE \
  -d file:///sdcard/Pictures/max-research-fixture.png
```

The tested PNG SHA-256 is `68e0f8e2bbdf30e3f1b4188e93821c611e461a41b97b41cd2d5f8a6e4fe6238a`. The allowed media assertion is the gallery node for the only image, without selecting it. Reproduce the generic run above with `--permission-config tooling/max-26.35.1-permission-routes.json`, starting from the main settings screen. The case data, capture hashes and restoration comparisons are in [E08](../evidence/2026-10-11/runtime-authenticated.json).

A separate refusal-only script covers the microphone without ever granting RECORD_AUDIO. Select a test recipient's chat manually with an empty composer and microphone permission already denied. Run:

```bash
python3 scripts/test_microphone_denial.py \
  --serial emulator-5580 --expected-avd max-research \
  --adb /path/to/Android/sdk/platform-tools/adb \
  --collection /private/tmp/max-review-collection \
  --output /private/tmp/max-microphone-new-run \
  --expected-recipient 'YOUR_TEST_RECIPIENT'
```

The script checks the exact chat header, empty draft, denied microphone grant and exact voice-control ID/action description before holding the entry for 900 ms. The control reports `clickable=false` but handles touch; its center is derived from the uniquely matched enabled node. The script denies the verified system audio prompt and asserts return to the empty composer, then restores the baseline. It never grants microphone permission or taps Send. [E09](../evidence/2026-10-11/runtime-microphone.json) discloses the exploratory assertion failure and the repeated test. Active-recording revocation remains not run; the generic microphone routes remain blocked.

Private action journals record selected taps/holds; permission snapshots, reviewed route configuration and source recipes document the permission mutations. No recipient or message text is present in the public route configuration. The [minimal UI extracts](../evidence/2026-10-11/runtime-ui-excerpts.json) include only the prompt and result nodes needed for the public assertions. Raw trees can incidentally include existing messages in the explicitly selected chat and must remain private.
