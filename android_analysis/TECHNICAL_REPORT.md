# MAX Android security review — 26.35.1 (6867)

## Assessment and scope

This review establishes build identity, manifest configuration, selected code paths, a read-only personal-device baseline and bounded isolated-emulator runtime outcomes. **No exploitable vulnerability or malicious behavior was confirmed by the completed checks.** This is a bounded result: it is not a certification that the application is safe, nor an exhaustive search for malicious behavior.

The subject is the installed RuStore-channel APK set for `ru.oneme.app`, collected on **11 October 2026 at 02:45 UTC (10:45 Asia/Singapore)**. It reports version `26.35.1`, version code `6867`, min SDK `26`, target SDK `37`, and compile SDK `37`. The environment is a personal Pixel 8 Pro running Android 17. Acquisition did not extract private application databases, conversations, contacts or personal media from the Pixel. Subsequent isolated-emulator account/UI coverage is documented below. [E01: Build manifest](../evidence/2026-10-11/build.json).

The [public RuStore listing](https://www.rustore.ru/catalog/app/ru.oneme.app), checked on 11 October, displayed `26.35.0` dated 6 October 2026. The installed build was newer than that displayed version. This discrepancy does not establish the release rollout status, region, or latest version available to every client. No update was installed and availability inside the RuStore app was not checked.

## Evidence and confidence

The [evidence index](../evidence/2026-10-11/INDEX.md) ties the public extracts to APK hashes. The base APK SHA-256 is:

```text
a9a76d5b15f1ed13f0fd368ebbc2cf0bb3c8567d15e4d229944865358d31c5a9
```

The base APK and both installed configuration splits passed `apksigner verify` and report the same signer certificate SHA-256:

```text
1684414033eb263e2c615f8b7df5ed8793850a07656304997fbf07e9e21e1e93
```

This is verification of the collected binaries' signatures and signer consistency. It does not independently authenticate the developer through a previously trusted certificate or establish equality with the March 2026 build, whose original APK is unavailable here.

Confidence is **high** for the directly extracted manifest and the cited DEX instructions. Confidence in runtime activation and data transfer remains **unestablished** unless explicitly stated. JADX 1.5.6 reported 558 decompilation errors across the full source pass; selected substantive conclusions below were checked against `apkanalyzer dex code`. Native libraries, reflection, other code paths and backend behavior remain outside the verified coverage.

## O01 — Sensitive permission declarations and version-specific corrections

**Type:** Configuration observation; informational. **Evidence:** [E02](../evidence/2026-10-11/static-summary.json), `manifest_permissions`. **Confidence:** High for declarations; no misuse demonstrated.

The examined base manifest contains 58 unique permission names, including contacts, precise/coarse location, camera, microphone, media access, boot reception, battery optimization exemption requests, package installation requests and foreground media projection. Legacy storage declarations are bounded by `maxSdkVersion`: read storage through API 32 and write storage through API 29.

`SYSTEM_ALERT_WINDOW` and `QUERY_ALL_PACKAGES` are absent from the examined base manifest. This corrects an earlier version-independent overlay claim. It does not establish what other-channel or older binaries declare.

The device baseline had contacts, location and media permissions denied; camera, microphone and notifications were granted. Those states describe this device at collection time. Manifest declarations do not prove grants or feature use; see Android's [permission declaration guidance](https://developer.android.com/training/permissions/declaring) and [runtime permission workflow](https://developer.android.com/training/permissions/requesting).

**Potential impact and conditions:** Sensitive information can be exposed if an enabled, reachable feature accesses it under the applicable platform authorization. The declaration alone establishes no unauthorized access. Package installation flows were not exercised; `REQUEST_INSTALL_PACKAGES` supports a request to install, not evidence of silent installation. [Android permission reference](https://developer.android.com/reference/android/Manifest.permission#REQUEST_INSTALL_PACKAGES).

**Reproduction:** Run `analyze_max_apk.py` against an APK set with the recorded base hash and inspect `manifest_permissions`. Compare grants separately through `dumpsys package ru.oneme.app`; do not infer them from the APK.

## O02 — Explicit cleartext exceptions for eight domains

**Type:** Configuration observation; review required, no demonstrated traffic exposure. **Evidence:** [E03: extracted XML](../evidence/2026-10-11/static-summary.network-policy.xml) and E02 `network_domain_rules`. **Confidence:** High for policy.

`res/xml/network_security_config.xml` sets `cleartextTrafficPermitted="true"` for these exact domains, each with `includeSubdomains="false"`:

- `mobileid.megafon.ru`
- `idgw.mobileid.mts.ru`
- `hhe.mts.ru`
- `he-mc.tele2.ru`
- `he-mc.t2.ru`
- `balance.beeline.ru`
- `nuc-cdp.voskhod.ru`
- `nuc-cdp.digital.gov.ru`

**Potential impact and conditions:** If a code path transmits security-sensitive information in cleartext, a network observer could read or modify it. Short pre-authentication emulator captures found no HTTP request signatures under the parser limits described in E07. No payloads for these eight domains were established. Domain names do not establish what data would be sent. Network libraries may enforce policy differently. [Android network security configuration](https://developer.android.com/privacy-and-security/security-config), [cleartext communication risks](https://developer.android.com/privacy-and-security/risks/cleartext-communications).

**Reproduction:** Decode the XML with `apkanalyzer resources xml --file /res/xml/network_security_config.xml BASE.apk`; compare with E03. Follow-up requires a controlled feature flow and network capture on a test account/device. E07 provides a bounded runtime observation; it does not prove absence of cleartext traffic in other flows.

## O03 — Exported components and WebView bridges

**Type:** Attack-surface inventory; exploitability untested. **Evidence:** E02 `exported_components`; [E04E: DEX bridge registration](../evidence/2026-10-11/bytecode-excerpts.md#e04e-javascript-bridges). **Confidence:** High for the cited declarations/instructions.

The base manifest explicitly exports 19 components: two activities, ten services, six receivers and one provider. These include the launcher and deep-link activity, push integration services and a device-ID provider. Some components have platform or vendor permission gates. Manifest exposure is an entry point to inspect, not a vulnerability finding. Disabled component state and code-level caller checks can further affect exposure. See Android's [intent and exported-component documentation](https://developer.android.com/guide/components/intents-filters).

Web app initialization registers `WebViewHandler` and `AndroidPerf` bridges and conditionally registers `PrivateWebViewHandler`. Their registration is present in bytecode. Trusted-origin enforcement, exposed method behavior and attacker-controlled navigation were not fully traced or exercised, so no JavaScript bridge exploit is claimed. Resource references in the decoded deep-link filters remain unresolved in E02; the report does not infer concrete hosts from those references.

**Reproduction:** Inspect E02's component names and `required_permission` values, and disassemble `pil.d(Ljava/lang/Object;)Ljava/lang/Object;` for the bridge calls. An isolated test account/device is required for adversarial intent and WebView flow tests.

## O04 — Earlier bulk-data and remote-command assertions revisited

**Type:** Corrections and selected static call-path observations. **Evidence:** [E04A–G](../evidence/2026-10-11/bytecode-excerpts.md). **Confidence:** High for cited instructions; execution conditions incomplete.

| Topic | What this build establishes | What remains unknown |
| --- | --- | --- |
| MyTracker installed-package provider | `setInstalledPackagesProvider(Le5c;)` reads its config field, calls `Object.getClass()` and returns `this`; it does not store the supplied provider. E04A. | Other analytics paths and actual payloads. The old provider-registration explanation cannot be reused for this binary. |
| Other installed-package query | `n16.a(Ld55;)` calls `PackageManager.getInstalledPackages(8)`. E04C. Decompiled adjacent code searches for a `VkpnsDeviceIdContentProvider` and queries its `deviceid` URI. | Invocation frequency, caller reachability and transmission. Android package visibility limits the result; absence of `QUERY_ALL_PACKAGES` does not prove that no packages are visible. [Android package visibility](https://developer.android.com/training/package-visibility). |
| Disk usage worker | `DiskUsageWorker.d()` supplies the application's `dataDir`, the parent of its external-files directory, and the parent of its installed APK path as traversal roots. E04B. | Whether this worker runs in the observed account state, and actual report contents. These identified roots do not support a whole-device scanning claim. |
| Disk usage reporting | The worker serializes a report and calls a sample-scheduling routine only when the accumulated size exceeds `0x280000000` (10 GiB), after earlier feature/probability gates. The routine constructs and enqueues `SampleUploadWorker`. E04B/F. | Current remote configuration, worker scheduling on this device, successful upload and backend retention. A static upload route does not establish observed transfer. |
| System command execution | `bi6.C` constructs a fixed `logcat` argument array and calls `Runtime.exec(String[])`. E04D. | Whether this branch runs for the user, and any independent route from remote inputs to other commands. The result corrects the earlier universal “no Runtime.exec” claim. |
| Push | `FcmMessagingService.d(Lkxf;)` parses the payload and dispatches to coroutine `nag`. The remainder of the coroutine was not reconstructed reliably by JADX. | A complete route from push to security-sensitive action. No arbitrary remote OS command execution is established. |

The worker's JSON includes file/directory names and sizes in the examined app-related roots. If the conditional upload path executes, those metadata may be included in the sample. No file contents or actual upload were observed. The code-level reporting path deserves follow-up without extending its scope to all files on the phone.

## Other reviewed capability areas

| Area | Completed review | Remaining coverage |
| --- | --- | --- |
| Contacts | Manifest and existing grant state | Synchronization, payloads, confirmation and write paths |
| Storage | Manifest, DiskUsageWorker roots/report branch and visual-media picker refusal/revocation | SAF, partial photo access, other picker paths and actual transferred files |
| Installer | Permission and `PackageInstaller` source references in `mvk`/`ot` | Trigger, update provenance, user approval and successful installation |
| Class loading | `PathClassLoader` subclass `prm` and reflective library-path inspection `b4j` identified in source | Downloaded code provenance and complete dynamic-loading analysis |
| Camera/microphone/screen capture | Manifest, camera scanner refusal/revocation and microphone refusal | Actual recorded media, capture lifetime, active-capture revocation and screen capture |
| Background/push | Boot declarations plus bounded startup and Home/background observations | Controlled boot, long-duration behavior, job execution and push replay |

Source-reference observations in this table are triage results from JADX, not bytecode-validated security findings. The underlying binaries are identified by E01. Exact class names are version-specific.

## Runtime coverage and device preservation

Only read-only configuration and process checks were completed on the personal phone. Permission grants/flags and AppOps modes were compared before and after the analysis and were unchanged. No app UI was opened, no app state was cleared, no permissions were changed, and no messages, contacts, files, calls or diagnostic reports were sent by the research scripts. [E05: device-state check](../evidence/2026-10-11/runtime-state.json).

A separate isolated Android 17 emulator ran the identical APK set without an authenticated account. Cold launch completed with `Status: ok`, `TotalTime: 251 ms`, a login screen and a live main process after 15 seconds; app-UID logs contained no `FATAL EXCEPTION` marker in that window. Repeat launch reported `UNKNOWN (0)`, which is retained without reclassifying it as a measured warm start. The main process was present 15 seconds after Home. These are bounded observations, not a performance benchmark or general background reliability result. [E07: runtime evidence](../evidence/2026-10-11/runtime-preauth.json).

Whole-emulator WAN capture recorded 0 packets in the stopped-app control, 136 in cold start, 4 in repeat start and 75 in the background window. Visible TLS SNI included `api2.oneme.ru`, `stats-dg.rustore.ru`, `tracker-api.vk-analytics.ru` and `ts43.eas3.msg.t-mobile.com`. These are guest-wide observations with no per-packet MAX attribution. No HTTP request signature was found by the limited parser; no TCP reassembly or TLS decryption was performed. TLS contents remain unknown. Raw captures and UI/log evidence remain private.

The initial six permission scenarios were **blocked before mutation** at the login screen. After the user authenticated an account designated for testing, the same APK set was tested through reviewed routes. The emulator build differs from the personal Pixel; results do not establish identical behavior on physical hardware. [E08: authenticated results](../evidence/2026-10-11/runtime-authenticated.json).

| Scenario | Observed result | Conditions and limits |
| --- | --- | --- |
| Authenticated cold/repeat launch | Activity launch succeeded, a main process remained after 15 seconds, login marker was absent and no `FATAL EXCEPTION` marker appeared in app-UID logs | Cold `TotalTime` was 304 ms; repeat launch reported `UNKNOWN (0)`. These are short synthetic observations, not benchmarks. |
| Authenticated background | Main process present 15 seconds after Home | No long-duration, boot, push or job-completion assertion. |
| Camera refusal | QR-scanner entry requested camera permission; denying it displayed “To scan a QR code, please allow camera access” | No code was scanned and no device was linked. |
| Camera revocation | With a grant, the scanner preview element appeared; after leaving it, revoking access and reopening, the same access explanation appeared and CAMERA was denied | Revocation during ongoing capture was not tested; preview-element presence does not by itself prove successful camera-frame processing. |
| Visual-media refusal | Denying the visual-media permission group left the picker at “No access to files and media” | CAMERA was temporarily granted to isolate media access. Images, video and selected-visual-media permissions were tested together. |
| Visual-media revocation | With grants, a gallery image node for the only synthetic PNG appeared; after leaving the picker, revoking the group and reopening, access was denied | No image was selected, saved to the profile or uploaded. Partial-access selections and other media flows remain untested. |
| Microphone refusal | With RECORD_AUDIO already denied, holding the voice entry produced a system audio prompt; denying it returned to the empty composer with permission still denied | No grant or send action occurred. No separate microphone explanation appeared in the observed tree. [E09](../evidence/2026-10-11/runtime-microphone.json). |
| Microphone revocation | **Not run** | No permitted active-recording route was exercised. The two generic microphone routes remained blocked; a separate refusal-only test supplied the result above. |

[Minimal selected UI nodes](../evidence/2026-10-11/runtime-ui-excerpts.json) support these assertions without exposing account names or conversation content. Per-scenario camera/media restoration and overall baseline restoration compared permission grants, flags and AppOps modes successfully. The microphone baseline restoration also passed. An exploratory microphone run failed a tooling assertion that expected an explanation; the observed empty-composer outcome was then specified and verified in a repeat run. This was not classified as an application defect.

Authenticated stopped/start/repeat/background captures contained 0, 1187, 281 and 19 guest packets respectively. E08 lists reviewed visible SNI for each scenario; the presence of a domain does not establish a payload, purpose or MAX attribution. No HTTP request signature was found under the parser's limits. TLS contents remain unknown. Feature captures include startup and system traffic and must not be interpreted as counts of feature-specific transmissions.

The supplied account contained pre-existing conversations. The user separately authorized one text-message send to an explicitly identified recipient; a single send action was performed and an outgoing message with one check mark was visually observed in a private screenshot. Read status was not established. This operational result is not independently verifiable from public evidence and is excluded from security findings. Recipient identifiers, message contents and chat screenshots are withheld. No voice message, image, contact, call or diagnostic submission was performed by the tests.

Adversarial deep links, TLS validation, traffic payload inspection, active-capture revocation and broader account flows remain **not run**. No personal-phone UI or app database was inspected. See [runtime automation](../docs/RUNTIME_AUTOMATION.md) for reproduction, safeguards and environmental limits.

## Recommendations and next verification

1. Use the recorded build hashes for any reproduction or follow-up. Reacquire and recheck metadata if an update changes the APK set.
2. On an isolated device and test account, trace activation of the disk usage worker, its configuration gates and sample payload, using synthetic files.
3. Verify cleartext domains through feature-specific capture; distinguish metadata-only endpoints from transmissions containing user data.
4. Validate deep-link, exported push/provider and WebView boundaries with benign inputs and explicit expected results before adversarial testing.
5. Extend the completed camera/media and microphone-refusal checks to active-capture revocation, partial media access, contacts and location; verify recovery and restoration after every scenario.

The earlier sensational conclusions have been withdrawn in the [claim register](../docs/CLAIM_REGISTER.md). This report supports a reproducible static review and bounded runtime observations in the documented environments. Its remaining hypotheses require runtime confirmation before they become security findings.
