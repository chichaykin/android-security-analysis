# Evidence index — 11 October 2026

All APK-derived evidence below concerns MAX `ru.oneme.app`, `26.35.1 (6867)`, installed through `ru.vk.store`. The base APK SHA-256 is `a9a76d5b15f1ed13f0fd368ebbc2cf0bb3c8567d15e4d229944865358d31c5a9`.

| ID | Artifact | Precise locator / method | What it supports |
| --- | --- | --- | --- |
| E01 | [build.json](build.json) | `apks`, version, installer and tool fields | Collected build identity, split hashes and signer consistency |
| E02 | [static-summary.json](static-summary.json) | `manifest_permissions`, `exported_components`, `dex_string_hits` | Declarations and raw byte-string presence; no runtime use implied |
| E03 | [static-summary.network-policy.xml](static-summary.network-policy.xml) | `domain-config`, `cleartextTrafficPermitted`, `includeSubdomains` | Exact decoded network policy |
| E04A–G | [bytecode-excerpts.md](bytecode-excerpts.md) | Raw class/method descriptor and method-output SHA-256 in each section | Selected instructions and connected static paths |
| E05 | [runtime-state.json](runtime-state.json) | Grant/flag and AppOps before/after comparison | Unchanged permission configuration; process presence |
| E08 | [runtime-authenticated.json](runtime-authenticated.json) | S00–S04, exact route configuration hash, fixture hash and per-scenario restoration comparisons | Authenticated launch/background and camera/media refusal/revocation outcomes; bounded guest-wide network metadata |
| E09 | [runtime-microphone.json](runtime-microphone.json) | S05, system prompt, denied grant, composer assertion and restoration | Microphone refusal without granting audio access; exploratory assertion failure disclosed |
| E08/E09-UI | [runtime-ui-excerpts.json](runtime-ui-excerpts.json) | Exact selected nodes and private source hashes | Public minimal camera/media/microphone UI evidence without account or conversation content |
| E07 | [runtime-preauth.json](runtime-preauth.json) | Scenario IDs S00–S04, build hash, capture hashes and restoration comparison | Isolated emulator launch/background observations and bounded network metadata; six permission tests blocked |
| E06 | [validation.json](validation.json) | Recorded checks and results | Reproduction and tooling validation |

The full APKs and unredacted device snapshots are outside Git. Public evidence contains no device serial, installed-package directory token, account identifier, contacts, conversation text, private media or application payload content. Network extracts contain reviewed host metadata only. Original strings and domain names in APK-derived artifacts are retained as evidence.

The summary and bytecode extracts can be reproduced using the commands in the [README](../../README.md) and [methodology](../../docs/METHODOLOGY.md). A different hash requires a new study; a matching version name alone is insufficient.
