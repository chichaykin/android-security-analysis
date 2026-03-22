# Security Analysis Report: ru.oneme.app (MAX)

**Analysis Date:** March 21, 2026  
**App Package:** ru.oneme.app  
**App Name:** MAX  
**App Version:** 26.9.1 (6643)  
**APK File Date:** 2026-03-21 20:10:18 +0800  
**Method:** Static analysis of latest APK by package id `ru.oneme.app` (Huawei AppGallery mirror via `apkeep`) plus direct comparison with a RuStore-installed build pulled from a physical Android device.

## Executive Summary

Приложение выглядит как полнофункциональный мессенджер/звонилка с большим набором чувствительных разрешений и интеграций (Google + Huawei экосистемы, в зависимости от канала дистрибуции). Явных сигнатур вредоносного ПО (например, `Runtime.exec` или собственного скрытого загрузчика кода) не выявлено, но сохраняются высокорисковые возможности: overlay, установка пакетов, автозапуск, экранный захват и ослабленная сетевая политика для ряда доменов. Сравнение Huawei-mirror APK и RuStore/device build показало одинаковые версию, signer и базовую security-модель, но небольшие различия в permission surface, связанные с каналом доставки.

## App Information (Current Build)

- **Package Name:** ru.oneme.app
- **Version Name:** 26.9.1
- **Version Code:** 6643
- **APK File Date:** 2026-03-21 20:10:18 +0800
- **RuStore appVerUpdatedAt:** 2026-03-18T15:36:40.580+00:00
- **minSdkVersion:** 26
- **targetSdkVersion:** 35
- **compileSdkVersion:** 36
- **Main Application Class:** one.me.android.OneMeApplication
- **Main Activity:** one.me.android.MainActivity
- **APK size (downloaded):** ~150 MB

## What Changed Since 2024 Report

### Key Updates

1. **App identity evolved:** в UI/строках бренд уже MAX (не OneMe).
2. **Version jump:** текущая проанализированная сборка — `26.9.1 (6643)`.
3. **Permission model updated for Android 13+:**
	- Используются `READ_MEDIA_IMAGES`, `READ_MEDIA_VIDEO`, `READ_MEDIA_VISUAL_USER_SELECTED`.
	- `READ_EXTERNAL_STORAGE` оставлен с `maxSdkVersion=32`.
	- `WRITE_EXTERNAL_STORAGE` оставлен с `maxSdkVersion=29`.
4. **В предыдущем отчете отмечались `READ_PHONE_NUMBERS` и `DISABLE_KEYGUARD`, в текущем манифесте они не обнаружены.**
5. **Новые заметные риски/маркеры:**
	- `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
	- `com.google.android.gms.permission.AD_ID`
	- Разрешенный cleartext-трафик для ряда операторских доменов в `network_security_config`.
6. **Подтверждено сравнение каналов поставки:** RuStore/device build и ранее проанализированный Huawei-based APK имеют одинаковые `versionName`, `versionCode`, `minSdk/targetSdk` и одинаковый сертификат подписи.
7. **Найдены channel-specific differences в permissions:**
	- **Только в RuStore/device base APK:** `com.google.android.c2dm.permission.RECEIVE`, `com.google.android.finsky.permission.BIND_GET_INSTALL_REFERRER_SERVICE`.
	- **Только в ранее проанализированном Huawei-oriented APK:** `android.permission.CHANGE_WIFI_STATE`, `com.huawei.appmarket.service.commondata.permission.GET_COMMON_DATA`, `com.huawei.permission.ACCESS_HW_KEYSTORE`, `ru.oneme.app.permission.PROCESS_PUSH_MSG`, `ru.oneme.app.permission.PUSH_PROVIDER`.
	- Это выглядит как **различие канала дистрибуции**, а не как смена разработчика или сигнатуры.

## Permissions Analysis (Current)

### High Risk

1. `android.permission.SYSTEM_ALERT_WINDOW`
2. `android.permission.REQUEST_INSTALL_PACKAGES`
3. `android.permission.READ_CONTACTS`
4. `android.permission.WRITE_CONTACTS`
5. `android.permission.ACCESS_FINE_LOCATION`
6. `android.permission.CAMERA`
7. `android.permission.RECORD_AUDIO`
8. `android.permission.RECEIVE_BOOT_COMPLETED`
9. `android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
10. `android.permission.FOREGROUND_SERVICE_MEDIA_PROJECTION`

### Medium Risk

1. `android.permission.ACCESS_COARSE_LOCATION`
2. `android.permission.BLUETOOTH_CONNECT`
3. `android.permission.CHANGE_NETWORK_STATE`
4. `android.permission.CHANGE_WIFI_STATE` (обнаружен в Huawei-oriented APK, отсутствует в pulled RuStore/device base APK)
5. `android.permission.WAKE_LOCK`
6. `android.permission.MODIFY_AUDIO_SETTINGS`
7. `android.permission.READ_MEDIA_IMAGES`
8. `android.permission.READ_MEDIA_VIDEO`
9. `android.permission.READ_MEDIA_VISUAL_USER_SELECTED`
10. `android.permission.FOREGROUND_SERVICE_*` (camera/microphone/media/dataSync/mediaProjection)

### Low Risk / Common

1. `android.permission.POST_NOTIFICATIONS`
2. `android.permission.VIBRATE`
3. Launcher badge permissions (Samsung/Huawei/Oppo/HTC/etc.)
4. `com.google.android.gms.permission.AD_ID` (tracking/ads context dependent)

## Component & Attack Surface Analysis

### Exported Components (Notable)

1. `one.me.android.MainActivity` (launcher)
2. `one.me.android.deeplink.LinkInterceptorActivity`
3. `ru.ok.tamtam.android.services.BootCompletedReceiver`
4. `androidx.work.impl.background.systemjob.SystemJobService`
5. `androidx.work.impl.diagnostics.DiagnosticsReceiver` (protected by `android.permission.DUMP`)
6. `androidx.profileinstaller.ProfileInstallReceiver` (protected by `android.permission.DUMP`)
7. Huawei push components (`PushMsgReceiver`, `PushReceiver`, `HmsMsgService`, `PushProvider` with custom permissions)

### Suspicious / Sensitive Patterns

1. **Auto-start path present** (`RECEIVE_BOOT_COMPLETED` + boot receiver).
2. **Overlay capability** (`SYSTEM_ALERT_WINDOW`).
3. **Package installation capability** (`REQUEST_INSTALL_PACKAGES`).
4. **Screen and audio capture stack** (WebRTC + `MediaProjectionService`).
5. **Legacy storage compatibility flag** (`requestLegacyExternalStorage="true"`).

## Channel Comparison (RuStore / Device vs Huawei Mirror)

### Confirmed Matches

1. **Version parity:** обе сборки имеют `26.9.1 (6643)`.
2. **Signer parity:** SHA-256 сертификата подписи совпадает полностью.
3. **SDK parity:** `minSdkVersion=26`, `targetSdkVersion=35`, `compileSdkVersion=36`.
4. **Network policy parity:** `network_security_config` совпадает, включая cleartext allowlist для операторских доменов.

### Observed Differences

1. **RuStore/device build смещен в Google/FCM сторону:** присутствуют `com.google.android.c2dm.permission.RECEIVE` и install-referrer permission.
2. **Huawei-oriented APK содержит Huawei-specific surface:** Huawei keystore/commondata permissions и custom push permissions.
3. **`CHANGE_WIFI_STATE` есть в Huawei-oriented APK, но не найден в pulled RuStore/device base APK.**
4. Эти отличия **не меняют общий risk profile радикально**, но влияют на attack surface конкретного канала дистрибуции.

## Code Analysis Findings

### Runtime Behavior Signals

1. **No direct `Runtime.getRuntime().exec(...)` hit found** in pattern scan.
2. `DexClassLoader`/`PathClassLoader` usages found mostly in Huawei dynamic feature stack.
3. `WebView.addJavascriptInterface(...)` is used (requires runtime testing for injection safety depending on loaded content origin).
4. `PackageInstaller` references found (mainly Huawei update SDK paths + installer/session logic).

### Network & Endpoints

1. App links/URLs in resources indicate official domains:
	- `https://help.max.ru`
	- `https://legal.max.ru/pp`
	- `https://legal.max.ru/ps`
	- `https://max.ru/support`
2. Tracer endpoint found in smali:
	- `https://sdk-api.apptracer.ru`
3. **Network security config allows cleartext traffic** for specific operator domains:
	- `mobileid.megafon.ru`
	- `idgw.mobileid.mts.ru`
	- `he-mc.tele2.ru`
	- `he-mc.t2.ru`
	- `*.beeline.ru`

### Third-Party / Platform Integrations

1. Firebase artifacts present.
2. Google Play Services integration present.
3. Huawei HMS / Update SDK / Push stack present.
4. WebRTC stack present (calls/screenshare/audio capture).
5. AndroidX WorkManager, Room, DataTransport, Material components present.

## Risk Assessment

### Overall Risk Level: **MEDIUM-HIGH**

### Prioritized Risks

#### P1 - Critical

1. **`SYSTEM_ALERT_WINDOW`**
	- **Риск:** overlay/UI deception, поверх других приложений.
	- **Статус относительно 2024:** **сохранился**.
	- **Изменение:** без снижения риска.
2. **`REQUEST_INSTALL_PACKAGES` + `PackageInstaller` paths**
	- **Риск:** установка APK вне store-пайплайна, social engineering vector.
	- **Статус относительно 2024:** **сохранился**.
	- **Изменение:** без снижения риска.
3. **`FOREGROUND_SERVICE_MEDIA_PROJECTION` + WebRTC/screenshare stack**
	- **Риск:** захват экрана и чувствительного контента пользователя.
	- **Статус относительно 2024:** **сохранился / стал более значимым**, так как стек звонков/screenshare явно присутствует.
	- **Изменение:** риск подтвержден в актуальной сборке.

#### P2 - High

1. **`READ_CONTACTS` / `WRITE_CONTACTS`**
	- **Риск:** чтение и модификация контактной книги.
	- **Статус относительно 2024:** **сохранился**.
2. **`RECEIVE_BOOT_COMPLETED` + фоновые сервисы**
	- **Риск:** автозапуск и persistence после перезагрузки.
	- **Статус относительно 2024:** **сохранился**.
3. **`REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`**
	- **Риск:** повышение живучести фоновых процессов и усложнение контроля пользователя.
	- **Статус относительно 2024:** **новый/более явно выраженный маркер**.
4. **`ACCESS_FINE_LOCATION`, `CAMERA`, `RECORD_AUDIO`**
	- **Риск:** сбор чувствительных данных в реальном времени.
	- **Статус относительно 2024:** **сохранился**.

#### P3 - Medium

1. **Cleartext allowlist в `network_security_config`**
	- **Риск:** downgrade/visibility risk для трафика к отдельным операторским доменам.
	- **Статус относительно 2024:** **новый важный нюанс**, явно отраженный в текущей сборке.
2. **`WebView.addJavascriptInterface(...)`**
	- **Риск:** зависит от origin policy и runtime behavior; без динамики не доказывает уязвимость, но требует проверки.
	- **Статус относительно 2024:** **актуален, требует runtime validation**.
3. **`requestLegacyExternalStorage="true"`**
	- **Риск:** расширенный доступ к legacy storage flows.
	- **Статус относительно 2024:** **частично снижен**, так как модель доступа адаптирована под Android 13+ media permissions, но legacy-совместимость все еще включена.
4. **Channel-specific permission deltas (Google/Firebase vs Huawei push stack)**
	- **Риск:** меняют supply-chain surface и набор сторонних интеграций.
	- **Статус:** **изменился по каналу поставки**, но не выглядит как malicious divergence.

### Risk Changes Summary

1. **Риски, которые сохранились:** overlay, package installation, boot persistence, contacts access, camera/microphone/location, media projection.
2. **Риски, которые усилились или стали заметнее:** `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, screenshare/media-projection stack, cleartext policy for operator domains.
3. **Риски, которые уменьшились или исчезли:** `READ_PHONE_NUMBERS` и `DISABLE_KEYGUARD` больше не обнаружены; storage model частично модернизирован под Android 13+.
4. **Риски, зависящие от канала дистрибуции:** Google/Firebase/Install Referrer permissions в RuStore/device build против Huawei-specific permissions в альтернативной сборке.

### Positive Signals

1. Архитектура и стек соответствуют крупному мессенджеру.
2. Нет явных следов примитивной malware-логики в быстрых сигнатурных проверках.
3. Значительная часть «опасных» API связана с ожидаемыми фичами связи/обновлений.

## Recommendations

1. **P1 mitigation:** отключить/запретить `SYSTEM_ALERT_WINDOW`, `REQUEST_INSTALL_PACKAGES` и screen capture flows, если это не требуется вашим сценарием.
2. **P2 mitigation:** минимизировать contacts/location/camera/microphone permissions и контролировать `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`.
3. **P3 mitigation:** проверить сетевое поведение динамически (MITM в тестовой среде с user CA + certificate pinning check), особенно для cleartext-исключений.
4. Отдельно верифицировать WebView-потоки: что именно грузится, откуда, и какие JS bridges доступны.
5. Мониторить фоновые сервисы/автозапуск на устройстве и различия между store channels (RuStore vs Huawei-oriented distribution).

## Conclusion

Текущая сборка `ru.oneme.app` (MAX, `26.9.1`) выглядит как легитимный, но «тяжелый» по полномочиям мессенджер. В сравнении с отчетом 2024 часть старых чувствительных прав больше не заявлена (например, `READ_PHONE_NUMBERS`, `DISABLE_KEYGUARD`), однако ключевые высокоприоритетные риски не исчезли: overlay, package installation, boot persistence и media projection остаются актуальными. Дополнительно подтвержден новый важный нюанс с cleartext-политикой для отдельных доменов и установлено, что RuStore/device build и Huawei-oriented APK различаются по части channel-specific permissions, но имеют одинаковую подпись и одинаковый базовый security profile.

---

*Static analysis only. Для окончательных выводов нужны dynamic analysis, TLS traffic validation, runtime permission tracing и поведенческая проверка обновлений/интентов.*
