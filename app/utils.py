import calendar
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pytz
import os

def tarih_araligi_hesapla(filtre, baslangic_str=None, bitis_str=None):
    bugun = date.today()

    if filtre == "bugun":
        return bugun, bugun

    elif filtre == "son_3_gun":
        return bugun - timedelta(days=2), bugun

    elif filtre == "son_hafta":
        return bugun - timedelta(days=6), bugun

    elif filtre == "bu_hafta":
        pazartesi = bugun - timedelta(days=bugun.weekday())
        return pazartesi, bugun

    elif filtre == "onceki_hafta":
        bu_pazartesi = bugun - timedelta(days=bugun.weekday())
        onceki_pazartesi = bu_pazartesi - timedelta(days=7)
        onceki_pazar = bu_pazartesi - timedelta(days=1)
        return onceki_pazartesi, onceki_pazar

    elif filtre == "son_ay":
        bir_ay_once = bugun - relativedelta(months=1)
        return bir_ay_once, bugun

    elif filtre and filtre.startswith("yil_"):
        yil = int(filtre.split("_")[1])
        return date(yil, 1, 1), date(yil, 12, 31)

    elif filtre and filtre.startswith("ay_"):
        parcalar = filtre.split("_")
        yil, ay = int(parcalar[1]), int(parcalar[2])
        son_gun = calendar.monthrange(yil, ay)[1]
        return date(yil, ay, 1), date(yil, ay, son_gun)

    elif filtre and filtre.startswith("hafta_"):
        parcalar = filtre.split("_")
        yil, ay, hafta_no = int(parcalar[1]), int(parcalar[2]), int(parcalar[3])
        ayin_ilk_gunu = date(yil, ay, 1)
        ilk_pazartesi_offset = (7 - ayin_ilk_gunu.weekday()) % 7
        if ayin_ilk_gunu.weekday() == 0:
            ilk_pazartesi = ayin_ilk_gunu
        else:
            ilk_pazartesi = ayin_ilk_gunu + timedelta(days=ilk_pazartesi_offset)
        hafta_baslangic = ilk_pazartesi + timedelta(weeks=hafta_no - 1)
        hafta_bitis = hafta_baslangic + timedelta(days=6)
        son_gun = calendar.monthrange(yil, ay)[1]
        ayin_sonu = date(yil, ay, son_gun)
        hafta_bitis = min(hafta_bitis, ayin_sonu)
        return hafta_baslangic, hafta_bitis

    elif filtre == "ozel" and baslangic_str and bitis_str:
        baslangic = datetime.strptime(baslangic_str, "%Y-%m-%d").date()
        bitis = datetime.strptime(bitis_str, "%Y-%m-%d").date()
        return baslangic, bitis

    return None, None

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul'))

def istanbul_simdi():
    return get_istanbul_time()

def yeni_firma_kodu_uret(tur, Cari, Fabrika):
    if tur == 'cari':
        son_kayit = Cari.query.order_by(Cari.firma_kodu.desc()).first()
        prefix = 'C-'
    else:
        son_kayit = Fabrika.query.order_by(Fabrika.firma_kodu.desc()).first()
        prefix = 'F-'
        
    if son_kayit and son_kayit.firma_kodu.startswith(prefix):
        try:
            num = int(son_kayit.firma_kodu.split('-')[1])
            yeni_num = num + 1
        except ValueError:
            yeni_num = 1
    else:
        yeni_num = 1
        
    return f"{prefix}{yeni_num:03d}"
