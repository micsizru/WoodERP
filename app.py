import sys
import os
import subprocess

# ---------------------------------------------------------------------------
#  WoodERP - Tek Giriş Noktası (Universal Entry Point)
# ---------------------------------------------------------------------------
#  Bu dosya hem PythonAnywhere (WSGI import) hem de local geliştirme
#  (python app.py) için çalışır.
#
#  PythonAnywhere wsgi.py dosyası bu dosyadan "app" nesnesini import eder.
#  Local'de doğrudan çalıştırıldığında otomatik venv algılama yapar.
# ---------------------------------------------------------------------------

def _ensure_venv():
    """
    Eğer script, sanal ortam (venv) dışından çalıştırılmışsa,
    projedeki venv'i otomatik bulur ve kendisini onunla yeniden başlatır.
    Eğer venv bulunamazsa mevcut Python ile devam eder.
    """
    executable = sys.executable.lower()
    if "venv" in executable or ".venv" in executable:
        return  # Zaten venv içindeyiz, devam et.

    basedir = os.path.dirname(os.path.abspath(__file__))
    for venv_name in ["venv", ".venv"]:
        if os.name == "nt":  # Windows
            python_exe = os.path.join(basedir, venv_name, "Scripts", "python.exe")
        else:  # Unix / Linux / Mac
            python_exe = os.path.join(basedir, venv_name, "bin", "python")

        if os.path.exists(python_exe):
            try:
                result = subprocess.call([python_exe] + sys.argv)
                sys.exit(result)
            except Exception as e:
                print(f"\n[HATA] Sanal ortam ile calistirma basarisiz: {e}")
                input("\nCikmak icin Enter'a basin...")
                sys.exit(1)

    # venv bulunamadı - mevcut Python ile devam et
    print("[!] Sanal ortam bulunamadi, sistem Python'u ile devam ediliyor.")


# ---------------------------------------------------------------------------
#  Doğrudan Çalıştırma (python app.py)
#  ÖNCELİKLE venv kontrolü yapılır, SONRA uygulama yüklenir.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _ensure_venv()

    try:
        from app import create_app
        app = create_app()

        print("\n" + "=" * 50)
        print("   WoodERP - Modern Kereste Yonetim Sistemi")
        print("=" * 50)
        print(f"[+] Adres: http://localhost:5000")
        print("[!] Durdurmak icin: CTRL+C\n")

        app.run(debug=True, host="0.0.0.0", port=5000)

    except ImportError as e:
        print(f"\n[HATA] Eksik kutuphane: {e}")
        input("\nCikmak icin Enter'a basin...")
    except Exception as e:
        print(f"\n[KRITIK HATA]: {e}")
        input("\nCikmak icin Enter'a basin...")

# ---------------------------------------------------------------------------
#  WSGI Import (PythonAnywhere / Gunicorn / vb.)
#  wsgi.py bu dosyayı import ettiğinde __name__ == "__main__" OLMAZ,
#  bu blok çalışır ve "app" nesnesi hazır olur.
# ---------------------------------------------------------------------------
else:
    from app import create_app
    app = create_app()
