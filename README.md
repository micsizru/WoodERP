# 🌲 WoodERP - Akıllı Kereste Takip Sistemi

## 🇹🇷 WoodERP Nedir?
Geleneksel kereste ticaretinde stok takibi, fiş kayıtları ve müşteri bilgileri genellikle kağıt-kalem veya karmaşık defterler üzerinden yürütülür; bu durum zamanla veri kaybına ve hatalı hesaplamalara yol açabilir. **WoodERP**, bu geleneksel süreçleri tamamen dijitalleştirerek işletmenizi modern bir düzene taşır. Her bir odun cinsini, alınan fişleri ve müşteri bilgilerini tek bir merkezde toplayarak stok durumunu anlık görmenizi sağlar ve tek tuşla profesyonel raporlar oluşturmanıza imkan tanıyarak işletme yönetimini kolaylaştırır.

## 🇷🇺 Что такое WoodERP?
В традиционной торговле древесиной складской учет, регистрация квитанций и данные клиентов часто ведутся на бумаге или в сложных журналах, что со временем может привести к потере данных и ошибкам в расчетах. **WoodERP** полностью цифровизирует эти традиционные процессы, переводя ваш бизнес на современный уровень. Объединяя учет видов древесины, квитанций и данных клиентов в едином центре, система обеспечивает мгновенный контроль остатков и позволяет создавать профессиональные отчеты одним нажатием кнопки.

---


## 🇹🇷 Teknik Mimari ve Uygulama Altyapısı
Bu proje, Flask framework'ü üzerinde **Application Factory (Uygulama Fabrikası)** ve **Blueprint (Modüler Yapı)** desenleri kullanılarak, endüstriyel standartlarda bir ERP altyapısı olarak geliştirilmiştir.

### 🏗️ Sistem Mimarisi ve Katmanlar
1.  **Giriş Noktası (Main Entry):** Proje, kök dizindeki `app.py` üzerinden ayağa kalkar. Bu dosya, tüm konfigürasyonu yöneten ve uygulama nesnesini (app context) oluşturan ana merkezdir.
2.  **Uygulama Fabrikası (App Factory):** `app/__init__.py` dosyası, `create_app()` fonksiyonu ile uygulamanın çalışma anındaki (runtime) instance'ını oluşturur. Bu aşamada:
    *   `config.py` içerisindeki sınıflar üzerinden çevre değişkenleri (environment variables) yüklenir.
    *   `extensions.py` katmanındaki veritabanı (SQLAlchemy) ve göç yönetimi (Flask-Migrate) araçları uygulamaya bağlanır.
3.  **Modüler Blueprint Yapısı:** Uygulama, karmaşıklığı yönetmek için mantıksal bölümlere (Blueprints) ayrılmıştır:
    *   `main`: Genel ana sayfa ve temel yönlendirmeler.
    *   `stoklar`: Envanter yönetimi ve birim bazlı stok takibi.
    *   `fis`: Alış/Satış evraklarının kaydı ve işlenmesi.
    *   `kartlar`: Müşteri, firma ve cari kart yönetimi.
    *   `raporlar`: İşlenen verilerin analiz edilip PDF formatına dönüştürüldüğü raporlama motoru.
4.  **Veri Katmanı (ORM):** `app/models/` dizini altında bulunan Python sınıfları, SQLite veritabanı ile birebir eşleşir. Veri bütünlüğü, tablolar arası ilişkiler (One-to-Many, Many-to-Many) ve yabancı anahtar (Foreign Key) kısıtlamaları ile korunur.

---

## 🇷🇺 Техническая архитектура и инфраструктура
Проект разработан на базе Flask с использованием паттернов **Application Factory** и **Blueprint**, что соответствует промышленным стандартам разработки ERP-систем.

### 🏗️ Архитектура системы
1.  **Точка входа:** Приложение запускается через `app.py` в корневом каталоге.
2.  **Фабрика приложений:** В `app/__init__.py` функция `create_app()` создает экземпляр приложения, подключая конфигурации и расширения (SQLAlchemy, Migrate).
3.  **Модульная структура (Blueprints):** Система разделена на логические блоки для удобства масштабирования (Склады, Квитанции, Карточки, Отчеты).
4.  **Слой данных (ORM):** Модели в `app/models/` обеспечивают связь с базой данных через SQLAlchemy, гарантируя целостность реляционных данных.

---

## 📂 Proje Dizin Yapısı / Структура проекта
```text
WoodERP/
├── app/                  # Paket ana dizini
│   ├── models/           # SQLAlchemy veri modelleri
│   ├── routes/           # Blueprint bazlı rotalar (fis, stoklar, vb.)
│   ├── static/           # CSS & JS (Custom Design System)
│   ├── templates/        # Jinja2 Layout & View katmanı
│   ├── extensions.py     # Paylaşılan eklentiler (db, migrate)
│   └── __init__.py       # App Factory (create_app)
├── app.py                # RESMİ GİRİŞ NOKTASI (Official Entry Point)
├── config.py             # Yapılandırma ayarları
└── migrations/           # DB versiyon kontrolü (Alembic)
```

## 🚀 Kurulum ve Çalıştırma / Установка и запуск
1. `pip install -r requirements.txt`
2. `python app.py`

*(TR: İlk çalıştırmada `veritabani.db` veritabanı dosyası tablolarıyla birlikte otomatik olarak oluşturulacaktır. Ekstra bir veritabanı komutuna gerek yoktur.)*
*(RU: При первом запуске файл базы данных `veritabani.db` вместе с таблицами будет создан автоматически. Дополнительные команды для базы данных не требуются.)*