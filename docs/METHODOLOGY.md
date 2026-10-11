# Research methodology

## Object and evidence levels

This study reviews the installed RuStore-channel MAX `26.35.1 (6867)` APK set acquired on 11 October 2026. [Build identity](../evidence/2026-10-11/build.json) fixes the version, hashes, signer and tool versions. Results cannot be transferred to an APK with a different hash without repeating the checks.

Each statement must distinguish four evidence levels:

1. **Declaration:** a permission, component or network rule exists in the manifest/resources.
2. **Code presence:** an instruction, method or string exists in a binary. A string match alone proves no behavior.
3. **Static call path:** connected instructions show the input, conditions, operation and downstream handler. Runtime activation may still depend on configuration and account state.
4. **Runtime observation:** a controlled scenario produced a recorded outcome. A negative observation applies only to the tested scenario and interval.

Confidence describes the support for a statement; severity describes demonstrated impact and prerequisites. A capability declaration has no exploit severity by itself. Potential impact must be introduced conditionally. Universal claims such as “no hidden collection exists” are not supported by a partial review.

## Acquisition and preservation

Run [the collector](../scripts/pull_oneme_for_analysis.sh) with an explicit serial, an unused output directory outside Git, and explicit tool paths if they are not on PATH. It checks that the selected device is authorized, queries package APK paths, pulls every returned APK, verifies signatures, computes SHA-256 and records package/build metadata. Any failed pull or signature verification leaves no completed output directory. It never attempts root, `run-as`, private-directory extraction, app installation or data clearing.

The output contains `package-dump.private.txt` and `appops-baseline.private.txt`. These may include personal configuration and package visibility details. Keep the complete collection private. This study retains its raw collection in the Git-ignored `analysis_artifacts/max-2026-10-11/` directory; the temporary tool and decompilation workspace is outside the repository. Publish only reviewed extracts with identifiers, access times, account values and unrelated package names removed. Raw binaries, private data and complete logs do not belong in the public repository.

A valid APK signature does not alone authenticate the vendor's identity. Comparing certificates requires a trusted reference. This study records the collected signer and consistency across installed splits without asserting continuity with an unavailable earlier APK.

## Static extraction and bytecode review

[The analyzer](../scripts/analyze_max_apk.py) validates the base hash against the collection manifest and emits a deterministic JSON summary. It extracts unique permission names, explicit exported-component declarations and network domain rules. Raw DEX string counts are used only to prioritize review. Network XML is saved beside the summary for inspection.

Use Android SDK `apkanalyzer` and `aapt2` to compare extracted resources. Named resources that remain unresolved must remain unresolved in conclusions. The summary is an inventory, not a full exploitability scanner: inherited component permissions, runtime-disabled components, receiver registration, alternative networking implementations and code-level guards require additional inspection.

JADX 1.5.6 was used without resource decoding for source navigation. It reported 558 errors; decompilation failures are coverage limits. [The bytecode evidence recipe](../scripts/extract_bytecode_evidence.py) disassembles selected raw methods and exports minimal ranges, with a hash of each complete method output. It intentionally accepts only the reviewed base hash because obfuscated names and line ranges are version-specific.

```bash
./scripts/extract_bytecode_evidence.py \
  --apk /private/tmp/max-review-collection/apk/base.apk \
  --apkanalyzer /path/to/Android/sdk/cmdline-tools/latest/bin/apkanalyzer \
  --output /private/tmp/max-review-bytecode.md
```

The selected checks cover provider registration, package querying, disk traversal roots and the reporting threshold, sample-worker scheduling, fixed `logcat` command execution, WebView bridge registration and FCM coroutine dispatch. Native code and the full obfuscated coroutine graph have not been validated.

## Personal-device protocol

The user authorized reversible permission changes and required restoration. The completed phase used read-only commands and introduced no permission changes. The [device-state evidence](../evidence/2026-10-11/runtime-state.json) compares permission grants/flags and AppOps modes before and after the phase. Access timestamps are omitted; no conversation or personal media content was captured.

For any later active scenario, save the specific permission grants, flags, AppOps modes and affected settings before the scenario. Record each mutation; restore the original values after the scenario, including on failure, and compare the resulting configuration. Do not treat a `pm grant` alone as restoration of flags and AppOps. Stop further mutation if restoration cannot be verified.

Startup checks must avoid interrupting ongoing personal activity and must not capture personal conversation screens. Messaging, contacts/file transmission, calls, diagnostics upload, destructive state changes, CA installation and instrumentation require an isolated test account/device and an agreed scenario. Network metadata must identify its capture scope and scenario; guest-wide captures must not be presented as per-app attribution; TLS contents that are not observed remain unknown.

## Validation and publication criteria

- Re-run static extraction with the same binary and require identical output.
- Cross-check the permission and cleartext lists against independent `aapt2` output.
- Verify collector behavior for no device, multiple devices, missing package, split APKs, failed pull and invalid signature using mocks.
- Check local document links, JSON integrity, evidence hashes, tool metadata and language.
- Review public artifacts for device identifiers, tokens, account information and private content.
- Preserve explicit **not run** or **blocked** status for unavailable feature flows. Never count unavailable tests as passing.
- Document the isolated emulator runtime scenarios separately from personal-device observations; see [runtime automation](RUNTIME_AUTOMATION.md), [E07](../evidence/2026-10-11/runtime-preauth.json), [E08](../evidence/2026-10-11/runtime-authenticated.json) and [E09](../evidence/2026-10-11/runtime-microphone.json).

The [claim register](CLAIM_REGISTER.md) tracks corrections; the [technical report](../android_analysis/TECHNICAL_REPORT.md) states what was completed and what remains unknown.
