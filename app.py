import os
import io
from datetime import datetime, date

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, jsonify, send_file
)
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

# ───────────────────────── App Konfigürasyonu ─────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = "marmara-aydoganlar-secret-key-2026"
basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "veritabani.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ───────────────────────── Veritabanı Modelleri ─────────────────────────

class Fis(db.Model):
    """Sevkiyat üst bilgisi (kamyon/fiş)."""
    __tablename__ = "fis"

    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.Date, nullable=False, default=date.today)
    sevk_eden_cari = db.Column(db.String(200), nullable=False)
    sevk_yeri_fabrika = db.Column(db.String(200), nullable=False)
    sevk_yeri_fis_no = db.Column(db.String(100), nullable=False)
    plaka_no = db.Column(db.String(50), nullable=False)

    # İlişki: Bir fişin birden fazla detay satırı olabilir
    detaylar = db.relationship(
        "FisDetayi", backref="fis", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Fis {self.id} – {self.plaka_no}>"


class FisDetayi(db.Model):
    """Kamyonun içeriği (her bir kalem satırı)."""
    __tablename__ = "fis_detayi"

    id = db.Column(db.Integer, primary_key=True)
    fis_id = db.Column(db.Integer, db.ForeignKey("fis.id"), nullable=False)
    agac_cinsi = db.Column(db.String(100), nullable=False)
    cap = db.Column(db.String(50), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(20), nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    toplam_tutar = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<FisDetayi {self.id} – {self.agac_cinsi}>"


# ───────────────────────── Sabit Dropdown Verileri ─────────────────────────

AGAC_CINSLERI = [
    "kayın odun",
    "çam odun",
    "çam odun (yanık saha)",
    "meşe odun",
    "kavak odun",
    "orman kavağı",
    "kestane odun",
    "çınar odun",
    "söğüt.kib.göb.selvi kavak",
    "kızılağaç-akasya",
    "ıhlamur",
    "diş budak",
]

CAPLER = ["6cm altı", "6-15cm arası", "15 üstü"]

BIRIMLER = ["Ton", "Ster", "m³", "Kg"]


# ───────────────────────── Route'lar ─────────────────────────

@app.route("/")
def index():
    """Dashboard – toplam kayıt sayıları ve ana menü."""
    toplam_fis = Fis.query.count()
    toplam_kalem = FisDetayi.query.count()
    return render_template("index.html", toplam_fis=toplam_fis, toplam_kalem=toplam_kalem)


@app.route("/yeni_fis", methods=["GET"])
def yeni_fis_formu():
    """Yeni fiş oluşturma formu."""
    bugun = date.today().isoformat()
    return render_template(
        "yeni_fis.html",
        bugun=bugun,
        agac_cinsleri=AGAC_CINSLERI,
        capler=CAPLER,
        birimler=BIRIMLER,
    )


@app.route("/yeni_fis", methods=["POST"])
def yeni_fis_kaydet():
    """JSON verisini alıp Fis ve FisDetayi tablolarına kaydeder."""
    try:
        veri = request.get_json()

        # Üst bilgi
        tarih_str = veri.get("tarih", date.today().isoformat())
        tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date()

        yeni_fis = Fis(
            tarih=tarih,
            sevk_eden_cari=veri["sevk_eden_cari"].strip(),
            sevk_yeri_fabrika=veri["sevk_yeri_fabrika"].strip(),
            sevk_yeri_fis_no=veri["sevk_yeri_fis_no"].strip(),
            plaka_no=veri["plaka_no"].strip(),
        )
        db.session.add(yeni_fis)
        db.session.flush()  # id ataması için

        # Detay satırları
        kalemler = veri.get("kalemler", [])
        if not kalemler:
            return jsonify({"durum": "hata", "mesaj": "En az bir kalem satırı eklemelisiniz."}), 400

        for k in kalemler:
            miktar = float(k["miktar"])
            birim_fiyat = float(k["birim_fiyat"])
            toplam_tutar = round(miktar * birim_fiyat, 2)

            detay = FisDetayi(
                fis_id=yeni_fis.id,
                agac_cinsi=k["agac_cinsi"],
                cap=k["cap"],
                miktar=miktar,
                birim=k["birim"],
                birim_fiyat=birim_fiyat,
                toplam_tutar=toplam_tutar,
            )
            db.session.add(detay)

        db.session.commit()
        return jsonify({"durum": "basarili", "mesaj": "Fiş başarıyla kaydedildi.", "fis_id": yeni_fis.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@app.route("/fisleri_goruntule")
def fisleri_goruntule():
    """Kayıtlı tüm fişleri tarih sırasıyla listeler."""
    fisler = Fis.query.order_by(Fis.tarih.desc()).all()
    return render_template("fisleri_goruntule.html", fisler=fisler)


@app.route("/fis_detay/<int:fis_id>")
def fis_detay(fis_id):
    """Tek bir fişin detay sayfası."""
    fis = Fis.query.get_or_404(fis_id)
    genel_toplam = sum(d.toplam_tutar for d in fis.detaylar)
    return render_template("fis_detay.html", fis=fis, genel_toplam=genel_toplam)


@app.route("/fis_sil/<int:fis_id>")
def fis_sil(fis_id):
    """Fişi ve tüm detay satırlarını siler."""
    fis = Fis.query.get_or_404(fis_id)
    db.session.delete(fis)
    db.session.commit()
    flash("Fiş başarıyla silindi.", "success")
    return redirect(url_for("fisleri_goruntule"))


@app.route("/rapor_indir")
def rapor_indir():
    """Pandas ile JOIN yapıp Excel dosyası oluşturur ve indirir."""
    query = (
        db.session.query(
            Fis.id.label("Fiş No"),
            Fis.tarih.label("Tarih"),
            Fis.sevk_eden_cari.label("Sevk Eden Cari"),
            Fis.sevk_yeri_fabrika.label("Fabrika"),
            Fis.sevk_yeri_fis_no.label("Sevkiyat Fiş No"),
            Fis.plaka_no.label("Plaka No"),
            FisDetayi.agac_cinsi.label("Ağaç Cinsi"),
            FisDetayi.cap.label("Çap"),
            FisDetayi.miktar.label("Miktar"),
            FisDetayi.birim.label("Birim"),
            FisDetayi.birim_fiyat.label("Birim Fiyat"),
            FisDetayi.toplam_tutar.label("Toplam Tutar"),
        )
        .join(FisDetayi, Fis.id == FisDetayi.fis_id)
        .order_by(Fis.tarih.desc(), Fis.id.desc())
        .all()
    )

    df = pd.DataFrame(query, columns=[
        "Fiş No", "Tarih", "Sevk Eden Cari", "Fabrika",
        "Sevkiyat Fiş No", "Plaka No", "Ağaç Cinsi", "Çap",
        "Miktar", "Birim", "Birim Fiyat", "Toplam Tutar",
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sevkiyat Raporu")
    output.seek(0)

    tarih_str = datetime.now().strftime("%Y-%m-%d")
    dosya_adi = f"Marmara_Aydoganlar_Rapor_{tarih_str}.xlsx"

    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=dosya_adi,
    )


# ───────────────────────── Uygulama Başlatma ─────────────────────────

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
