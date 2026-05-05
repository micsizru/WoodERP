# 🌲 WoodERP - Modüler Ahşap Yönetim Sistemi

## 🇹🇷 Proje Uygulama Mantığı ve Teknik Akış
Bu proje, monolitik bir yapının parçalanarak **Uygulama Fabrikası (App Factory)** deseniyle yeniden kurgulanmasıdır. Sistemin çalışma mantığı aşağıdaki teknik temel üzerine kuruludur:

### ⚙️ Uygulama Yaşam Döngüsü
1.  **Başlatma (Bootstrapping):** `run.py` dosyası, `app/__init__.py` içerisindeki `create_app()` fonksiyonunu tetikler. Bu aşamada konfigürasyonlar yüklenir ve SQLAlchemy ORM ile veritabanı bağlantısı kurulur.
2.  **Modüler Rotalama (Blueprints):** Her modül (Stoklar, Raporlar, Fişler) bağımsız birer `Blueprint` olarak tanımlanmıştır. Bu, kodun okunabilirliğini ve bakımını kolaylaştırır.
3.  **İş Mantığı ve Veri İşleme:** 
    *   Kullanıcıdan gelen ham veriler route katmanında karşılanır.
    *   `app/models/` altındaki sınıflar aracılığıyla veritabanı sorguları (ORM) yürütülür.
    *   İlişkisel tablolar (Foreign Keys) kullanılarak, örneğin bir stok girişi yapıldığında ilgili firma ve birim bilgileri otomatik olarak eşleştirilir.
4.  **Sunucu Taraflı Render (Jinja2):** İşlenen veriler, Jinja2 motoru ile HTML şablonlarına gömülerek kullanıcıya ulaştırılır. CSS katmanında özel `root` değişkenleri ile dinamik bir tema yönetimi sağlanmıştır.

---

## 🇷🇺 Логика работы приложения и технический процесс
Проект представляет собой рефакторинг монолитной структуры с использованием паттерна **App Factory**. Логика работы системы основана на следующих технических принципах:

### ⚙️ Жизненный цикл приложения
1.  **Инициализация:** Файл `run.py` запускает функцию `create_app()` в `app/__init__.py`. На этом этапе загружаются конфигурации и устанавливается соединение с БД через SQLAlchemy.
2.  **Модульная маршрутизация (Blueprints):** Каждый модуль (Склады, Отчеты, Квитанции) определен как независимый `Blueprint`.
3.  **Бизнес-логика и обработка данных:** 
    *   Сырые данные от пользователя принимаются на уровне маршрутов (routes).
    *   Запросы к базе данных выполняются через классы в `app/models/` с использованием ORM.
    *   Связанные таблицы (Foreign Keys) обеспечивают автоматическое сопоставление данных.
4.  **Серверный рендеринг (Jinja2):** Обработанные данные передаются в шаблоны HTML через движок Jinja2.

---

## 🛠️ Teknik Envanter
*   **Flask & SQLAlchemy:** Veri yönetimi ve API katmanı.
*   **Alembic:** Veritabanı şema değişikliklerinin (migration) takibi.
*   **Jinja2 & CSS3:** Dinamik arayüz ve modern tasarım dili.

## 🚀 Hızlı Başlangıç
1. `pip install -r requirements.txt`
2. `flask db upgrade`
3. `python run.py`