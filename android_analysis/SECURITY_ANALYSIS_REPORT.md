# Security Analysis Report: ru.oneme.app

**Analysis Date:** August 18, 2024  
**App Package:** ru.oneme.app  
**App Name:** OneMe  

## Executive Summary

This appears to be a legitimate messaging/communication app (OneMe) with extensive permissions. While the app requests many sensitive permissions, the analysis suggests it's likely a legitimate messaging application similar to Telegram or WhatsApp, rather than malicious software.

## App Information

- **Package Name:** ru.oneme.app
- **Main Application Class:** one.me.android.OneMeApplication
- **Main Activity:** one.me.android.MainActivity
- **Developer:** Appears to be Russian origin (ru domain)
- **App Size:** ~45MB (base APK + split APKs)

## Permissions Analysis

### 🔴 HIGH RISK PERMISSIONS

1. **SYSTEM_ALERT_WINDOW** - Can display over other apps
2. **REQUEST_INSTALL_PACKAGES** - Can request to install other apps
3. **READ_CONTACTS / WRITE_CONTACTS** - Full contact access
4. **ACCESS_FINE_LOCATION** - Precise location tracking
5. **CAMERA** - Camera access
6. **RECORD_AUDIO** - Microphone access
7. **READ_PHONE_NUMBERS** - Access to phone numbers
8. **RECEIVE_BOOT_COMPLETED** - Auto-start on device boot

### 🟡 MEDIUM RISK PERMISSIONS

1. **INTERNET / ACCESS_NETWORK_STATE** - Network communication
2. **BLUETOOTH_CONNECT / BLUETOOTH_ADMIN** - Bluetooth control
3. **CHANGE_WIFI_STATE** - WiFi control
4. **READ_EXTERNAL_STORAGE / WRITE_EXTERNAL_STORAGE** - File system access
5. **WAKE_LOCK** - Keep device awake
6. **DISABLE_KEYGUARD** - Disable lock screen
7. **FOREGROUND_SERVICE_*** - Multiple foreground service types

### 🟢 LOW RISK PERMISSIONS

1. **POST_NOTIFICATIONS** - Send notifications
2. **VIBRATE** - Device vibration
3. Various launcher badge permissions (Samsung, Huawei, etc.)

## Application Components Analysis

### Main Components

1. **MainActivity** - Main app interface
2. **OneMeApplication** - Application initialization
3. **CallServiceImpl** - Video/voice calling functionality
4. **MediaProjectionService** - Screen sharing capability
5. **NotificationTamService** - Notification handling

### Suspicious Indicators

#### ⚠️ CONCERNING PATTERNS

1. **Auto-start capability** - App can start automatically on boot
2. **System overlay permission** - Can display content over other apps
3. **Install packages permission** - Could potentially install other apps
4. **Extensive location permissions** - Fine location access
5. **Media projection** - Screen recording/sharing capability

#### ✅ LEGITIMATE PATTERNS

1. **Messaging app structure** - Contains typical messaging app components
2. **Firebase integration** - Uses standard Google services
3. **Standard Android architecture** - Follows Android development patterns
4. **Call functionality** - Video/voice calling features typical of communication apps

## Code Analysis Findings

### Network Communication
- Uses HTTPS for secure communication
- Integrates with Google Play Services
- Firebase messaging for push notifications

### Data Collection
- Accesses contacts for messaging functionality
- Location access (likely for sharing location in messages)
- Camera/microphone for media messaging and calls

### Third-Party Libraries
- Firebase (Google)
- Google Play Services
- AndroidX libraries (Google)
- LZ4 compression library

## Risk Assessment

### Overall Risk Level: **MEDIUM-HIGH** ⚠️

### Risk Factors:

1. **Extensive Permissions** - App requests many sensitive permissions
2. **Russian Origin** - Domain suggests Russian development
3. **System-level Access** - Can interact with system components
4. **Auto-start Capability** - Runs automatically on boot

### Mitigation Recommendations:

1. **Review Permissions** - Carefully consider which permissions to grant
2. **Monitor Network Traffic** - Use network monitoring tools
3. **Check App Store** - Verify app legitimacy through official stores
4. **Regular Updates** - Keep app updated if using
5. **Alternative Options** - Consider well-established messaging apps

## Conclusion

**ru.oneme.app** appears to be a legitimate messaging application with video calling capabilities, similar to popular apps like Telegram or WhatsApp. However, the extensive permission set and Russian origin warrant caution. The app's functionality seems consistent with a modern messaging platform, but users should be aware of the broad access it requests.

**Recommendation:** If you must use this app, carefully review and limit permissions where possible. Consider using established alternatives like Signal, WhatsApp, or Telegram for sensitive communications.

---

*This analysis was performed using static analysis tools and may not detect all potential security issues. Dynamic analysis and network monitoring are recommended for comprehensive security assessment.*
