# Register of corrected earlier claims

Earlier report files were removed from the current documentation because they combined snippets, inference and conclusion without a reproducible evidence chain. Their original text remains in Git history. This register does not treat an unverified claim as disproved.

| Earlier assertion | Evidence provided earlier | Gap | Status for 26.35.1 |
| --- | --- | --- | --- |
| “Comprehensive surveillance tool” / “potential spyware” | A mixture of manifest declarations and decompiled excerpts | No validated malicious data flow or observed behavior | **Withdrawn.** No such conclusion follows from the completed checks. |
| Upload of every installed application to VK Analytics | `InstalledPackagesProvider` interface, processing routine and endpoint string | No verified registration, invocation, payload or observed upload; Android package visibility also constrains results | **Earlier explanation unsupported for this binary.** The MyTracker provider setter is a no-op in DEX. A separate package-query path exists; no bulk upload is established. |
| Recursive scanning of the entire SD card and file system | `DiskUsageWorker` recursion and JSON serialization excerpt | Caller, root path and destination were not established; serialization does not imply transmission | **Narrowed by current bytecode.** The worker selects app-related roots and conditionally schedules a sample report; whole-device scanning and actual upload remain unestablished. |
| Arbitrary remote command execution through push | Push handler, names containing “CommandExecutor” and configuration keys | No demonstrated route from push input to an arbitrary OS command or executable action | **Withdrawn as a finding.** Further call-path review would be needed. |
| `SYSTEM_ALERT_WINDOW` is a current critical risk | Permission listed in March 2026 report | Version-specific declaration was not rechecked | **Not present** in the examined base APK manifest. This does not describe older or other-channel builds. |
| `REQUEST_INSTALL_PACKAGES` proves silent app installation | Manifest permission and installer-related symbols | No reachable installation flow, bypass of user approval or installed package observed | **Capability declaration only.** No installation finding. |
| Contacts are accessed only after user confirmation | Selected UI excerpts | Other code paths and runtime behavior were not exhaustively checked | **Unverified.** This study does not claim absence of background contact use. |
| Cleartext network policy proves insecure traffic | Allowlist in `network_security_config.xml` | No network capture demonstrating HTTP requests to these domains | **Confirmed policy allowance; traffic unobserved.** |
| No system command execution exists | No hit in a limited `Runtime.exec` pattern scan | Partial search cannot prove absence of equivalent mechanisms | **Corrected.** A fixed `logcat` command is present in the examined bytecode; no arbitrary remote command path is established. |

Every current statement must identify its evidence tier: **manifest declaration**, **code/string presence**, **reachable call path**, or **runtime observation**. The [technical report](../android_analysis/TECHNICAL_REPORT.md) applies this distinction.
