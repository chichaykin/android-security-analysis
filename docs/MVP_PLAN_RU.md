# MVP Plan: Behavioral APK Analysis Tool

## Контекст

Репозиторий уже содержит результаты статического анализа Android-приложений и вспомогательные скрипты для сбора артефактов. Следующий логичный шаг — собрать минимально жизнеспособный инструментарий, который подтверждает или опровергает статические находки на запущенном APK и формирует воспроизводимые evidence-паки.

Цель MVP — не "полностью автоматизировать mobile pentest", а сократить путь от APK к проверяемому runtime-отчету по ключевым рискам: сетевое поведение, интенты, разрешения, обновления, WebView и чувствительные capability flows.

## Продуктовая гипотеза

Если дать AppSec-команде или исследователю инструмент, который:

1. устанавливает APK в чистый Android emulator;
2. автоматически прогоняет базовые сценарии;
3. собирает сетевые, UI и системные артефакты;
4. сопоставляет их со статическими сигналами;
5. выдает короткий, воспроизводимый отчет с evidence;

то такой инструмент будет полезен как минимум для:

1. первичной triage-проверки release APK без исходников;
2. проверки гипотез из статического анализа;
3. regression-проверок новых сборок;
4. подготовки материалов для ручного review или pentest.

## Что входит в MVP

### Основной scope

1. Установка APK и запуск в чистом эмуляторе Android.
2. Базовый UI automation для холодного старта, onboarding и переходов по deep links.
3. Сбор `logcat`, скриншотов, `dumpsys` и сетевых артефактов.
4. Проверка runtime permissions в сценариях `allow` / `deny` / `revoke`.
5. Проверка exported components и внешних `intent`-точек входа.
6. Проверка update/install flow на уровне observable behavior.
7. Проверка cleartext/TLS behavior в тестовой среде.
8. Генерация одного итогового отчета в Markdown или HTML.

### Что сознательно не входит в MVP

1. Полная поддержка физических устройств и device farm.
2. Обход anti-emulation, anti-debugging и certificate pinning любой ценой.
3. Полная автоавторизация во всех сложных login flow.
4. Поддержка iOS.
5. Мультитенантный SaaS, billing, RBAC и enterprise admin-функции.

## Архитектура MVP

### 1. APK Intake

На вход подаются:

1. APK или набор split APK;
2. package name;
3. тестовые deep links и опциональные сценарные параметры;
4. опциональные учетные данные для тестовой среды.

На этом шаге инструмент:

1. сохраняет метаданные сборки;
2. запускает быстрый static pre-pass;
3. вычисляет fingerprint для сравнения повторных запусков.

### 2. Static Pre-pass

Минимальный статический слой нужен не для финального verdict, а для приоритизации рантайм-проверок:

1. manifest permissions;
2. exported components;
3. `network_security_config`;
4. `http://` и update-related строки;
5. `WebView`, `PackageInstaller`, `MediaProjection`, `DexClassLoader` и другие чувствительные маркеры.

Выход этого шага — список runtime hypotheses, которые надо подтвердить или опровергнуть.

### 3. Runtime Orchestrator

Оркестратор отвечает за:

1. поднятие чистого эмулятора из snapshot;
2. установку APK;
3. прокладку proxy / network shaping;
4. запуск сценариев;
5. сбор и сохранение артефактов;
6. teardown и очистку состояния.

### 4. Scenario Runner

Runner должен поддерживать три класса действий:

1. UI actions: tap, text input, wait-for-element, screenshot checkpoints;
2. system actions: `pm grant`, `pm revoke`, `am start`, `am broadcast`, `am startservice`;
3. environment actions: airplane mode, bad TLS cert, proxy on/off, reinstall, reboot.

### 5. Collectors

Для MVP достаточно пяти потоков наблюдения:

1. `logcat`;
2. сетевой capture/proxy logs;
3. screenshots;
4. `dumpsys package`, `dumpsys activity`, `dumpsys jobscheduler`;
5. структурированные события самого раннера.

### 6. Rule Engine

Правила первого уровня:

1. найден реальный cleartext traffic;
2. приложение принимает неверный сертификат в тестовой среде;
3. exported component вызывается извне без ожидаемой защиты;
4. приложение запрашивает чувствительные permissions не по ожидаемому сценарию;
5. update/install flow активируется из runtime path;
6. WebView загружает чувствительные origin или вызывает JS bridge в risky contexts.

### 7. Evidence Report

Формат результата для каждой находки:

1. краткое описание риска;
2. что именно было найдено в статике;
3. что произошло в рантайме;
4. шаги воспроизведения;
5. ссылки на артефакты;
6. confidence и ограничения.

## Что берем из Google tooling

Для MVP максимально используем штатные компоненты Android ecosystem:

1. `adb` для установки APK, shell-команд, логов и системных проверок;
2. Android Emulator как основную среду исполнения;
3. `UI Automator` для базовой автоматизации интерфейса;
4. `Perfetto` как опциональный источник таймлайнов и системных traces;
5. Firebase Test Lab — не для первого спринта, а как опция для масштабирования после локального MVP.

## Что пишем сами

С нуля нужны:

1. orchestration layer;
2. очередь сценариев и управление состоянием эмулятора;
3. runtime hypothesis planner;
4. rule engine;
5. нормальный report generator;
6. слой хранения артефактов;
7. diff между двумя прогонками или сборками.

## План на 12 недель

### Недели 1-2: Foundations

1. Зафиксировать формат входных данных и структуру артефактов.
2. Поднять локальный emulator workflow со snapshot reset.
3. Реализовать install/uninstall/run pipeline.
4. Подготовить базовый static pre-pass.

### Недели 3-4: Runtime Harness

1. Подключить `adb` collectors.
2. Добавить screenshots и `logcat` capture.
3. Завести общий run manifest: start time, package, build hash, scenario list.
4. Сделать первый reproducible smoke run.

### Недели 5-6: Scenario Engine

1. Добавить `UI Automator`-сценарии.
2. Поддержать deep links и exported components.
3. Добавить environment toggles: proxy, offline mode, permission revoke.
4. Оформить DSL или JSON/YAML-формат сценариев.

### Недели 7-8: Security Checks

1. Проверка cleartext traffic.
2. Базовая TLS validation в тестовой среде.
3. Runtime permission tracing.
4. Update/install behavior tracing.
5. Первые WebView-focused checks.

### Недели 9-10: Reporting

1. Собрать единый Markdown/HTML report.
2. Добавить evidence links и replay steps.
3. Добавить diff между статикой и динамикой.
4. Вывести итоговый severity/confidence summary.

### Недели 11-12: Stabilization

1. Повысить устойчивость UI automation.
2. Добавить retry policy и таймауты.
3. Прогнать 3-5 реальных APK на одном и том же пайплайне.
4. Зафиксировать список известных ограничений и backlog post-MVP.

## Команда и трудоемкость

### Минимальная команда

1. 1 engineer на orchestration / backend glue;
2. 1 engineer на Android automation / device runtime;
3. 0.5 AppSec researcher на rules, validation и quality bar.

### Оценка

1. PoC: `2-4` чел.-мес.
2. Рабочий внутренний MVP: `8-15` чел.-мес.
3. Продаваемый Android-only v1: `20-35` чел.-мес.

## Риски MVP

1. UI automation будет flaky без жесткой дисциплины по state reset.
2. Release APK могут детектировать emulator или прокси.
3. Без выделенной тестовой среды TLS-проверки будут давать шум.
4. Легко утонуть в сборе артефактов и не довести rule engine до полезного состояния.
5. Самая частая продуктовая ошибка — пытаться решить слишком широкий класс задач уже в первом релизе.

## Критерии успеха MVP

MVP можно считать успешным, если он:

1. стабильно прогоняет хотя бы 3 типовых APK end-to-end;
2. подтверждает или опровергает ключевые статические находки;
3. формирует воспроизводимый отчет без ручной склейки доказательств;
4. экономит исследователю заметное время на triage;
5. не требует ручного "оживления" пайплайна после каждого второго запуска.

## Post-MVP

После первого работающего релиза в backlog логично поставить:

1. device farm и физические устройства;
2. интеграцию с CI/CD;
3. более умный сценарный crawler;
4. сравнение каналов дистрибуции одной и той же app;
5. compliance packs под MASVS / store policies;
6. private deployment или single-tenant mode;
7. iOS parity только после стабилизации Android pipeline.
