from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Cari, Fabrika
from app.services.kartlar_service import KartlarService

kartlar_bp = Blueprint('kartlar', __name__)

@kartlar_bp.route("/kartlar")
def kartlar():
    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_kodu).all()
    cariler_data = []
    for c in cariler:
        c.hacim = KartlarService.get_hacim(c.firma_adi, c.firma_kodu, 'cari')
        cariler_data.append(c)

    fabrikalar = Fabrika.query.filter_by(aktif_mi=True).order_by(Fabrika.firma_kodu).all()
    fabrikalar_data = []
    for f in fabrikalar:
        f.hacim = KartlarService.get_hacim(f.firma_adi, f.firma_kodu, 'fabrika')
        fabrikalar_data.append(f)

    return render_template("kartlar/index.html", cariler=cariler_data, fabrikalar=fabrikalar_data)

@kartlar_bp.route("/kart_ekle/<tur>", methods=["POST"])
def kart_ekle(tur):
    try:
        yeni_kod = KartlarService.add_kart(tur, request.form)
        flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla eklendi. (Kod: {yeni_kod})", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("kartlar.kartlar"))

@kartlar_bp.route("/kart_duzenle/<tur>/<firma_kodu>", methods=["POST"])
def kart_duzenle(tur, firma_kodu):
    try:
        KartlarService.edit_kart(tur, firma_kodu, request.form)
        flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla güncellendi.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("kartlar.kartlar"))

@kartlar_bp.route("/kart_sil/<tur>/<firma_kodu>", methods=["POST"])
def kart_sil(tur, firma_kodu):
    KartlarService.delete_kart(tur, firma_kodu)
    flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla silindi.", "success")
    return redirect(url_for("kartlar.kartlar"))
