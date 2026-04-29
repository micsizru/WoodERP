from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensions import db
from app.models import MevcutStok, GelecekStok, StokBildirim, Cari
from app.constants import AGAC_CINSLERI, BIRIMLER

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
    except Exception as e:
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500


@stoklar_bp.route("/stoklar")
def stoklar():
    bugun = date.today()
    zamani_gelenler = GelecekStok.query.filter(GelecekStok.teslim_tarihi <= bugun).all()
    if zamani_gelenler:
        aktif_bildirimler = StokBildirim.query.filter(StokBildirim.durum.in_(['bekliyor', 'reddedildi'])).all()
        aktif_gelecek_stok_idleri = {b.gelecek_stok_id for b in aktif_bildirimler if b.gelecek_stok_id is not None}
        
        yeni_bildirimler = []
        for g in zamani_gelenler:
            if g.id not in aktif_gelecek_stok_idleri:
                yeni_bildirimler.append(StokBildirim(
                    tip='ekleme',
                    cari_kodu=g.cari_kodu,
                    kalem=g.kalem,
                    islem_miktari=g.miktar,
                    birim=g.birim,
                    durum='bekliyor',
                    gelecek_stok_id=g.id
                ))
        if yeni_bildirimler:
            db.session.bulk_save_objects(yeni_bildirimler)
            db.session.commit()

    bekleyenler = StokBildirim.query.filter_by(durum='bekliyor').order_by(StokBildirim.id.desc()).all()
    mevcut_stoklar = MevcutStok.query.join(Cari).order_by(Cari.firma_adi, MevcutStok.kalem).all()
    gelecek_stoklar = GelecekStok.query.order_by(GelecekStok.teslim_tarihi.asc()).all()
    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_adi).all()
    reddedilenler = StokBildirim.query.filter_by(durum='reddedildi').all()
    
    bekleyen_gelecek_dict = {b.gelecek_stok_id: b.id for b in bekleyenler if b.gelecek_stok_id}
    reddedilen_gelecek_dict = {b.gelecek_stok_id: b.id for b in reddedilenler if b.gelecek_stok_id}

    return render_template("stoklar.html", 
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
    bildirim = StokBildirim.query.get_or_404(bildirim_id)
    if bildirim.durum != 'bekliyor':
        flash("Bu işlem zaten gerçekleştirilmiş.", "warning")
        return redirect(url_for('stoklar.stoklar'))

    mevcut = MevcutStok.query.filter_by(cari_kodu=bildirim.cari_kodu, kalem=bildirim.kalem, birim=bildirim.birim).first()
    if bildirim.tip == 'dusum':
        if mevcut:
            mevcut.miktar = max(0.0, mevcut.miktar - bildirim.islem_miktari)
        else:
            yeni_stok = MevcutStok(
                cari_kodu=bildirim.cari_kodu,
                kalem=bildirim.kalem,
                miktar=0.0,
                birim=bildirim.birim
            )
            db.session.add(yeni_stok)
    elif bildirim.tip == 'ekleme':
        if mevcut:
            mevcut.miktar += bildirim.islem_miktari
        else:
            yeni_stok = MevcutStok(
                cari_kodu=bildirim.cari_kodu,
                kalem=bildirim.kalem,
                miktar=bildirim.islem_miktari,
                birim=bildirim.birim
            )
            db.session.add(yeni_stok)
    
    bildirim.durum = 'onaylandi'
    if bildirim.gelecek_stok_id:
        g_stok = GelecekStok.query.get(bildirim.gelecek_stok_id)
        if g_stok:
            db.session.delete(g_stok)
            
    db.session.commit()
    flash("Stok işlemi başarıyla onaylandı.", "success")
    return redirect(url_for('stoklar.stoklar'))

@stoklar_bp.route("/stok_reddet/<int:bildirim_id>", methods=["POST"])
def stok_reddet(bildirim_id):
    bildirim = StokBildirim.query.get_or_404(bildirim_id)
    if bildirim.durum != 'bekliyor':
        flash("Bu işlem zaten gerçekleştirilmiş.", "warning")
        return redirect(url_for('stoklar.stoklar'))
    
    bildirim.durum = 'reddedildi'
    db.session.commit()
    flash("Stok işlemi reddedildi.", "info")
    return redirect(url_for('stoklar.stoklar'))


@stoklar_bp.route("/stok_ekle_manuel", methods=["POST"])
def stok_ekle_manuel():
    cari_kodu = request.form.get("cari_kodu")
    kalem = request.form.get("kalem")
    miktar = float(request.form.get("miktar", 0))
    birim = request.form.get("birim", "Ton")
    
    mevcut = MevcutStok.query.filter_by(cari_kodu=cari_kodu, kalem=kalem, birim=birim).first()
    if mevcut:
        mevcut.miktar += miktar
    else:
        yeni = MevcutStok(cari_kodu=cari_kodu, kalem=kalem, miktar=miktar, birim=birim)
        db.session.add(yeni)
    
    db.session.commit()
    flash("Mevcut stok manuel olarak güncellendi.", "success")
    return redirect(url_for("stoklar.stoklar"))


@stoklar_bp.route("/gelecek_stok_ekle", methods=["POST"])
def gelecek_stok_ekle():
    cari_kodu = request.form.get("cari_kodu")
    kalem = request.form.get("kalem")
    miktar = float(request.form.get("miktar", 0))
    birim = request.form.get("birim", "Ton")
    teslim_tarihi_str = request.form.get("teslim_tarihi")
    
    tarih = datetime.strptime(teslim_tarihi_str, "%Y-%m-%d").date() if teslim_tarihi_str else date.today()
    yeni = GelecekStok(cari_kodu=cari_kodu, kalem=kalem, miktar=miktar, birim=birim, teslim_tarihi=tarih)
    db.session.add(yeni)
    db.session.commit()
    flash("Gelecek sipariş/taahhüt başarıyla eklendi.", "success")
    return redirect(url_for("stoklar.stoklar"))


@stoklar_bp.route("/stok_sil/<tip>/<int:id>", methods=["POST"])
def stok_sil(tip, id):
    if tip == 'mevcut':
        kayit = MevcutStok.query.get_or_404(id)
    elif tip == 'gelecek':
        kayit = GelecekStok.query.get_or_404(id)
        StokBildirim.query.filter_by(gelecek_stok_id=kayit.id).delete()
    else:
        flash("Geçersiz işlem tipi.", "danger")
        return redirect(url_for("stoklar.stoklar"))
        
    db.session.delete(kayit)
    db.session.commit()
    flash(f"{'Mevcut' if tip=='mevcut' else 'Gelecek'} stok kaydı silindi.", "success")
    return redirect(url_for("stoklar.stoklar"))


@stoklar_bp.route("/stok_duzenle/<tip>/<int:id>", methods=["POST"])
def stok_duzenle(tip, id):
    if tip == 'mevcut':
        kayit = MevcutStok.query.get_or_404(id)
        kayit.cari_kodu = request.form.get("cari_kodu")
        kayit.kalem = request.form.get("kalem")
        kayit.miktar = float(request.form.get("miktar", 0))
        kayit.birim = request.form.get("birim", "Ton")
    elif tip == 'gelecek':
        kayit = GelecekStok.query.get_or_404(id)
        kayit.cari_kodu = request.form.get("cari_kodu")
        kayit.kalem = request.form.get("kalem")
        kayit.miktar = float(request.form.get("miktar", 0))
        kayit.birim = request.form.get("birim", "Ton")
        teslim_tarihi_str = request.form.get("teslim_tarihi")
        if teslim_tarihi_str:
            kayit.teslim_tarihi = datetime.strptime(teslim_tarihi_str, "%Y-%m-%d").date()
            
        bildirim = StokBildirim.query.filter_by(gelecek_stok_id=kayit.id).filter(StokBildirim.durum.in_(['bekliyor', 'reddedildi'])).first()
        if bildirim:
            if kayit.teslim_tarihi > date.today():
                db.session.delete(bildirim)
            else:
                if bildirim.durum == 'reddedildi':
                    bildirim.durum = 'bekliyor'
                bildirim.cari_kodu = kayit.cari_kodu
                bildirim.kalem = kayit.kalem
                bildirim.islem_miktari = kayit.miktar
                bildirim.birim = kayit.birim
    else:
        flash("Geçersiz işlem tipi.", "danger")
        return redirect(url_for("stoklar.stoklar"))
        
    db.session.commit()
    flash(f"{'Mevcut' if tip=='mevcut' else 'Gelecek'} stok kaydı güncellendi.", "success")
    return redirect(url_for("stoklar.stoklar"))
