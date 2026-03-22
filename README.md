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

### ru.oneme.app Analysis - CRITICAL SECURITY THREAT 🚨

**COMPREHENSIVE SECURITY ANALYSIS REVEALS DANGEROUS SPYWARE-LIKE BEHAVIOR**

#### 🔴 **CRITICAL FINDINGS:**

**Risk Level:** EXTREMELY HIGH - POTENTIAL SPYWARE ⚠️

#### **Major Security Violations Discovered:**

1. **📱 [Mass Data Collection](android_analysis/DATA_COLLECTION_ANALYSIS_RU.md)**
   - **COLLECTS LIST OF ALL INSTALLED APPS** 
   - Sends data to VK Analytics servers (`tracker-api.vk-analytics.ru`)
   - Creates detailed user profiling information

2. **🕵️ [Remote Command Execution](android_analysis/REMOTE_COMMANDS_ANALYSIS_RU.md)**
   - **CAN EXECUTE COMMANDS FROM THE INTERNET** via Firebase Cloud Messaging
   - Command execution system with multiple executors
   - Remote configuration changes (debug mode, logging)
   - Potential for remote data exfiltration

3. **💾 [Complete File System Scanning](android_analysis/SDCARD_ACCESS_ANALYSIS_RU.md)**
   - **RECURSIVELY SCANS ENTIRE SD CARD AND FILE SYSTEM**
   - Creates detailed JSON maps of all user files
   - Accesses photos, documents, downloads, app data
   - Sends file statistics to servers

4. **📞 [Contact Access](android_analysis/CONTACTS_ANALYSIS_RU.md)**
   - Full access to contact database (READ/WRITE)
   - Contact sharing with bots and external services
   - Standard messenger functionality (less concerning)

5. **⚡ [Dangerous Permissions](android_analysis/PERMISSION_ANALYSIS.md)**
   - `REQUEST_INSTALL_PACKAGES` - Can install other apps
   - `SYSTEM_ALERT_WINDOW` - Can display over other apps
   - `RECEIVE_BOOT_COMPLETED` - Auto-starts on device boot

#### **📊 Analysis Statistics:**
- **Total Analysis:** 1,149+ lines of detailed technical documentation
- **Files Analyzed:** 6 comprehensive security reports
- **Code Evidence:** Hundreds of code snippets proving malicious behavior

#### **🎯 VERDICT:**
**THIS IS NOT A MESSENGER - IT'S A COMPREHENSIVE SURVEILLANCE TOOL**

**IMMEDIATE ACTION REQUIRED:** Uninstall immediately and revoke all permissions.

---

### 📄 **Detailed Reports:**
- 🔍 **[Complete Security Overview](android_analysis/SECURITY_ANALYSIS_REPORT.md)** - Initial comprehensive analysis
- 📱 **[Data Collection Analysis](android_analysis/DATA_COLLECTION_ANALYSIS_RU.md)** - App list harvesting (Russian)
- 🕵️ **[Remote Commands Analysis](android_analysis/REMOTE_COMMANDS_ANALYSIS_RU.md)** - Remote execution capabilities (Russian)  
- 💾 **[SD Card Access Analysis](android_analysis/SDCARD_ACCESS_ANALYSIS_RU.md)** - File system scanning (Russian)
- 📞 **[Contacts Analysis](android_analysis/CONTACTS_ANALYSIS_RU.md)** - Contact access investigation (Russian)
- ⚡ **[Permissions Deep Dive](android_analysis/PERMISSION_ANALYSIS.md)** - Dangerous permissions breakdown

## MVP Roadmap

The repository now also includes a product and engineering plan for turning the current analysis workflow into a behavioral APK analysis tool.

- **[MVP Plan (RU)](docs/MVP_PLAN_RU.md)** - Scope, architecture, 12-week roadmap, effort estimates, and post-MVP backlog

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

4. **Collect artifacts from a connected device:**
   ```bash
   ./scripts/pull_oneme_for_analysis.sh
   ```

## Security Considerations

⚠️ **Warning:** Always analyze APK files in a secure, isolated environment. Some applications may contain malicious code.

Raw pulled artifacts and large binary outputs are intentionally kept out of git via `.gitignore`. Store them outside the repository or in dedicated artifact storage.

## License

This project is for educational and security research purposes only.
