# 🌲 WoodERP - Clean Architecture Wood Management System

## 🇹🇷 Proje Hakkında (Teknik Detaylar)
WoodERP, ahşap endüstrisi için geliştirilmiş, **Clean Architecture** (Temiz Mimari) prensiplerini temel alan bir kurumsal kaynak planlama sistemidir. Proje, ölçeklenebilirlik ve sürdürülebilirlik amacıyla monolitik yapıdan modüler bir yapıya refactor edilmiştir.

### 🏗️ Mimari Yapı
*   **Separation of Concerns:** Uygulama mantığı (App), Veri modelleri (Models) ve Arayüz (Templates/Static) tamamen birbirinden ayrılmıştır.
*   **Veritabanı Yönetimi:** Flask-Migrate (Alembic) ile veritabanı şeması versiyonlanmaktadır. İlişkisel veri bütünlüğü (Foreign Key constraints) ön plandadır.
*   **Routing:** Flask Blueprints kullanılarak modüler bir rota yönetimi sağlanmıştır.
*   **UI/UX:** Vanilla CSS kullanılarak modern, responsive ve glassmorphism odaklı bir tasarım dili oluşturulmuştur. Harici ağır kütüphaneler yerine optimize edilmiş özel bileşenler tercih edilmiştir.

---

## 🇷🇺 О проекте (Технические детали)
WoodERP — это система планирования ресурсов предприятия для деревообрабатывающей промышленности, построенная на принципах **Clean Architecture**. Проект прошел рефакторинг от монолитной структуры к модульной для обеспечения масштабируемости и удобства поддержки.

### 🏗️ Архитектурная структура
*   **Разделение ответственности (SoC):** Логика приложения (App), модели данных (Models) и интерфейс (Templates/Static) полностью изолированы друг от друга.
*   **Управление БД:** Схема базы данных версионируется с помощью Flask-Migrate (Alembic). Особое внимание уделено реляционной целостности данных.
*   **Маршрутизация:** Модульное управление роутами реализовано через Flask Blueprints.
*   **UI/UX:** Используется современный адаптивный дизайн с акцентом на Glassmorphism, реализованный на чистом CSS без тяжелых внешних библиотек.

---

## 📂 Proje Yapısı / Структура проекта

```text
WoodERP/
├── app/                # Ana uygulama mantığı / Основная логика
│   ├── routes/         # Modüler rotalar / Модульные роуты
│   ├── models/         # Veritabanı modelleri / Модели БД
│   ├── static/         # CSS & JS dosyaları / Статические файлы
│   └── templates/      # Jinja2 şablonları / Шаблоны Jinja2
├── migrations/         # Veritabanı göç kayıtları / Миграции БД
├── config.py           # Konfigürasyon yönetimi / Конфигурация
├── run.py              # Uygulama başlatıcı / Запуск приложения
└── requirements.txt    # Bağımlılıklar / Зависимости
```

## 🛠️ Teknik Gereksinimler / Технические требования
*   **Backend:** Python 3.x, Flask, SQLAlchemy
*   **Database:** SQLite (Alembic for migrations)
*   **Reporting:** PDF Generation utilities
*   **Frontend:** HTML5, CSS3 (Modern UI), Vanilla JS

---

## 🚀 Kurulum / Установка

1. `git clone https://github.com/micsizru/WoodERP.git`
2. `pip install -r requirements.txt`
3. `flask db upgrade` (Veritabanı şemasını oluşturmak için / Для создания схемы БД)
4. `python run.py`