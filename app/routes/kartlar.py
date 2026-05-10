from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.extensions import db
from app.models import Cari, Fabrika
from app.services.kartlar_service import KartlarService

kartlar_bp = Blueprint('kartlar', __name__)

@kartlar_bp.route("/kartlar")
def kartlar():
    """
    Tüm Cari ve Fabrika kartlarını listeleyen sayfa (GET isteği ile çalışır).
    """
    # Veritabanından sadece aktif olan Carileri kod sırasına göre getir
    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_kodu).all()
    cariler_data = []
    for c in cariler:
        # Her cari için işlem hacmi (toplam tutar) bilgilerini hesapla
        c.hacim = KartlarService.get_hacim(c.firma_adi, c.firma_kodu, 'cari')
        cariler_data.append(c)

    # Veritabanından sadece aktif olan Fabrikaları kod sırasına göre getir
    fabrikalar = Fabrika.query.filter_by(aktif_mi=True).order_by(Fabrika.firma_kodu).all()
    fabrikalar_data = []
    for f in fabrikalar:
        # Her fabrika için işlem hacmi bilgilerini hesapla
        f.hacim = KartlarService.get_hacim(f.firma_adi, f.firma_kodu, 'fabrika')
        fabrikalar_data.append(f)

    # index.html şablonuna bu verileri göndererek ekranda gösterilmesini sağla
    return render_template("kartlar/index.html", cariler=cariler_data, fabrikalar=fabrikalar_data)

@kartlar_bp.route("/kart_ekle/<tur>", methods=["POST"])
def kart_ekle(tur):
    """
    Yeni bir Cari veya Fabrika kartı eklemek için kullanılan fonksiyon (Sadece POST kabul eder).
    """
    try:
        # KartlarService üzerinden ekleme işlemini yap. request.form formdaki verileri taşır.
        yeni_kod = KartlarService.add_kart(tur, request.form)
        # İşlem başarılıysa yeşil (success) bir bildirim göster
        flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla eklendi. (Kod: {yeni_kod})", "success")
    except ValueError as e:
        # Eğer bir kural ihlali varsa (örn: isim boşsa) hata mesajını kırmızı (danger) göster
        flash(str(e), "danger")
    # İşlem sonunda listeleme sayfasına geri dön
    return redirect(url_for("kartlar.kartlar"))

@kartlar_bp.route("/kart_duzenle/<tur>/<firma_kodu>", methods=["POST"])
def kart_duzenle(tur, firma_kodu):
    """
    Mevcut bir kartın bilgilerini günceller (POST).
    """
    try:
        # İlgili kartı veritabanında bul ve yeni verilerle güncelle
        KartlarService.edit_kart(tur, firma_kodu, request.form)
        flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla güncellendi.", "success")
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("kartlar.kartlar"))

@kartlar_bp.route("/kart_sil/<tur>/<firma_kodu>", methods=["POST"])
def kart_sil(tur, firma_kodu):
    """
    Bir kartı silmek yerine 'aktif_mi' durumunu False yapar (Soft Delete).
    """
    # Veritabanından fiziksel olarak silmek yerine, aktiflik durumunu kapatıyoruz
    KartlarService.delete_kart(tur, firma_kodu)
    flash(f"{'Cari' if tur == 'cari' else 'Fabrika'} başarıyla silindi.", "success")
    return redirect(url_for("kartlar.kartlar"))
