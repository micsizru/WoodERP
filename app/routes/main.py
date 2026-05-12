import logging
from datetime import date
from flask import Blueprint, render_template
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from app.extensions import db
from app.models import Fis, FisDetayi, StokBildirim

main_bp = Blueprint('main', __name__)

@main_bp.app_context_processor
def inject_bekleyen_bildirim():
    try:
        sayi = StokBildirim.query.outerjoin(Fis, StokBildirim.fis_id == Fis.id).filter(
            StokBildirim.durum == 'bekliyor',
            db.or_(StokBildirim.fis_id == None, Fis.tarih <= date.today())
        ).count()
    except SQLAlchemyError as e:
        logging.error("Context processor veritabanı hatası (StokBildirim):", exc_info=True)
        sayi = 0
    except Exception as e:
        logging.critical("Context processor beklenmeyen hata:", exc_info=True)
        sayi = 0
    return dict(bekleyen_bildirim_sayisi=sayi)

@main_bp.route("/")
def index():
    toplam_fis = Fis.query.count()
    toplam_kalem = FisDetayi.query.count()
    son_fisler = Fis.query.options(
        joinedload(Fis.cari)
    ).order_by(Fis.tarih.desc(), Fis.id.desc()).limit(5).all()
    return render_template("home/index.html", toplam_fis=toplam_fis,
                           toplam_kalem=toplam_kalem, son_fisler=son_fisler)
