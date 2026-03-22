# Executive Summary: MAX (ru.oneme.app)

**Дата анализа:** March 21, 2026  
**Пакет:** ru.oneme.app  
**Версия приложения:** 26.9.1 (6643)  
**Дата файла APK:** 2026-03-21 20:10:18 +0800  
**RuStore update date:** 2026-03-18T15:36:40.580+00:00

## Краткий вывод

Приложение MAX выглядит как легитимный мессенджер крупной платформы, но обладает расширенным набором чувствительных разрешений и функций. Признаков примитивного malware-класса или прямого выполнения системных команд в текущем статическом анализе не обнаружено. При этом остаются важные риски высокого приоритета: overlay, установка APK, автозапуск после перезагрузки, захват экрана и ослабленная сетевая политика для части доменов.

## Приоритеты рисков

### P1

1. `SYSTEM_ALERT_WINDOW`
2. `REQUEST_INSTALL_PACKAGES`
3. `FOREGROUND_SERVICE_MEDIA_PROJECTION` и screen-sharing stack

### P2

1. Доступ к контактам (`READ_CONTACTS`, `WRITE_CONTACTS`)
2. Автозапуск (`RECEIVE_BOOT_COMPLETED`)
3. `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
4. `ACCESS_FINE_LOCATION`, `CAMERA`, `RECORD_AUDIO`
5. Сбор списка установленных приложений и аналитический telemetry flow
6. Чтение внешнего хранилища и построение карты файловой системы

### P3

1. Cleartext allowlist для отдельных операторских доменов
2. `WebView.addJavascriptInterface(...)` без подтвержденной exploit-цепочки
3. Channel-specific permission deltas между RuStore/device build и Huawei-oriented APK

## Что изменилось относительно 2024

1. Подтверждена актуальная сборка `26.9.1 (6643)` с брендом MAX.
2. Часть ранее чувствительных прав исчезла из актуального манифеста:
   - `READ_PHONE_NUMBERS`
   - `DISABLE_KEYGUARD`
3. Storage model частично обновлен под Android 13+:
   - `READ_MEDIA_IMAGES`
   - `READ_MEDIA_VIDEO`
   - `READ_MEDIA_VISUAL_USER_SELECTED`
4. Новые важные акценты текущего анализа:
   - `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`
   - cleartext policy для операторских доменов
   - подтвержденный MediaProjection/screenshare surface

## Сравнение каналов поставки

Сравнение Huawei-oriented APK и RuStore/device build показало:

1. Совпадает `versionName`, `versionCode`, `minSdk`, `targetSdk`.
2. Полностью совпадает сертификат подписи.
3. Совпадает `network_security_config`, включая cleartext allowlist.
4. Различаются некоторые permissions по каналу дистрибуции:
   - RuStore/device build: Google/FCM и install-referrer related permissions
   - Huawei-oriented APK: Huawei push/keystore/commondata related permissions

Вывод: это похоже на channel-specific build variance, а не на смену разработчика или вредоносную подмену.

## Практический вывод

1. Это не выглядит как типичный троян или spyware с прямым shell execution.
2. Это выглядит как функционально тяжелый мессенджер с высоким уровнем привилегий и широким telemetry/feature surface.
3. Основной риск для пользователя связан не с явным malware-pattern, а с объемом полномочий, доступом к данным и системным возможностям приложения.

## Рекомендации

1. Не выдавать лишние разрешения без реальной необходимости.
2. Избегать разрешения на установку APK и overlay, если это не требуется.
3. Проверить приложение динамически: MITM, WebView flows, certificate pinning, screen capture behavior.
4. Учитывать store-channel differences при корпоративной оценке риска.