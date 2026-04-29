from flask import Blueprint, render_template
from app.models import Fis, FisDetayi, StokBildirim

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_bekleyen_bildirim():
    try:
        sayi = StokBildirim.query.filter_by(durum='bekliyor').count()
    except Exception:
        sayi = 0
    return dict(bekleyen_bildirim_sayisi=sayi)

@main_bp.route("/")
def index():
    toplam_fis = Fis.query.count()
    toplam_kalem = FisDetayi.query.count()
    son_fisler = Fis.query.order_by(Fis.tarih.desc(), Fis.id.desc()).limit(5).all()
    return render_template("index.html", toplam_fis=toplam_fis,
                           toplam_kalem=toplam_kalem, son_fisler=son_fisler)
