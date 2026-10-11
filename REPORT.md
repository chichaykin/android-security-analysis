# MAX for Android — Final Research Report

**Study date:** 11 October 2026

**Subject:** `ru.oneme.app`, RuStore-channel APK set, version **26.35.1 (6867)**

**Coverage:** Static binary review, read-only personal-device baseline, and bounded runtime scenarios in an isolated Android emulator

## Assessment

The completed checks did **not confirm an exploitable vulnerability or malicious behavior**. They established sensitive permission declarations, exported entry points, eight explicit cleartext-policy exceptions, selected bytecode paths, and specific permission-refusal/revocation outcomes. These observations do not establish bulk data collection, whole-device scanning or arbitrary remote command execution.

This result is limited to the identified binaries and tested scenarios. It is not a safety certification, an exhaustive code audit, or evidence that sensitive information is never transmitted. Unobserved TLS payloads and untested behavior remain unknown.

## 1. Build identity and acquisition

The installed APK set was collected from a personal Pixel 8 Pro running Android 17, build `CP3A.260905.009`, at **02:45 UTC / 10:45 Asia/Singapore**. The installer package was `ru.vk.store`. The app reports minimum SDK 26 and target SDK 37. All three collected APKs passed signature verification and share the signer fingerprint below. [E01: build manifest](evidence/2026-10-11/build.json).

| Artifact | SHA-256 |
| --- | --- |
| `base.apk` | `a9a76d5b15f1ed13f0fd368ebbc2cf0bb3c8567d15e4d229944865358d31c5a9` |
| `split_config.arm64_v8a.apk` | `dd60b53a4055aeb8e0e94fc12a48a3fe72a97816723338581b3145c87820737b` |
| `split_config.xhdpi.apk` | `59208feddef4c955aa19b2c413dfa978b22799c5921fd046e37bd502740246e9` |

Signer certificate SHA-256:

```text
1684414033eb263e2c615f8b7df5ed8793850a07656304997fbf07e9e21e1e93
```

Signature verification establishes binary integrity under the collected signer and consistency across splits. It does not independently authenticate the developer against a previously trusted reference.

The public RuStore listing observed during the study displayed `26.35.0`; the installed package reported `26.35.1`. Update availability inside RuStore was **not checked**. This report therefore identifies the collected installed build and does not call it the globally latest release. [Acquisition scope](android_analysis/TECHNICAL_REPORT.md#assessment-and-scope).

## 2. Method and evidence standard

The review distinguishes manifest declarations, code presence, connected static paths and observed runtime behavior. A permission, SDK, URL or class name alone is insufficient to establish a vulnerability or data transfer.

Static extraction used Android SDK tools, with independent `aapt2` cross-checks. JADX 1.5.6 was used for navigation; it reported 558 decompilation errors. Selected substantive code conclusions were checked against DEX disassembly. Tool versions, method descriptors and evidence hashes are recorded in [E01](evidence/2026-10-11/build.json) and [E04A–G](evidence/2026-10-11/bytecode-excerpts.md).

Runtime tests used the identical three-APK set in a separate Android 17 ARM64 emulator, version 36.6.11. Its Android build and hardware environment differ from the Pixel. The user completed sign-in to an account designated for testing; that account contained pre-existing conversations. Raw account screens and logs remain private. [E08: environment and scenarios](evidence/2026-10-11/runtime-authenticated.json).

## 3. Confirmed static observations

| ID | Observation | Evidence and confidence | Interpretation and limits |
| --- | --- | --- | --- |
| O01 | The examined manifest declares 58 unique permissions. `SYSTEM_ALERT_WINDOW` and `QUERY_ALL_PACKAGES` are absent. | [E02, `manifest_permissions`](evidence/2026-10-11/static-summary.json); high confidence for declarations | Sensitive capabilities require further reachability and behavior review. Absence applies only to the examined manifest. |
| O02 | Network configuration permits cleartext for eight exact domains, with `includeSubdomains=false`. | [E03, decoded XML](evidence/2026-10-11/static-summary.network-policy.xml); high confidence for configuration | An allowance does not prove an HTTP request or sensitive payload. Exposure would require a reachable path actually sending sensitive data in cleartext. |
| O03 | The manifest explicitly exports 19 components: two activities, ten services, six receivers and one provider. WebView initialization registers JavaScript bridges. | [E02](evidence/2026-10-11/static-summary.json), [E04E](evidence/2026-10-11/bytecode-excerpts.md#e04e-javascript-bridges); high confidence for the cited declarations/instructions | Caller checks, permission gates, origins and attacker-controlled input were not fully validated. No component or bridge exploit is established. |
| O04A | The examined MyTracker installed-package provider setter does not store its argument. A separate method calls `getInstalledPackages(8)`. | [E04A/C](evidence/2026-10-11/bytecode-excerpts.md); high confidence for cited instructions | The earlier provider-registration explanation cannot be reused. Bulk inventory upload, invocation frequency and actual payloads remain unestablished. |
| O04B | DiskUsageWorker selects app-related roots and conditionally schedules a sample report above 10 GiB, after earlier gates. | [E04B/F](evidence/2026-10-11/bytecode-excerpts.md); high confidence for the examined static path | The code does not support a whole-device scanning conclusion. Runtime activation, successful upload and backend handling were not observed. |
| O04C | A fixed `logcat` argument array reaches `Runtime.exec(String[])`. FCM payload handling dispatches to a coroutine whose full behavior was not reliably reconstructed. | [E04D/G](evidence/2026-10-11/bytecode-excerpts.md); high confidence for cited instructions, incomplete downstream coverage | A fixed local command does not establish arbitrary commands through push. No remote command-execution finding is reported. |

The eight cleartext-policy domains are `mobileid.megafon.ru`, `idgw.mobileid.mts.ru`, `hhe.mts.ru`, `he-mc.tele2.ru`, `he-mc.t2.ru`, `balance.beeline.ru`, `nuc-cdp.voskhod.ru` and `nuc-cdp.digital.gov.ru`. Their names do not establish the purpose or content of any request. [E03](evidence/2026-10-11/static-summary.network-policy.xml).

These are configuration and code observations, rather than severity-rated exploits. Detailed conditions, potential impact and reproduction steps appear in the [technical report](android_analysis/TECHNICAL_REPORT.md).

## 4. Runtime results

| Scenario | Result | Scope of the assertion |
| --- | --- | --- |
| Stopped-app control | Completed; main MAX process absent at the control check | Provides guest-network context, not per-packet attribution |
| Cold launch and repeat opening | Completed before and after authentication; process present after 15 seconds and no `FATAL EXCEPTION` marker in the checked app-UID logs | A short synthetic startup observation; not an exhaustive crash check or performance benchmark |
| Background observation | Main process present 15 seconds after Home | Does not establish long-term reliability, job completion or push handling |
| Camera refusal | System permission denied; app displayed its camera-access explanation | QR-scanner entry only; no code scanned or device linked |
| Camera revocation | Preview UI appeared with a grant; after leaving, revoking and reopening, access was denied | Not revocation during ongoing capture; preview-element presence does not prove frame processing |
| Visual-media refusal and revocation | Denied permission group produced the no-access UI; granted state displayed the only synthetic gallery image | CAMERA temporarily granted to isolate visual-media access; no image selected, profile saved or file uploaded |
| Microphone refusal | With RECORD_AUDIO already denied, a hold on the voice entry produced the system prompt; denial returned to the empty composer | Microphone permission never granted by this scenario; no voice send action |
| Microphone revocation during recording | **Not run** | No active recording was started |

The media fixture was a generated 256 × 256 PNG with SHA-256 `68e0f8e2bbdf30e3f1b4188e93821c611e461a41b97b41cd2d5f8a6e4fe6238a`. Image, video and selected-visual-media permissions were tested as a group. Partial-access selection remains untested. [E08](evidence/2026-10-11/runtime-authenticated.json).

The initial unauthenticated permission tests were blocked before mutation. The generic microphone routes also remained blocked; a separate refusal-only script supplied the microphone result. An exploratory microphone run failed a tooling assertion expecting an explanation. The observed empty-composer outcome was then specified and verified in a repeat run. This was not classified as an application defect. [E07](evidence/2026-10-11/runtime-preauth.json), [E09](evidence/2026-10-11/runtime-microphone.json).

Public [minimal UI extracts](evidence/2026-10-11/runtime-ui-excerpts.json) contain only the nodes supporting these assertions, with hashes of their private source files. Full trees and screenshots may include account information and are excluded from Git.

## 5. Network observations

Captures covered the entire isolated emulator's cellular/WAN interface, including system services. Wi-Fi was disabled for this capture method. No trusted certificate was installed, TLS was not decrypted, and pinning was not bypassed.

| Account state | Stopped control | Cold start | Repeat start | Background |
| --- | ---: | ---: | ---: | ---: |
| Unauthenticated | 0 packets | 136 packets | 4 packets | 75 packets |
| Authenticated | 0 packets | 1,187 packets | 281 packets | 19 packets |

These are guest-wide counts from the recorded windows, **not MAX-specific traffic volumes**. The control does not establish ownership of packets in other windows. Feature captures also include startup and system traffic. [E07](evidence/2026-10-11/runtime-preauth.json), [E08](evidence/2026-10-11/runtime-authenticated.json).

The parser found no HTTP request signatures in the published scenario captures. It performs no TCP reassembly, TLS decryption, encrypted-DNS decoding or IPv6 extension traversal. That negative result does not prove absence of cleartext communication. Visible TLS SNI is recorded as host metadata only; it does not establish request content, purpose or successful transfer. TLS application payloads remain **unknown**. [Capture and parser limits](docs/RUNTIME_AUTOMATION.md#evidence-and-network-limits).

## 6. Preservation, privacy and validation

Personal-phone acquisition used read-only commands. Its permission grants, flags and AppOps modes were unchanged. Private app databases were not extracted, and the personal-phone UI was not opened for the study. [E05](evidence/2026-10-11/runtime-state.json).

Emulator permission scenarios used full snapshots and restoration checks. Camera/media per-scenario comparisons and all published run-baseline comparisons confirmed equality of permission grants, flags and AppOps modes. ADB-generated permission states and fresh launches are test-environment interventions, not assertions about ordinary user interaction.

The user separately authorized one text-message send to a specified recipient. A single send action was performed, and the outgoing message was visually observed with one check mark. Read status was not established. Recipient details, message content and chat screenshots remain private; this operational result is excluded from public security findings because its visual evidence is not publicly available. No voice message, image, contact, call or diagnostic submission was performed by the tests.

Validation recorded **21 passing tooling tests**, repeated static outputs with identical results, independent permission/network-policy cross-checks, a repeated fixture hash, local-link checks and public-language/identifier scans. All public authored documentation and code comments are in English. [E06: validation record](evidence/2026-10-11/validation.json).

## 7. Corrections and remaining work

Earlier conclusions about spyware, bulk application-inventory upload, whole-device scanning, silent installation and arbitrary commands through push are not supported by the completed evidence. They were withdrawn or narrowed in the [claim register](docs/CLAIM_REGISTER.md). Lack of confirmation is not presented as proof that the behavior cannot exist.

The following remain outside verified coverage:

- Sensitive TLS payloads, backend processing and retention.
- Runtime activation and actual upload of the conditional disk-usage report.
- Complete installed-package, contact and location data flows.
- Adversarial deep links, exported-component authorization and WebView origin boundaries.
- Installation and downloaded-code provenance, native-code behavior and unreconstructed paths.
- Active-capture revocation, screen capture, partial media access, long-duration background behavior and controlled push replay.
- Update availability inside RuStore and behavior of other versions, channels or physical devices.

## 8. Reproduction and evidence navigation

Start with the [README](README.md), [methodology](docs/METHODOLOGY.md) and [evidence index](evidence/2026-10-11/INDEX.md). Static reproduction requires matching APK hashes. Runtime reproduction requires the isolated environment, synthetic fixture, reviewed routes and explicit scenario assertions described in [runtime automation](docs/RUNTIME_AUTOMATION.md).

A matching version label without matching hashes is insufficient. A changed APK set, Android build, account state or distribution channel requires renewed verification. This report describes the completed study and keeps untested capabilities and future tooling proposals separate from its findings.
