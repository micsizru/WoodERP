from datetime import timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models import Cari, Fabrika, Fis, FisDetayi
from app.utils import istanbul_simdi, yeni_firma_kodu_uret

kartlar_bp = Blueprint('kartlar', __name__)

@kartlar_bp.route("/kartlar")
def kartlar():
    now = istanbul_simdi()
    bu_ay_baslangic = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    son_30_gun_baslangic = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)

    def hacim_hesapla(firma_adi, firma_kodu, tip='cari'):
        sorgu_base = db.session.query(db.func.sum(FisDetayi.toplam_tutar)).join(Fis)
        if tip == 'cari':
            sorgu_base = sorgu_base.filter(Fis.cari_kodu == firma_kodu)
        else:
            sorgu_base = sorgu_base.filter(Fis.fabrika_kodu == firma_kodu)
        
        tum_zamanlar = sorgu_base.scalar() or 0.0
        bu_ay = sorgu_base.filter(Fis.tarih >= bu_ay_baslangic.date()).scalar() or 0.0
        son_30 = sorgu_base.filter(Fis.tarih >= son_30_gun_baslangic.date()).scalar() or 0.0
        
        return {
            'tum': round(tum_zamanlar, 2),
            'bu_ay': round(bu_ay, 2),
            'son_30': round(son_30, 2)
        }

    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_kodu).all()
    cariler_data = []
    for c in cariler:
        c.hacim = hacim_hesapla(c.firma_adi, c.firma_kodu, 'cari')
        cariler_data.append(c)

    fabrikalar = Fabrika.query.filter_by(aktif_mi=True).order_by(Fabrika.firma_kodu).all()
    fabrikalar_data = []
    for f in fabrikalar:
        f.hacim = hacim_hesapla(f.firma_adi, f.firma_kodu, 'fabrika')
        fabrikalar_data.append(f)

    return render_template("kartlar.html", cariler=cariler_data, fabrikalar=fabrikalar_data)

@kartlar_bp.route("/kart_ekle/<tur>", methods=["POST"])
def kart_ekle(tur):
    Model = Cari if tur == 'cari' else Fabrika
    
    firma_adi = request.form.get("firma_adi", "").strip()
    if not firma_adi:
        flash("Firma adı zorunludur.", "danger")
        return redirect(url_for("kartlar.kartlar"))
        
    mevcut = Model.query.filter_by(firma_adi=firma_adi, aktif_mi=True).first()
    if mevcut:
        flash(f"Bu firma adı zaten mevcut: {firma_adi}", "danger")
        return redirect(url_for("kartlar.kartlar"))
        
    yeni_kod = yeni_firma_kodu_uret(tur, Cari, Fabrika)
    
    yeni_kart = Model(
        firma_kodu=yeni_kod,
        firma_adi=firma_adi,
        vergi_dairesi=request.form.get("vergi_dairesi", "").strip(),
        vergi_numarasi=request.form.get("vergi_numarasi", "").strip(),
        firma_adres=request.form.get("firma_adres", "").strip(),
        e_posta=request.form.get("e_posta", "").strip(),
        telefon_no=request.form.get("telefon_no", "").strip()
    )
    db.session.add(yeni_kart)
    db.session.commit()
    flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla eklendi. (Kod: {yeni_kod})", "success")
    return redirect(url_for("kartlar.kartlar"))

@kartlar_bp.route("/kart_duzenle/<tur>/<firma_kodu>", methods=["POST"])
def kart_duzenle(tur, firma_kodu):
    Model = Cari if tur == 'cari' else Fabrika
    kart = Model.query.get_or_404(firma_kodu)
    
    yeni_ad = request.form.get("firma_adi", "").strip()
    if not yeni_ad:
        flash("Firma adı zorunludur.", "danger")
        return redirect(url_for("kartlar.kartlar"))
        
    mevcut = Model.query.filter(Model.firma_adi == yeni_ad, Model.firma_kodu != firma_kodu, Model.aktif_mi == True).first()
    if mevcut:
        flash(f"Bu firma adı başka bir kayıtta kullanılıyor: {yeni_ad}", "danger")
        return redirect(url_for("kartlar.kartlar"))
        
    kart.firma_adi = yeni_ad
    kart.vergi_dairesi = request.form.get("vergi_dairesi", "").strip()
    kart.vergi_numarasi = request.form.get("vergi_numarasi", "").strip()
    kart.firma_adres = request.form.get("firma_adres", "").strip()
    kart.e_posta = request.form.get("e_posta", "").strip()
    kart.telefon_no = request.form.get("telefon_no", "").strip()
    
    db.session.commit()
    flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla güncellendi.", "success")
    return redirect(url_for("kartlar.kartlar"))

@kartlar_bp.route("/kart_sil/<tur>/<firma_kodu>", methods=["POST"])
def kart_sil(tur, firma_kodu):
    Model = Cari if tur == 'cari' else Fabrika
    kart = Model.query.get_or_404(firma_kodu)
    kart.aktif_mi = False
    db.session.commit()
    flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla silindi.", "success")
    return redirect(url_for("kartlar.kartlar"))
