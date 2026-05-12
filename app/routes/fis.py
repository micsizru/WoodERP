import logging
from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import Fis, Cari, Fabrika
from app.constants import AGAC_CINSLERI, CAPLER, BIRIMLER
from app.utils import get_istanbul_time
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
    except (ValueError, KeyError) as e:
        db.session.rollback()
        logging.warning(f"Kullanıcı/Veri hatası (Yeni Fiş): {e}")
        return jsonify({"durum": "hata", "mesaj": f"Geçersiz veya eksik veri: {str(e)}"}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error("Veritabanı hatası (Yeni Fiş):", exc_info=True)
        return jsonify({"durum": "hata", "mesaj": "Kayıt sırasında veritabanı hatası oluştu."}), 500
    except Exception as e:
        db.session.rollback()
        logging.critical("Bilinmeyen kritik hata (Yeni Fiş):", exc_info=True)
        return jsonify({"durum": "hata", "mesaj": "Sistemde beklenmeyen bir hata oluştu."}), 500

@fis_bp.route("/fisleri_goruntule")
def fisleri_goruntule():
    fisler = Fis.query.options(
        joinedload(Fis.cari),
        joinedload(Fis.fabrika),
        joinedload(Fis.detaylar)
    ).order_by(Fis.tarih.desc(), Fis.id.desc()).all()
    return render_template("fis/list.html", fisler=fisler)

@fis_bp.route("/fis_detay/<int:fis_id>")
def fis_detay(fis_id):
    fis = Fis.query.options(
        joinedload(Fis.cari),
        joinedload(Fis.fabrika),
        joinedload(Fis.detaylar)
    ).get_or_404(fis_id)
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
        except (ValueError, KeyError) as e:
            db.session.rollback()
            logging.warning(f"Kullanıcı/Veri hatası (Fiş Düzenle {fis_id}): {e}")
            return jsonify({"durum": "hata", "mesaj": f"Geçersiz veya eksik veri: {str(e)}"}), 400
        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Veritabanı hatası (Fiş Düzenle {fis_id}):", exc_info=True)
            return jsonify({"durum": "hata", "mesaj": "Güncelleme sırasında veritabanı hatası oluştu."}), 500
        except Exception as e:
            db.session.rollback()
            logging.critical(f"Bilinmeyen kritik hata (Fiş Düzenle {fis_id}):", exc_info=True)
            return jsonify({"durum": "hata", "mesaj": "Sistemde beklenmeyen bir hata oluştu."}), 500

    fis = Fis.query.options(
        joinedload(Fis.cari),
        joinedload(Fis.fabrika),
        joinedload(Fis.detaylar)
    ).get_or_404(fis_id)

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
    fis = Fis.query.options(
        joinedload(Fis.cari),
        joinedload(Fis.fabrika),
        joinedload(Fis.detaylar)
    ).get_or_404(fis_id)
    
    veriler = []
    for d in fis.detaylar:
        veriler.append({
            "Fiş No": fis.id,
            "Tarih": fis.tarih.strftime("%d.%m.%Y"),
            "Sevk Eden Cari": fis.guncel_sevk_eden_cari,
            "Fabrika": fis.guncel_sevk_yeri_fabrika,
            "Sevkiyat Fiş No": fis.sevk_yeri_fis_no,
            "Plaka No": fis.plaka_no,
            "Ağaç Cinsi": d.agac_cinsi,
            "Çap": d.cap,
            "Miktar": d.miktar,
            "Birim": d.birim,
            "Birim Fiyat": d.birim_fiyat,
            "Toplam Tutar": d.toplam_tutar,
        })
        
    return jsonify({
        "filename": f"Fis_{fis.id}_{fis.guncel_sevk_eden_cari.replace(' ', '_')}_{fis.tarih}.xlsx",
        "data": veriler
    })

@fis_bp.route("/tek_fis_pdf/<int:fis_id>")
def tek_fis_pdf(fis_id):
    fis = Fis.query.options(
        joinedload(Fis.cari),
        joinedload(Fis.fabrika),
        joinedload(Fis.detaylar)
    ).get_or_404(fis_id)
    genel_toplam = sum(d.toplam_tutar for d in fis.detaylar)
    return render_template("pdf/fis_pdf.html", fis=fis, genel_toplam=genel_toplam, datetime=datetime)
