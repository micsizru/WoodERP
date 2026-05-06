import os
import platform

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "wood-erp-secret-key-2026"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "veritabani.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # PDF Configuration
    if platform.system() == "Windows":
        WKHTMLTOPDF_PATH = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    else:
        WKHTMLTOPDF_PATH = '/usr/bin/wkhtmltopdf'
