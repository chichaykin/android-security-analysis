# Android Security Analysis

This repository contains security analysis tools and reports for Android applications.

## Overview

This project provides comprehensive security analysis of Android APK files, including:

- **Permission Analysis** - Detailed examination of app permissions
- **Code Decompilation** - Static analysis of application logic
- **Malware Detection** - Identification of suspicious patterns
- **Security Reporting** - Comprehensive security assessment reports

## Tools Used

- **apktool** - APK disassembly and resource extraction
- **jadx** - Java decompilation from DEX bytecode
- **adb** - Android Debug Bridge for device communication

## Analysis Reports

### ru.oneme.app Analysis

A comprehensive security analysis of the OneMe messaging application (`ru.oneme.app`).

**Key Findings:**
- **Risk Level:** MEDIUM-HIGH ⚠️
- **Concerning Permissions:** `REQUEST_INSTALL_PACKAGES`, `SYSTEM_ALERT_WINDOW`
- **App Type:** Russian messaging application with extensive system access

📄 **[Full Analysis Report](android_analysis/SECURITY_ANALYSIS_REPORT.md)**

## Usage

1. **Extract APK from device:**
   ```bash
   adb shell pm path <package_name>
   adb pull <apk_path> app.apk
   ```

2. **Analyze permissions:**
   ```bash
   apktool d app.apk -o decoded_app
   cat decoded_app/AndroidManifest.xml
   ```

3. **Decompile code:**
   ```bash
   jadx -d decompiled_app app.apk
   ```

## Security Considerations

⚠️ **Warning:** Always analyze APK files in a secure, isolated environment. Some applications may contain malicious code.

## License

This project is for educational and security research purposes only.
