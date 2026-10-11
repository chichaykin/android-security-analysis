# MAX for Android: evidence-led security review

This repository documents an independent review of the installed RuStore-channel MAX build (`ru.oneme.app`) collected on **11 October 2026**. The tested APK set reports **26.35.1 (6867)**. The review is limited to this build and the stated test environment; it does not make claims about all MAX releases or distribution channels.

**Result:** The completed static checks identify sensitive permission declarations, exported components, and eight domains for which the app's network security configuration permits cleartext traffic. They do **not** establish spyware behavior, arbitrary remote command execution, bulk upload of contacts or installed apps, whole-device file scanning, or observed cleartext transfer. No confirmed exploitable vulnerability is reported. See the [technical report](android_analysis/TECHNICAL_REPORT.md) for evidence and limits.

| Document | Purpose |
| --- | --- |
| [Final research report](REPORT.md) | Consolidated assessment, static/runtime results, evidence and remaining coverage |
| [Executive summary](android_analysis/EXECUTIVE_SUMMARY.md) | Short presentation-ready result |
| [Technical report](android_analysis/TECHNICAL_REPORT.md) | Observations, reproductions, confidence and limits |
| [Methodology](docs/METHODOLOGY.md) | Acquisition, evidence standard and safe runtime protocol |
| [Earlier-claim register](docs/CLAIM_REGISTER.md) | Corrections to previous analyses |
| [Evidence index](evidence/2026-10-11/INDEX.md) | Public build identity and machine-readable static evidence |
| [Runtime automation](docs/RUNTIME_AUTOMATION.md) | Isolated emulator scenarios, safeguards and current coverage |
| [Future tooling proposal](docs/FUTURE_TOOLING.md) | Separate engineering idea, not a completed capability |

A separate Android 17 emulator using the identical APK set completed startup, repeat-launch and background observations before and after authentication. Camera and visual-media refusal/revocation flows passed their bounded assertions; a separate microphone-refusal scenario returned to an empty composer with permission denied. Active-recording revocation remains not run. Whole-emulator captures do not establish TLS payload contents or per-packet app attribution. [Authenticated runtime evidence](evidence/2026-10-11/runtime-authenticated.json), [microphone refusal](evidence/2026-10-11/runtime-microphone.json), [minimal UI extracts](evidence/2026-10-11/runtime-ui-excerpts.json).

The full APKs and private device snapshots are deliberately outside Git. The public evidence includes hashes and a certificate fingerprint so another researcher with the same APK set can reproduce the static checks. Decompiled output is not treated as authoritative without checking call paths and bytecode.

## Reproduce the static checks

Requires Android SDK `adb`, `apksigner`, `aapt2`, `apkanalyzer`, Bash and Python 3. The collector requires an explicit device serial and collects **APKs and build metadata only**. Choose an output directory outside this repository.

```bash
./scripts/pull_oneme_for_analysis.sh \
  --serial YOUR_DEVICE_SERIAL \
  --output /private/tmp/max-review-collection \
  --apksigner /path/to/Android/sdk/build-tools/36.0.0/apksigner

./scripts/analyze_max_apk.py \
  --collection /private/tmp/max-review-collection \
  --output /private/tmp/max-review-static.json \
  --apkanalyzer /path/to/Android/sdk/cmdline-tools/latest/bin/apkanalyzer \
  --aapt2 /path/to/Android/sdk/build-tools/36.0.0/aapt2
```

Compare the generated JSON with [this study's summary](evidence/2026-10-11/static-summary.json) only if the base APK SHA-256 matches. The collector does not elevate privileges, copy private app data, change permissions, or start the app.

## Attribution

This is an independent review of publicly distributed application binaries on a personally owned device. Findings describe what was actually checked. Previous drafts remain available through Git history; their unsupported conclusions have been corrected in the current documents. No claim of vendor affiliation or coordinated disclosure is made.
