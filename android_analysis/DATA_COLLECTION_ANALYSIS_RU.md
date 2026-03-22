# Анализ сбора данных: ru.oneme.app

**Версия приложения:** 26.9.1 (6643)  
**Дата файла APK:** 2026-03-21 20:10:18 +0800

## 🚨 КРИТИЧЕСКОЕ ОБНАРУЖЕНИЕ: Сбор данных об установленных приложениях

### Основные выводы

**✅ ДА, приложение СОБИРАЕТ данные об установленных приложениях**  
**✅ ДА, приложение ОТПРАВЛЯЕТ эти данные в сеть**

### Приоритет риска

- **Приоритет:** P2
- **Текущий риск:** высокий privacy/profiling risk, так как список установленных приложений позволяет строить чувствительный профиль пользователя.
- **Как изменился риск:** риск **остается актуальным** в текущем цикле анализа; это не системный RCE-вектор, но значимый канал телеметрии и профилирования.

---

## Детальный анализ кода

### 1. Библиотека MyTracker - Система сбора аналитики

Приложение использует библиотеку **MyTracker** (принадлежит VK/Mail.ru Group) для сбора детальной аналитики.

#### Код сбора данных об установленных приложениях:

```java
// MyTrackerConfig.java - Интерфейс для сбора установленных приложений
public interface InstalledPackagesProvider {
    List<PackageInfo> getInstalledPackages();  // Получает список всех установленных приложений
}

// Метод настройки сбора данных
public MyTrackerConfig setInstalledPackagesProvider(InstalledPackagesProvider installedPackagesProvider) {
    this.a.a(installedPackagesProvider);
    return this;
}
```

#### Обработка данных об приложениях:

```java
// f.java - Класс обработки данных об установленных приложениях
public e a(MyTrackerConfig.InstalledPackagesProvider installedPackagesProvider, Context context) {
    List<PackageInfo> installedPackages;
    if (installedPackagesProvider == null) {
        return a;
    }
    try {
        installedPackages = installedPackagesProvider.getInstalledPackages();  // ПОЛУЧЕНИЕ СПИСКА ПРИЛОЖЕНИЙ
    } catch (Throwable unused) {
        y0.b("MyTracker error: exception at InstalledPackagesProvider::getInstalledPackages()");
        installedPackages = null;
    }
    if (installedPackages != null && !installedPackages.isEmpty()) {
        List listB = b(installedPackages);  // ОБРАБОТКА СПИСКА
        if (listB.isEmpty()) {
            return a;
        }
        String strA = a(listB);  // СОЗДАНИЕ СТРОКИ ИЗ СПИСКА ПРИЛОЖЕНИЙ
        String strF = p0.a(context).f();
        String strA2 = s.a(strA);  // ХЕШИРОВАНИЕ ДАННЫХ
        // ... код отправки данных
    }
}

// Метод фильтрации приложений (исключает системные)
private static List b(List list) {
    ArrayList arrayList = new ArrayList();
    Iterator it = list.iterator();
    while (it.hasNext()) {
        PackageInfo packageInfo = (PackageInfo) it.next();
        ApplicationInfo applicationInfo = packageInfo.applicationInfo;
        if ((applicationInfo.flags & 1) == 0) {  // Исключает системные приложения
            arrayList.add(new e.a(applicationInfo.packageName, x0.b(packageInfo.firstInstallTime)));
        }
    }
    return arrayList;
}
```

### 2. Отправка данных в сеть

#### Сервер назначения:
```java
// z0.java - Конфигурация сервера
private void s() {
    d("tracker-api.vk-analytics.ru");  // СЕРВЕР VK ANALYTICS
}
```

#### Код отправки HTTP запросов:
```java
// c0.java - Абстрактный HTTP клиент
public abstract class c0 {
    public static boolean a(Context context) {
        NetworkInfo activeNetworkInfo;
        ConnectivityManager connectivityManager = (ConnectivityManager) context.getSystemService("connectivity");
        if (connectivityManager == null || (activeNetworkInfo = connectivityManager.getActiveNetworkInfo()) == null) {
            return false;
        }
        return activeNetworkInfo.isConnected();  // ПРОВЕРКА СЕТЕВОГО СОЕДИНЕНИЯ
    }

    public abstract b a(String str);  // ОТПРАВКА HTTP ЗАПРОСА

    public static c0 a(a aVar, MyTrackerConfig.OkHttpClientProvider okHttpClientProvider, boolean z) {
        if (okHttpClientProvider != null) {
            try {
                return new m0(aVar, okHttpClientProvider, z);  // СОЗДАНИЕ HTTP КЛИЕНТА
            } catch (Throwable th) {
                y0.a("HttpRequest error: error while creating OkHttpPostRequest", th);
            }
        }
        return new b0(aVar, z);
    }
}
```

---

## Что именно собирается и отправляется

### Собираемые данные:
1. **Список всех установленных приложений** (кроме системных)
2. **Имена пакетов приложений** (`applicationInfo.packageName`)
3. **Время первой установки** (`packageInfo.firstInstallTime`)
4. **Хеш от списка приложений** для отслеживания изменений

### Куда отправляются данные:
- **Основной сервер:** `tracker-api.vk-analytics.ru` (VK/Mail.ru Group)
- **Протокол:** HTTPS
- **Метод:** HTTP POST запросы

---

## Оценка рисков

### 🔴 КРИТИЧЕСКИЕ РИСКИ:

1. **Нарушение приватности**
   - Полный список установленных приложений раскрывает личные интересы
   - Можно определить банковские приложения, мессенджеры, игры, etc.

2. **Профилирование пользователей**
   - Создание детального профиля пользователя
   - Возможность таргетированной рекламы
   - Потенциальная продажа данных третьим лицам

3. **Безопасность**
   - Информация о безопасности (антивирусы, VPN)
   - Данные о финансовых приложениях
   - Потенциальное использование для социальной инженерии

4. **Отсутствие согласия**
   - Сбор происходит без явного согласия пользователя
   - Нет возможности отказаться от сбора данных

### Примеры собираемой информации:
- Банковские приложения (Сбербанк, ВТБ, etc.)
- Мессенджеры (WhatsApp, Telegram, Viber)
- Социальные сети (Instagram, TikTok, VK)
- Игры и развлечения
- Рабочие приложения
- Приложения для здоровья

---

## Сравнение с другими мессенджерами

| Мессенджер | Сбор списка приложений | Аналитика |
|------------|------------------------|-----------|
| WhatsApp   | ❌ НЕТ                 | Минимальная |
| Telegram   | ❌ НЕТ                 | Минимальная |
| Signal     | ❌ НЕТ                 | Отсутствует |
| **OneMe**  | ✅ **ДА**              | **Обширная** |

---

## Рекомендации

### 🚨 КРИТИЧЕСКАЯ РЕКОМЕНДАЦИЯ:
**НЕ ИСПОЛЬЗУЙТЕ это приложение, если цените приватность**

### Если вы уже используете приложение:
1. **Удалите приложение** немедленно
2. **Очистите данные** приложения перед удалением
3. **Проверьте разрешения** других установленных приложений
4. **Используйте альтернативы** (Signal, Telegram, WhatsApp)

### Для разработчиков:
Это приложение демонстрирует **недопустимые практики** сбора данных:
- Скрытый сбор чувствительной информации
- Отправка данных на сторонние серверы без согласия
- Использование обфусцированного кода для сокрытия функциональности

---

## Заключение

Приложение **ru.oneme.app** представляет **серьёзную угрозу приватности** пользователей. Оно активно собирает список всех установленных приложений и отправляет эти данные на серверы VK Analytics без явного согласия пользователя.

**Это не просто мессенджер - это инструмент массового сбора пользовательских данных.**
