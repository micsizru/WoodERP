from datetime import date, datetime
from app.extensions import db
from app.models import Fis, FisDetayi, Cari, StokBildirim, MevcutStok

class FisService:
    @staticmethod
    def create_fis(veri):
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
            raise ValueError("En az bir kalem satırı eklemelisiniz.")

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
        return yeni_fis.id

    @staticmethod
    def update_fis(fis_id, veri):
        fis = Fis.query.get_or_404(fis_id)
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

    @staticmethod
    def delete_fis(fis_id):
        fis = Fis.query.get_or_404(fis_id)
        db.session.delete(fis)
        db.session.commit()
