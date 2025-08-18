# Permission Analysis: ru.oneme.app

## Critical Permission Investigation

### REQUEST_INSTALL_PACKAGES Permission 🚨

**Risk Level: CRITICAL**

#### What We Found

The app requests `REQUEST_INSTALL_PACKAGES` permission to handle APK files shared through messages.

#### Code Evidence

```java
// From defpackage/v3c.java
if (!"application/vnd.android.package-archive".equals(strQ)) {
    // Handle normal files
} else {
    // Handle APK files specifically
    try {
        if (context.getPackageManager().canRequestPackageInstalls()) {
            nd7.Q(new nm(context, i));  // Install APK directly
        }
    } catch (SecurityException e) {
        if (e.toString().contains("REQUEST_INSTALL_PACKAGES")) {
            // Fallback to file browser
            Intent intent2 = new Intent("android.intent.action.GET_CONTENT");
            context.startActivity(intent2);
        }
    }
}
```

#### App Warning Message (Russian)

```xml
<string name="apk_install_warning">
Установка APK-файлов не разрешена для приложения. 
Вы можете разрешить установку в настройках.
</string>
```

**Translation:** "Installation of APK files is not allowed for the application. You can allow installation in settings."

#### Security Implications

🔴 **CRITICAL RISKS:**
1. **Malware Distribution Vector** - Can install any APK shared in messages
2. **Bypasses App Store Security** - Circumvents Google Play protection
3. **Social Engineering Potential** - Users may unknowingly install malicious apps
4. **Direct Installation** - No user verification for APK authenticity

#### Comparison with Legitimate Apps

| App | REQUEST_INSTALL_PACKAGES |
|-----|-------------------------|
| WhatsApp | ❌ No |
| Telegram | ❌ No |
| Signal | ❌ No |
| OneMe | ✅ **YES** |

#### Recommendation

**🚨 DO NOT GRANT THIS PERMISSION**

This permission creates a significant security vulnerability. Most legitimate messaging apps do not require this permission for normal operation.

---

### RECEIVE_BOOT_COMPLETED Permission ✅

**Risk Level: LOW (Legitimate)**

#### Purpose
Auto-starts notification service for message delivery after device reboot.

#### Code Evidence
```java
// From BootCompletedReceiver.java
if ("android.intent.action.BOOT_COMPLETED".equals(intent.getAction())) {
    jyc jycVarD = np8.D(context);
    jycVarD.p().a().execute(new b(18, jycVarD));  // Start NotificationTamService
}
```

#### Verdict
Standard behavior for messaging apps to ensure reliable message notifications.

---

## Overall Assessment

The `REQUEST_INSTALL_PACKAGES` permission is the most concerning aspect of this application. While the app appears to be a legitimate messaging service, this permission creates an unacceptable security risk for most users.

**Final Recommendation:** Avoid using this app or deny the installation permission if you must use it.
