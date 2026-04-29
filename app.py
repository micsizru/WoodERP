from app import create_app

"""
WoodERP - Standart Calistirma Modulu
------------------------------------
Bu dosya projenin resmi giris noktasidir. 
Sektör standartlarina uygundur (Clean Architecture).

Calistirmak icin:
1. venv aktif edin: venv\Scripts\activate
2. Uygulamayi baslatin: python app.py
"""

app = create_app()

if __name__ == "__main__":
    # Geliştirme modu
    app.run(debug=True, host="0.0.0.0", port=5000)
