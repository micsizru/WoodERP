import logging
from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
from app.models import MevcutStok, GelecekStok, StokBildirim, Cari, Fis
from app.constants import AGAC_CINSLERI, BIRIMLER
from app.services.stok_service import StokService

stoklar_bp = Blueprint('stoklar', __name__)

@stoklar_bp.route("/api/stok_getir/<path:cari_kodu>")
def stok_getir(cari_kodu):
    try:
        mevcut_stoklar = MevcutStok.query.filter_by(cari_kodu=cari_kodu).all()
        mevcut_liste = [{
            "id": s.id,
            "kalem": s.kalem,
            "miktar": s.miktar,
            "birim": s.birim
        } for s in mevcut_stoklar]

        gelecek_stoklar = GelecekStok.query.filter_by(cari_kodu=cari_kodu).all()
        gelecek_liste = [{
            "id": s.id,
            "kalem": s.kalem,
            "miktar": s.miktar,
            "birim": s.birim,
            "teslim_tarihi": s.teslim_tarihi.strftime('%Y-%m-%d') if s.teslim_tarihi else None
        } for s in gelecek_stoklar]

        return jsonify({
            "durum": "basarili",
            "cari_kodu": cari_kodu,
            "mevcut_stok": mevcut_liste,
            "gelecek_stok": gelecek_liste
        })
    except SQLAlchemyError as e:
        logging.error(f"Veritabanı hatası (stok_getir - {cari_kodu}):", exc_info=True)
        return jsonify({"durum": "hata", "mesaj": "Stok verileri çekilirken veritabanı hatası oluştu."}), 500
    except Exception as e:
        logging.critical(f"Beklenmeyen hata (stok_getir - {cari_kodu}):", exc_info=True)
        return jsonify({"durum": "hata", "mesaj": "Sistemde beklenmeyen bir hata oluştu."}), 500


@stoklar_bp.route("/stoklar")
def stoklar():
    bugun = date.today()
    StokService.process_future_stocks()

    bekleyenler = StokBildirim.query.outerjoin(Fis, StokBildirim.fis_id == Fis.id).filter(
        StokBildirim.durum == 'bekliyor',
        db.or_(StokBildirim.fis_id == None, Fis.tarih <= bugun)
    ).order_by(StokBildirim.id.desc()).all()
    
    mevcut_stoklar = MevcutStok.query.outerjoin(Cari).order_by(Cari.firma_adi, MevcutStok.kalem).all()
    gelecek_stoklar = GelecekStok.query.order_by(GelecekStok.teslim_tarihi.asc()).all()
    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_adi).all()
    
    reddedilenler = StokBildirim.query.outerjoin(Fis, StokBildirim.fis_id == Fis.id).filter(
        StokBildirim.durum == 'reddedildi',
        db.or_(StokBildirim.fis_id == None, Fis.tarih <= bugun)
    ).all()
    
    bekleyen_gelecek_dict = {b.gelecek_stok_id: b.id for b in bekleyenler if b.gelecek_stok_id}
    reddedilen_gelecek_dict = {b.gelecek_stok_id: b.id for b in reddedilenler if b.gelecek_stok_id}

    return render_template("stok/index.html", 
                           bekleyenler=bekleyenler, 
                           mevcut_stoklar=mevcut_stoklar, 
                           gelecek_stoklar=gelecek_stoklar,
                           cariler=cariler,
                           agac_cinsleri=AGAC_CINSLERI,
                           birimler=BIRIMLER,
                           bekleyen_gelecek_dict=bekleyen_gelecek_dict,
                           reddedilen_gelecek_dict=reddedilen_gelecek_dict,
                           bugun=bugun)

@stoklar_bp.route("/stok_onayla/<int:bildirim_id>", methods=["POST"])
def stok_onayla(bildirim_id):
    if not StokService.approve_notification(bildirim_id):
        flash("Bu işlem zaten gerçekleştirilmiş.", "warning")
        return redirect(url_for('stoklar.stoklar'))
        
    flash("Stok işlemi başarıyla onaylandı.", "success")
    return redirect(url_for('stoklar.stoklar'))

@stoklar_bp.route("/stok_reddet/<int:bildirim_id>", methods=["POST"])
def stok_reddet(bildirim_id):
    if not StokService.reject_notification(bildirim_id):
        flash("Bu işlem zaten gerçekleştirilmiş.", "warning")
        return redirect(url_for('stoklar.stoklar'))
        
    flash("Stok işlemi reddedildi.", "info")
    return redirect(url_for('stoklar.stoklar'))


@stoklar_bp.route("/stok_ekle_manuel", methods=["POST"])
def stok_ekle_manuel():
    StokService.add_manual_stock(request.form)
    flash("Mevcut stok manuel olarak güncellendi.", "success")
    return redirect(url_for("stoklar.stoklar"))


@stoklar_bp.route("/gelecek_stok_ekle", methods=["POST"])
def gelecek_stok_ekle():
    StokService.add_future_stock(request.form)
    flash("Gelecek sipariş/taahhüt başarıyla eklendi.", "success")
    return redirect(url_for("stoklar.stoklar"))


@stoklar_bp.route("/stok_sil/<tip>/<int:id>", methods=["POST"])
def stok_sil(tip, id):
    try:
        StokService.delete_stock(tip, id)
        flash(f"{'Mevcut' if tip=='mevcut' else 'Gelecek'} stok kaydı silindi.", "success")
    except ValueError:
        flash("Geçersiz işlem tipi.", "danger")
    return redirect(url_for("stoklar.stoklar"))


@stoklar_bp.route("/stok_duzenle/<tip>/<int:id>", methods=["POST"])
def stok_duzenle(tip, id):
    try:
        StokService.update_stock(tip, id, request.form)
        flash(f"{'Mevcut' if tip=='mevcut' else 'Gelecek'} stok kaydı güncellendi.", "success")
    except ValueError:
        flash("Geçersiz işlem tipi.", "danger")
    return redirect(url_for("stoklar.stoklar"))
