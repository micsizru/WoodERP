import sys
import os
import subprocess
from app import create_app

def ensure_venv():
    """Sanal ortamın (venv) aktif olup olmadığını kontrol eder, değilse otomatik aktif eder."""
    executable = sys.executable.lower()
    if "venv" in executable or ".venv" in executable:
        return

    basedir = os.path.dirname(os.path.abspath(__file__))
    for venv_name in ["venv", ".venv"]:
        if os.name == "nt": # Windows
            python_exe = os.path.join(basedir, venv_name, "Scripts", "python.exe")
        else: # Unix/Linux/Mac
            python_exe = os.path.join(basedir, venv_name, "bin", "python")
            
        if os.path.exists(python_exe):
            try:
                result = subprocess.call([python_exe] + sys.argv)
                sys.exit(result)
            except Exception:
                sys.exit(1)

if __name__ == "__main__":
    ensure_venv()
    
    app = create_app()
    
    # Geliştirme modu
    print("\n[+] WoodERP Baslatiliyor...")
    app.run(debug=True, host="0.0.0.0", port=5000)
