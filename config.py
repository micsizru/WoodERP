import os
import platform

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # TR: Geliştirme aşamasında kolaylık olması için geçici olarak burada; canlıya geçişte çevre değişkenlerine (env) taşınacak.
    # RU: Временно здесь для удобства разработки; при переходе в продакшн будет перенесено в переменные окружения.
    SECRET_KEY = "wood-erp-secret-key-2026"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "veritabani.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False