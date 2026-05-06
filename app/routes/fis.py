from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from app.extensions import db
from app.models import Fis, FisDetayi, Cari, Fabrika, StokBildirim, MevcutStok
from app.constants import AGAC_CINSLERI, CAPLER, BIRIMLER
from app.utils import get_istanbul_time
from app.services.report_service import ReportService
from app.services.fis_service import FisService

fis_bp = Blueprint('fis', __name__)

@fis_bp.route("/yeni_fis", methods=["GET"])
def yeni_fis_formu():
    bugun = get_istanbul_time().strftime("%Y-%m-%d")
    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_adi).all()
    fabrikalar = Fabrika.query.filter_by(aktif_mi=True).order_by(Fabrika.firma_adi).all()
    
    return render_template(
        "fis/create.html",
        bugun=bugun,
        agac_cinsleri=AGAC_CINSLERI,
        capler=CAPLER,
        birimler=BIRIMLER,
        cariler=cariler,
        fabrikalar=fabrikalar
    )

@fis_bp.route("/yeni_fis", methods=["POST"])
def yeni_fis_kaydet():
    try:
        veri = request.get_json()
        fis_id = FisService.create_fis(veri)
        return jsonify({"durum": "basarili", "mesaj": "Fiş başarıyla kaydedildi.", "fis_id": fis_id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@fis_bp.route("/fisleri_goruntule")
def fisleri_goruntule():
    fisler = Fis.query.order_by(Fis.tarih.desc(), Fis.id.desc()).all()
    return render_template("fis/list.html", fisler=fisler)

@fis_bp.route("/fis_detay/<int:fis_id>")
def fis_detay(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    genel_toplam = sum(d.toplam_tutar for d in fis.detaylar)
    return render_template("fis/detail.html", fis=fis, genel_toplam=genel_toplam)

@fis_bp.route("/fis_sil/<int:fis_id>")
def fis_sil(fis_id):
    FisService.delete_fis(fis_id)
    flash("Fiş başarıyla silindi.", "success")
    return redirect(url_for("fis.fisleri_goruntule"))

@fis_bp.route("/fis_duzenle/<int:fis_id>", methods=["GET", "POST"])
def fis_duzenle(fis_id):
    if request.method == "POST":
        try:
            veri = request.get_json()
            FisService.update_fis(fis_id, veri)
            return jsonify({"durum": "basarili", "mesaj": "Fiş başarıyla güncellendi."})
        except Exception as e:
            db.session.rollback()
            return jsonify({"durum": "hata", "mesaj": str(e)}), 500

    fis = Fis.query.get_or_404(fis_id)

    cariler = Cari.query.filter(db.or_(Cari.aktif_mi == True, Cari.firma_kodu == fis.cari_kodu)).order_by(Cari.firma_adi).all()
    fabrikalar = Fabrika.query.filter(db.or_(Fabrika.aktif_mi == True, Fabrika.firma_kodu == fis.fabrika_kodu)).order_by(Fabrika.firma_adi).all()

    detaylar_list = []
    for d in fis.detaylar:
        detaylar_list.append({
            "agac_cinsi": d.agac_cinsi,
            "cap": d.cap,
            "miktar": d.miktar,
            "birim": d.birim,
            "birim_fiyat": d.birim_fiyat,
            "toplam_tutar": d.toplam_tutar,
            "stok_disi": d.stok_disi
        })
    
    return render_template(
        "fis/edit.html",
        fis=fis,
        detaylar_list=detaylar_list,
        agac_cinsleri=AGAC_CINSLERI,
        capler=CAPLER,
        birimler=BIRIMLER,
        cariler=cariler,
        fabrikalar=fabrikalar
    )

@fis_bp.route("/tek_fis_excel/<int:fis_id>")
def tek_fis_excel(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    return ReportService.generate_excel_for_fis(fis)

@fis_bp.route("/tek_fis_pdf/<int:fis_id>")
def tek_fis_pdf(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    genel_toplam = sum(d.toplam_tutar for d in fis.detaylar)
    return render_template("pdf/fis_pdf.html", fis=fis, genel_toplam=genel_toplam, datetime=datetime)
