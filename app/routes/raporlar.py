from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models import Fis, FisDetayi, Cari, Fabrika
from app.constants import TURKCE_AYLAR
from app.utils import tarih_araligi_hesapla

raporlar_bp = Blueprint('raporlar', __name__)

def fise_firma_filtresi_ekle(sorgu, cari_kodu=None, cari_adi=None, fabrika_kodu=None, fabrika_adi=None):
    if cari_kodu:
        cari_obj = Cari.query.get(cari_kodu)
        if cari_obj:
            # Kod varsa: Ya kod eşleşmeli YA DA (kod boşsa ve isim eşleşiyorsa) legacy kayıt olmalı.
            sorgu = sorgu.filter(db.or_(
                Fis.cari_kodu == cari_kodu, 
                db.and_(Fis.cari_kodu == None, Fis.sevk_eden_cari == cari_obj.firma_adi)
            ))
    elif cari_adi:
        sorgu = sorgu.filter(Fis.sevk_eden_cari.ilike(f"%{cari_adi}%"))

    if fabrika_kodu:
        fabrika_obj = Fabrika.query.get(fabrika_kodu)
        if fabrika_obj:
            sorgu = sorgu.filter(db.or_(
                Fis.fabrika_kodu == fabrika_kodu, 
                db.and_(Fis.fabrika_kodu == None, Fis.sevk_yeri_fabrika == fabrika_obj.firma_adi)
            ))
    elif fabrika_adi:
        sorgu = sorgu.filter(Fis.sevk_yeri_fabrika.ilike(f"%{fabrika_adi}%"))
        
    return sorgu

@raporlar_bp.route("/raporlar")
def raporlar():
    bugun = date.today()
    en_eski = db.session.query(db.func.min(Fis.tarih)).scalar()
    en_eski_yil = en_eski.year if en_eski else bugun.year
    yillar = list(range(bugun.year, en_eski_yil - 1, -1))

    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_adi).all()
    fabrikalar = Fabrika.query.filter_by(aktif_mi=True).order_by(Fabrika.firma_adi).all()

    return render_template(
        "raporlar/index.html",
        bugun=bugun.isoformat(),
        yillar=yillar,
        aylar=TURKCE_AYLAR,
        cariler=cariler,
        fabrikalar=fabrikalar
    )

@raporlar_bp.route("/rapor_indir")
def rapor_indir():
    filtre = request.args.get("filtre", "")
    baslangic_str = request.args.get("baslangic", "")
    bitis_str = request.args.get("bitis", "")
    
    cari_kodu = request.args.get("cari_kodu", "")
    cari_adi = request.args.get("cari_adi", "")
    fabrika_kodu = request.args.get("fabrika_kodu", "")
    fabrika_adi = request.args.get("fabrika_adi", "")

    baslangic, bitis = tarih_araligi_hesapla(filtre, baslangic_str, bitis_str)
    
    # RAM Darboğazı Koruması: Tarih seçilmemişse (Tümü/God Mode) son 5 yılın 1 Ocak tarihinden başlat
    if not baslangic:
        baslangic = date(date.today().year - 5, 1, 1)
        bitis = date.today()

    sorgu = (
        db.session.query(
            Fis.id.label("Fiş No"),
            Fis.tarih.label("Tarih"),
            Fis.sevk_eden_cari.label("Sevk Eden Cari"),
            Fis.cari_kodu,
            Fis.sevk_yeri_fabrika.label("Fabrika"),
            Fis.fabrika_kodu,
            Fis.sevk_yeri_fis_no.label("Sevkiyat Fiş No"),
            Fis.plaka_no.label("Plaka No"),
            FisDetayi.agac_cinsi.label("Ağaç Cinsi"),
            FisDetayi.cap.label("Çap"),
            FisDetayi.miktar.label("Miktar"),
            FisDetayi.birim.label("Birim"),
            FisDetayi.birim_fiyat.label("Birim Fiyat"),
            FisDetayi.toplam_tutar.label("Toplam Tutar"),
        )
        .join(FisDetayi, Fis.id == FisDetayi.fis_id)
    )

    if baslangic and bitis:
        sorgu = sorgu.filter(Fis.tarih >= baslangic, Fis.tarih <= bitis)

    if filtre != 'god_mode':
        sorgu = fise_firma_filtresi_ekle(sorgu, cari_kodu, cari_adi, fabrika_kodu, fabrika_adi)

    sonuclar = sorgu.order_by(Fis.tarih.desc(), Fis.id.desc()).all()

    cariler_dict = {c.firma_kodu: c.firma_adi for c in Cari.query.all()}
    fabrikalar_dict = {f.firma_kodu: f.firma_adi for f in Fabrika.query.all()}

    json_data = []
    for r in sonuclar:
        json_data.append({
            "Fiş No": r[0],
            "Tarih": r[1].strftime("%d.%m.%Y") if hasattr(r[1], 'strftime') else r[1],
            "Sevkiyat Fiş No": r[6],
            "Sevk Eden Cari": cariler_dict.get(r[3], r[2]),
            "Fabrika": fabrikalar_dict.get(r[5], r[4]),
            "Plaka No": r[7],
            "Ağaç Cinsi": r[8],
            "Çap": r[9],
            "Miktar": r[10],
            "Birim": r[11],
            "Birim Fiyat": r[12],
            "Toplam Tutar": r[13]
        })

    if baslangic and bitis:
        dosya_adi = f"WoodERP_Rapor_{baslangic}_{bitis}.xlsx"
    else:
        tarih_str = datetime.now().strftime("%Y-%m-%d")
        dosya_adi = f"WoodERP_Rapor_Tumu_{tarih_str}.xlsx"

    return jsonify({
        "filename": dosya_adi,
        "data": json_data
    })

@raporlar_bp.route("/rapor_indir_pdf")
def rapor_indir_pdf():
    filtre = request.args.get("filtre", "")
    baslangic_str = request.args.get("baslangic", "")
    bitis_str = request.args.get("bitis", "")
    
    cari_kodu = request.args.get("cari_kodu", "")
    cari_adi = request.args.get("cari_adi", "")
    fabrika_kodu = request.args.get("fabrika_kodu", "")
    fabrika_adi = request.args.get("fabrika_adi", "")

    baslangic, bitis = tarih_araligi_hesapla(filtre, baslangic_str, bitis_str)
    
    # RAM Darboğazı Koruması: Tarih seçilmemişse (Tümü/God Mode) son 5 yılın 1 Ocak tarihinden başlat
    if not baslangic:
        baslangic = date(date.today().year - 5, 1, 1)
        bitis = date.today()

    sorgu = (
        db.session.query(
            Fis.id,
            Fis.tarih,
            Fis.sevk_eden_cari,
            Fis.cari_kodu,
            Fis.sevk_yeri_fabrika,
            Fis.fabrika_kodu,
            Fis.sevk_yeri_fis_no,
            Fis.plaka_no,
            FisDetayi.agac_cinsi,
            FisDetayi.cap,
            FisDetayi.miktar,
            FisDetayi.birim,
            FisDetayi.birim_fiyat,
            FisDetayi.toplam_tutar,
        )
        .join(FisDetayi, Fis.id == FisDetayi.fis_id)
    )

    if baslangic and bitis:
        sorgu = sorgu.filter(Fis.tarih >= baslangic, Fis.tarih <= bitis)

    cari_isim = "Tümü"
    fabrika_isim = "Tümü"

    if filtre != 'god_mode':
        if cari_kodu:
            c = Cari.query.get(cari_kodu)
            if c: cari_isim = c.firma_adi
        elif cari_adi:
            cari_isim = cari_adi
            
        if fabrika_kodu:
            f = Fabrika.query.get(fabrika_kodu)
            if f: fabrika_isim = f.firma_adi
        elif fabrika_adi:
            fabrika_isim = fabrika_adi

        sorgu = fise_firma_filtresi_ekle(sorgu, cari_kodu, cari_adi, fabrika_kodu, fabrika_adi)

    sonuclar = sorgu.order_by(Fis.tarih.desc(), Fis.id.desc()).all()
    
    # Detaylar için cariler ve fabrikalar sözlükleri
    cariler_dict = {c.firma_kodu: c.firma_adi for c in Cari.query.all()}
    fabrikalar_dict = {f.firma_kodu: f.firma_adi for f in Fabrika.query.all()}

    # Sonuçları işleyerek listeye dök
    islenmis_sonuclar = []
    toplam_genel = 0
    for res in sonuclar:
        row = {
            "id": res.id,
            "tarih": res.tarih,
            "cari": cariler_dict.get(res.cari_kodu, res.sevk_eden_cari),
            "fabrika": fabrikalar_dict.get(res.fabrika_kodu, res.sevk_yeri_fabrika),
            "plaka_no": res.plaka_no,
            "agac_cinsi": res.agac_cinsi,
            "cap": res.cap,
            "miktar": res.miktar,
            "birim": res.birim,
            "birim_fiyat": res.birim_fiyat,
            "toplam_tutar": res.toplam_tutar
        }
        islenmis_sonuclar.append(row)
        toplam_genel += res.toplam_tutar

    return render_template(
        "pdf/rapor_pdf.html",
        sonuclar=islenmis_sonuclar,
        baslangic=baslangic,
        bitis=bitis,
        cari_isim=cari_isim,
        fabrika_isim=fabrika_isim,
        toplam_genel=toplam_genel,
        datetime=datetime
    )
