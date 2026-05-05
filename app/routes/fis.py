from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from app.extensions import db
from app.models import Fis, FisDetayi, Cari, Fabrika, StokBildirim, MevcutStok
from app.constants import AGAC_CINSLERI, CAPLER, BIRIMLER
from app.utils import get_istanbul_time, get_pdf_config
from app.services.report_service import ReportService

fis_bp = Blueprint('fis', __name__)

@fis_bp.route("/yeni_fis", methods=["GET"])
def yeni_fis_formu():
    bugun = get_istanbul_time().strftime("%Y-%m-%d")
    cariler = Cari.query.filter_by(aktif_mi=True).order_by(Cari.firma_adi).all()
    fabrikalar = Fabrika.query.filter_by(aktif_mi=True).order_by(Fabrika.firma_adi).all()
    
    return render_template(
        "yeni_fis.html",
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
        tarih_str = veri.get("tarih", date.today().isoformat())
        tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date()

        yeni_fis = Fis(
            tarih=tarih,
            sevk_eden_cari=veri["sevk_eden_cari"].strip(),
            cari_kodu=veri.get("cari_kodu"),
            sevk_yeri_fabrika=veri["sevk_yeri_fabrika"].strip(),
            fabrika_kodu=veri.get("fabrika_kodu"),
            sevk_yeri_fis_no=veri["sevk_yeri_fis_no"].strip(),
            plaka_no=veri["plaka_no"].strip(),
        )
        db.session.add(yeni_fis)
        db.session.flush()

        kalemler = veri.get("kalemler", [])
        if not kalemler:
            return jsonify({"durum": "hata", "mesaj": "En az bir kalem satırı eklemelisiniz."}), 400

        for k in kalemler:
            miktar = float(k["miktar"])
            birim_fiyat = float(k["birim_fiyat"])
            toplam_tutar = round(miktar * birim_fiyat, 2)
            k_stok_disi = k.get("stok_disi_birak", False)

            detay = FisDetayi(
                fis_id=yeni_fis.id,
                agac_cinsi=k["agac_cinsi"],
                cap=k.get("cap", "-") or "-",
                miktar=miktar,
                birim=k["birim"],
                birim_fiyat=birim_fiyat,
                toplam_tutar=toplam_tutar,
                stok_disi=k_stok_disi,
            )
            db.session.add(detay)

            if not k_stok_disi:
                cari_obj = db.session.get(Cari, yeni_fis.cari_kodu) if yeni_fis.cari_kodu else None
                if cari_obj:
                    bildirim = StokBildirim(
                        tip='dusum',
                        cari_kodu=cari_obj.firma_kodu,
                        kalem=k["agac_cinsi"],
                        islem_miktari=miktar,
                        birim=k["birim"],
                        durum='bekliyor',
                        fis_id=yeni_fis.id
                    )
                    db.session.add(bildirim)

        db.session.commit()
        return jsonify({"durum": "basarili", "mesaj": "Fiş başarıyla kaydedildi.", "fis_id": yeni_fis.id})

    except Exception as e:
        db.session.rollback()
        return jsonify({"durum": "hata", "mesaj": str(e)}), 500

@fis_bp.route("/fisleri_goruntule")
def fisleri_goruntule():
    fisler = Fis.query.order_by(Fis.tarih.desc(), Fis.id.desc()).all()
    return render_template("fisleri_goruntule.html", fisler=fisler)

@fis_bp.route("/fis_detay/<int:fis_id>")
def fis_detay(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    genel_toplam = sum(d.toplam_tutar for d in fis.detaylar)
    return render_template("fis_detay.html", fis=fis, genel_toplam=genel_toplam)

@fis_bp.route("/fis_sil/<int:fis_id>")
def fis_sil(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    db.session.delete(fis)
    db.session.commit()
    flash("Fiş başarıyla silindi.", "success")
    return redirect(url_for("fis.fisleri_goruntule"))

@fis_bp.route("/fis_duzenle/<int:fis_id>", methods=["GET", "POST"])
def fis_duzenle(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    
    if request.method == "POST":
        try:
            veri = request.get_json()
            yeni_cari_kodu = veri.get("cari_kodu")
            kalemler = veri.get("kalemler", [])

            # 1. Stok Değişim Kontrolü ve Geri Alma (Reversal)
            stok_degisti = False
            if fis.cari_kodu != yeni_cari_kodu:
                stok_degisti = True
            else:
                eski_kalem_sayisi = sum(1 for d in fis.detaylar if not d.stok_disi)
                yeni_kalem_sayisi = sum(1 for k in kalemler if not k.get("stok_disi_birak", False))
                if eski_kalem_sayisi != yeni_kalem_sayisi:
                    stok_degisti = True
                else:
                    eski_kalemler_dict = {(d.agac_cinsi, d.birim, round(d.miktar, 2)): True for d in fis.detaylar if not d.stok_disi}
                    for k in kalemler:
                        if not k.get("stok_disi_birak", False):
                            key = (k["agac_cinsi"], k["birim"], round(float(k["miktar"]), 2))
                            if key not in eski_kalemler_dict:
                                stok_degisti = True
                                break

            if stok_degisti:
                eski_bildirimler = StokBildirim.query.filter_by(fis_id=fis.id).all()
                for b in eski_bildirimler:
                    if b.durum == 'onaylandi':
                        mevcut = MevcutStok.query.filter_by(cari_kodu=b.cari_kodu, kalem=b.kalem, birim=b.birim).first()
                        if mevcut:
                            if b.tip == 'dusum':
                                mevcut.miktar += b.islem_miktari
                            elif b.tip == 'ekleme':
                                mevcut.miktar = max(0.0, mevcut.miktar - b.islem_miktari)
                    db.session.delete(b)
            
            # Eski detayları temizle
            FisDetayi.query.filter_by(fis_id=fis.id).delete()
            
            # Fiş bilgilerini güncelle
            tarih_str = veri.get("tarih")
            if tarih_str:
                fis.tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date()
            
            fis.sevk_eden_cari = veri["sevk_eden_cari"].strip()
            fis.cari_kodu = yeni_cari_kodu
            fis.sevk_yeri_fabrika = veri["sevk_yeri_fabrika"].strip()
            fis.fabrika_kodu = veri.get("fabrika_kodu")
            fis.sevk_yeri_fis_no = veri["sevk_yeri_fis_no"].strip()
            fis.plaka_no = veri["plaka_no"].strip()
            for k in kalemler:
                miktar = float(k["miktar"])
                birim_fiyat = float(k["birim_fiyat"])
                toplam_tutar = round(miktar * birim_fiyat, 2)
                k_stok_disi = k.get("stok_disi_birak", False)
                
                yeni_detay = FisDetayi(
                    fis_id=fis.id,
                    agac_cinsi=k["agac_cinsi"],
                    cap=k.get("cap", "-") or "-",
                    miktar=miktar,
                    birim=k["birim"],
                    birim_fiyat=birim_fiyat,
                    toplam_tutar=toplam_tutar,
                    stok_disi=k_stok_disi
                )
                db.session.add(yeni_detay)

                # 2. Yeni bildirimleri oluştur (Eğer stok dışı bırakılmamışsa VE stok değişmişse)
                if not k_stok_disi and stok_degisti:
                    cari_obj = db.session.get(Cari, fis.cari_kodu) if fis.cari_kodu else None
                    if cari_obj:
                        bildirim = StokBildirim(
                            tip='dusum',
                            cari_kodu=cari_obj.firma_kodu,
                            kalem=k["agac_cinsi"],
                            islem_miktari=miktar,
                            birim=k["birim"],
                            durum='bekliyor',
                            fis_id=fis.id
                        )
                        db.session.add(bildirim)
                
            db.session.commit()
            return jsonify({"durum": "basarili", "mesaj": "Fiş başarıyla güncellendi."})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"durum": "hata", "mesaj": str(e)}), 500

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
        "fis_duzenle.html",
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
    fis = Fis.query.get_or_404(fis_id)
    return ReportService.generate_excel_for_fis(fis)

@fis_bp.route("/tek_fis_pdf/<int:fis_id>")
def tek_fis_pdf(fis_id):
    fis = Fis.query.get_or_404(fis_id)
    pdf_config = get_pdf_config(current_app)
    response = ReportService.generate_pdf_for_fis(fis, pdf_config)
    if isinstance(response, tuple):
        flash(f"PDF oluşturulurken hata oluştu: {response[1]}", "danger")
        return redirect(url_for("fis.fis_detay", fis_id=fis.id))
    return response
