from datetime import date, datetime
from app.extensions import db
from app.models import Fis, FisDetayi, Cari, StokBildirim, MevcutStok

class FisService:
    """
    Fiş (Receipt) yönetim süreçlerini (oluşturma, güncelleme, silme) ve buna bağlı 
    stok hareketlerini yöneten merkezi servis sınıfı.
    """

    @staticmethod
    def create_fis(veri):
        """
        Yeni bir fiş ve buna bağlı kalemleri oluşturur. 
        Her kalem için otomatik stok düşüm bildirimi tetikler.
        """
        # 1. Ana Fiş Bilgisinin Hazırlanması
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
        db.session.flush() # ID alabilmek için veritabanına ön gönderim yapıyoruz.

        kalemler = veri.get("kalemler", [])
        if not kalemler:
            raise ValueError("En az bir kalem satırı eklemelisiniz.")

        # N+1 Optimizasyonu: Cari bilgisini döngü dışına alarak veritabanı spam'ini engelliyoruz.
        cari_obj = db.session.get(Cari, yeni_fis.cari_kodu) if yeni_fis.cari_kodu else None
        
        # 2. Kalemlerin (FisDetayi) ve Stok Bildirimlerinin İşlenmesi
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

            # Stok takibi istenmişse ve geçerli bir Cari kartı varsa bildirim oluştur.
            if not k_stok_disi and cari_obj:
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

        db.session.commit() # Tüm işlemler başarılıysa tek seferde kalıcı hale getir.
        return yeni_fis.id

    @staticmethod
    def stok_degisikligi_var_mi(fis, yeni_kalemler, yeni_cari_kodu):
        """
        Fiş üzerindeki kalemlerin veya carinin stok etkileyen bir değişikliğe uğrayıp 
        uğramadığını kontrol eden dedektör fonksiyon.
        """
        # Cari değişmişse stok otomatik olarak değişmiş sayılır (eski cariden iade, yeniye düşüm).
        if fis.cari_kodu != yeni_cari_kodu:
            return True
            
        # Sadece stok takibi yapılan (stok_disi olmayan) kalemleri filtrele.
        eski_kalemler = [d for d in fis.detaylar if not d.stok_disi]
        yeni_kalemler_stoklu = [k for k in yeni_kalemler if not k.get("stok_disi_birak", False)]
        
        # Kalem sayısı değişmişse doğrudan True dön.
        if len(eski_kalemler) != len(yeni_kalemler_stoklu):
            return True
            
        # İçerik kontrolü: Cins, Birim veya Miktar değişmiş mi? (O(N) karmaşıklığında hızlı kontrol)
        eski_dict = {(d.agac_cinsi, d.birim, round(d.miktar, 2)): True for d in eski_kalemler}
        for k in yeni_kalemler_stoklu:
            key = (k["agac_cinsi"], k["birim"], round(float(k["miktar"]), 2))
            if key not in eski_dict:
                return True # Herhangi bir kalem farklıysa stok değişmiştir.
        return False

    @staticmethod
    def stoklari_geri_al(fis_id, cari_kodu):
        """
        Fişe bağlı onaylı stok hareketlerini geri çeker. 
        Lookup Table optimizasyonu ile N+1 sorgu problemini çözer.
        """
        eski_bildirimler = StokBildirim.query.filter_by(fis_id=fis_id).all()
        if not eski_bildirimler:
            return

        # N+1 Çözümü: Cari'ye ait tüm mevcut stokları tek bir SELECT ile çekip belleğe (dict) alıyoruz.
        mevcut_stoklar = {
            (s.kalem, s.birim): s 
            for s in MevcutStok.query.filter_by(cari_kodu=cari_kodu).all()
        }
        
        for b in eski_bildirimler:
            # Sadece onaylanmış bildirimlerin rakamsal etkisi olduğu için onları geri çekiyoruz.
            if b.durum == 'onaylandi':
                mevcut = mevcut_stoklar.get((b.kalem, b.birim))
                if mevcut:
                    if b.tip == 'dusum':
                        mevcut.miktar += b.islem_miktari # Düşülen miktarı iade et.
                    elif b.tip == 'ekleme':
                        mevcut.miktar = max(0.0, mevcut.miktar - b.islem_miktari) # Ekleneni geri al.
            
            # Bildirim her durumda silinmeli ki yenileriyle çakışmasın.
            db.session.delete(b)

    @staticmethod
    def fis_metadata_guncelle(fis, veri):
        """Fişin ana meta verilerini (tarih, plaka, sevk bilgileri) günceller."""
        tarih_str = veri.get("tarih")
        if tarih_str:
            fis.tarih = datetime.strptime(tarih_str, "%Y-%m-%d").date()
        
        fis.sevk_eden_cari = veri["sevk_eden_cari"].strip()
        fis.cari_kodu = veri.get("cari_kodu")
        fis.sevk_yeri_fabrika = veri["sevk_yeri_fabrika"].strip()
        fis.fabrika_kodu = veri.get("fabrika_kodu")
        fis.sevk_yeri_fis_no = veri["sevk_yeri_fis_no"].strip()
        fis.plaka_no = veri["plaka_no"].strip()

    @staticmethod
    def update_fis(fis_id, veri):
        """
        Mevcut fişi günceller. Stok değişimlerini algılar, gerekiyorsa 
        eski hareketleri geri alır ve yenilerini oluşturur.
        """
        fis = Fis.query.get_or_404(fis_id)
        eski_cari_kodu = fis.cari_kodu
        yeni_cari_kodu = veri.get("cari_kodu")
        yeni_kalemler = veri.get("kalemler", [])

        # 1. Stok Değişim Analizi
        stok_degisti = FisService.stok_degisikligi_var_mi(fis, yeni_kalemler, yeni_cari_kodu)

        # 2. Reversal (Geri Alma) İşlemi: Stok etkileyen bir değişim varsa eskiyi temizle.
        if stok_degisti:
            FisService.stoklari_geri_al(fis.id, eski_cari_kodu)
        
        # 3. Temizlik ve Başlık Güncelleme
        # Detayları silip yeniden oluşturmak, "update" yerine "replace" mantığıyla veri bütünlüğünü korur.
        FisDetayi.query.filter_by(fis_id=fis.id).delete()
        FisService.fis_metadata_guncelle(fis, veri)

        # 4. Yeni İçeriğin Oluşturulması
        cari_obj = db.session.get(Cari, fis.cari_kodu) if fis.cari_kodu else None

        for k in yeni_kalemler:
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

            # Eğer stok değişmişse ve bu kalem stok takibine tabiyse yeni bildirim oluştur.
            if not k_stok_disi and stok_degisti and cari_obj:
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
            
        db.session.commit() # Tüm kompleks işlemler tek bir transaction olarak tamamlanır.

    @staticmethod
    def delete_fis(fis_id):
        """Fişi veritabanından tamamen siler. İlişkili detaylar (cascade) otomatik silinir."""
        fis = Fis.query.get_or_404(fis_id)
        db.session.delete(fis)
        db.session.commit()
