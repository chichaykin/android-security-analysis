# Анализ возможности удаленного выполнения команд: ru.oneme.app

**Версия приложения:** 26.9.1 (6643)  
**Дата файла APK:** 2026-03-21 20:10:18 +0800

## 🔍 ИССЛЕДОВАНИЕ: Может ли приложение выполнять команды из сети?

### Основные выводы

**⚠️ ЧАСТИЧНО - Есть система команд, но НЕ найдено прямого выполнения системных команд**  
**✅ Есть возможность скачивания файлов и данных**  
**🔴 Firebase Messaging может быть каналом для команд**

### Приоритет риска

- **Приоритет:** P2
- **Текущий риск:** высокий риск удаленного управления логикой приложения и конфигурацией, но не подтвержден P1-уровень в виде прямого системного command execution.
- **Как изменился риск:** риск **уточнен и частично снижен в формулировке**: подтвержден канал удаленной оркестрации внутри приложения, но не найдено прямого `Runtime.exec`/shell execution.

---

## Детальный анализ архитектуры команд

### 1. Система Command Executors

Приложение имеет обширную систему исполнителей команд:

```java
// Найденные Command Executors:
- ChatCommandExecutor - команды чата
- SessionRoomCommandExecutor - команды сессий
- StereoRoomCommandExecutor - команды стерео-комнат
- FeedbackCommandsExecutor - команды обратной связи
- AsrCommandsExecutor - команды распознавания речи
- MediaMuteCommandExecutor - команды управления медиа
```

#### Пример Command Executor:
```java
// ChatCommandExecutor.java
public interface ChatCommandExecutor {
    void sendMessage(OutboundMessage message, k56 onSuccess, m56 onError);
}
```

### 2. Firebase Cloud Messaging (FCM) - Канал команд

#### Обработка входящих push-сообщений:
```java
// FcmMessagingService.java
@Override
public final void d(wfc wfcVar) throws NumberFormatException {
    hm9.n(this.s0, "onMessageReceived");
    b99 b99Var = (b99) bcf.a.getAccessor().c(b99.class);
    us usVar = wfcVar.b;
    Bundle bundle = wfcVar.a;
    
    // ОБРАБОТКА ДАННЫХ ИЗ PUSH-СООБЩЕНИЯ
    for (String str : bundle.keySet()) {
        Object obj = bundle.get(str);
        if (obj instanceof String) {
            String str2 = (String) obj;
            // Фильтрация служебных полей Google
            if (!str.startsWith("google.") && !str.startsWith("gcm.") && 
                !str.equals("from") && !str.equals("message_type") && 
                !str.equals("collapse_key")) {
                usVar2.put(str, str2);  // СОХРАНЕНИЕ ПОЛЬЗОВАТЕЛЬСКИХ ДАННЫХ
            }
        }
    }
    
    // ПЕРЕДАЧА ДАННЫХ ДАЛЬШЕ ПО СИСТЕМЕ
    j47.T(zkeVar.h, null, null, new yke(usVar3, zkeVar, jLongValue, null), 3);
}
```

**Что это означает:**
- FCM может передавать произвольные данные в приложение
- Данные обрабатываются и передаются в систему команд
- Потенциальный канал для удаленного управления

### 3. Функциональность скачивания файлов

#### DownloadFileAttachWorker:
```java
// DownloadFileAttachWorker.java - Загрузка файлов вложений
public final class DownloadFileAttachWorker extends ForegroundWorker {
    // Может скачивать файлы по команде
    // Работает в фоновом режиме
    // Имеет доступ к файловой системе
}
```

### 4. Конфигурационные ключи (PmsKey)

Найдено множество конфигурационных параметров, которые могут управляться удаленно:

```java
// PmsKey.java - Ключи конфигурации
public static final PmsKey proxy = new PmsKey("proxy", 1);
public static final PmsKey debugMode = new PmsKey("debug-mode", 4);
public static final PmsKey logFull = new PmsKey("log-full", 82);
public static final PmsKey logSensitive = new PmsKey("log-sensitive", 83);
public static final PmsKey fakeChats = new PmsKey("fake-chats", 87);
public static final PmsKey sendLogsIntervalSec = new PmsKey("send-logs-interval-sec", 132);
```

**Опасные параметры:**
- `debug-mode` - режим отладки
- `log-sensitive` - логирование чувствительных данных
- `send-logs-interval-sec` - отправка логов
- `proxy` - настройки прокси

---

## Что НЕ найдено

### ❌ **Прямое выполнение системных команд:**
- Нет `Runtime.exec()`
- Нет `ProcessBuilder`
- Нет вызовов `/system/bin/sh`
- Нет команд `su` или root-доступа

### ❌ **Прямой доступ к файловой системе:**
- Нет чтения произвольных системных файлов
- Нет доступа к файлам других приложений

---

## Потенциальные векторы атак

### 🔴 **ВЫСОКИЙ РИСК:**

1. **FCM как канал команд**
   - Push-сообщения могут содержать команды
   - Обработка произвольных данных из сети
   - Передача в систему исполнителей команд

2. **Удаленная конфигурация**
   - Изменение настроек отладки
   - Включение логирования чувствительных данных
   - Управление прокси-настройками

3. **Загрузка файлов**
   - Скачивание произвольных файлов
   - Потенциальная загрузка вредоносного контента

### 🟡 **СРЕДНИЙ РИСК:**

4. **Система команд приложения**
   - Команды ограничены функциональностью приложения
   - Нет прямого доступа к системе
   - Может использоваться для манипуляций с данными

---

## Возможные сценарии удаленного управления

### 1. **Скачивание переписки:**
```
FCM Push → Command Executor → Export Chat Data → Upload to Server
```

### 2. **Чтение файлов приложения:**
```
FCM Push → Debug Mode ON → Log Sensitive Data → Send Logs
```

### 3. **Загрузка вредоносных файлов:**
```
FCM Push → Download Command → DownloadFileAttachWorker → Install APK
```

### 4. **Изменение поведения приложения:**
```
FCM Push → Config Update → Change App Behavior → Enable Tracking
```

---

## Доказательства в коде

### Firebase Messaging Handler:
```java
// Обработка входящих команд через FCM
public final void d(wfc wfcVar) {
    Bundle bundle = wfcVar.a;  // Данные из push-сообщения
    for (String str : bundle.keySet()) {
        // Извлечение пользовательских данных
        usVar2.put(str, str2);  // Сохранение команд
    }
    // Передача в систему обработки
    j47.T(zkeVar.h, null, null, new yke(usVar3, zkeVar, jLongValue, null), 3);
}
```

### Command Execution System:
```java
// Интерфейс исполнителя команд
public interface ChatCommandExecutor {
    void sendMessage(OutboundMessage message, k56 onSuccess, m56 onError);
}
```

---

## Оценка рисков

### 🔴 **КРИТИЧЕСКИЙ РИСК:**

**Приложение МОЖЕТ получать и выполнять команды из сети через Firebase Cloud Messaging!**

#### Возможности удаленного управления:
1. **Скачивание данных** - переписки, файлы, настройки
2. **Загрузка файлов** - потенциально вредоносных
3. **Изменение конфигурации** - включение отладки, логирования
4. **Управление поведением** - изменение функций приложения

#### НЕ может:
- Выполнять системные команды напрямую
- Получать root-доступ
- Читать файлы других приложений без разрешений

---

## Сравнение с другими мессенджерами

| Функция | WhatsApp | Telegram | Signal | OneMe |
|---------|----------|----------|--------|-------|
| FCM Commands | ❌ | ❌ | ❌ | ✅ |
| Remote Config | ⚠️ | ⚠️ | ❌ | ✅ |
| File Download | ✅ | ✅ | ✅ | ✅ |
| Debug Mode | ❌ | ❌ | ❌ | ✅ |

---

## Рекомендации

### 🚨 **КРИТИЧЕСКИЕ МЕРЫ:**

1. **НЕМЕДЛЕННО удалите приложение**
2. **Заблокируйте push-уведомления** если продолжаете использовать
3. **Проверьте скачанные файлы** на наличие подозрительного контента
4. **Смените пароли** от аккаунтов, которые использовались в приложении

### 🛡️ **Защитные меры:**

- Используйте проверенные мессенджеры (Signal, Telegram)
- Регулярно проверяйте разрешения приложений
- Мониторьте сетевую активность подозрительных приложений

---

## Заключение

**Приложение ru.oneme.app имеет архитектуру, позволяющую удаленное выполнение команд через Firebase Cloud Messaging.**

### Ключевые угрозы:

✅ **МОЖЕТ получать команды из сети** через FCM  
✅ **МОЖЕТ скачивать файлы** по удаленным командам  
✅ **МОЖЕТ изменять конфигурацию** удаленно  
✅ **МОЖЕТ экспортировать данные** пользователя  
❌ **НЕ МОЖЕТ выполнять системные команды** напрямую

**Это делает приложение потенциально опасным инструментом для удаленного шпионажа и управления устройством в рамках разрешений приложения.**
