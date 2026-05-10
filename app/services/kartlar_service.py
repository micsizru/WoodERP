from datetime import timedelta
from app.extensions import db
from app.models import Cari, Fabrika, Fis, FisDetayi
from app.utils import istanbul_simdi, yeni_firma_kodu_uret

class KartlarService:
    @staticmethod
    def get_hacim(firma_adi, firma_kodu, tip='cari'):
        """
        Bir firmanın (Cari veya Fabrika) toplam işlem hacmini hesaplar.
        Tüm zamanlar, bu ay ve son 30 gün verilerini döner.
        """
        now = istanbul_simdi()
        # Zaman aralıklarını belirle (Ayın başı ve 30 gün öncesi)
        bu_ay_baslangic = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        son_30_gun_baslangic = (now - timedelta(days=30)).replace(hour=0, minute=0, second=0, microsecond=0)

        # Veritabanında fiş detayları üzerinden toplam tutarı sorgula
        sorgu_base = db.session.query(db.func.sum(FisDetayi.toplam_tutar)).join(Fis)
        
        # Filtreleme: Cari mi yoksa Fabrika mı sorgulanıyor?
        if tip == 'cari':
            sorgu_base = sorgu_base.filter(Fis.cari_kodu == firma_kodu)
        else:
            sorgu_base = sorgu_base.filter(Fis.fabrika_kodu == firma_kodu)
        
        # Farklı zaman dilimleri için sonuçları al (Hic veri yoksa 0.0 döner)
        tum_zamanlar = sorgu_base.scalar() or 0.0
        bu_ay = sorgu_base.filter(Fis.tarih >= bu_ay_baslangic.date()).scalar() or 0.0
        son_30 = sorgu_base.filter(Fis.tarih >= son_30_gun_baslangic.date()).scalar() or 0.0
        
        # Sonuçları yuvarlayarak bir sözlük (dictionary) yapısında döndür
        return {
            'tum': round(tum_zamanlar, 2),
            'bu_ay': round(bu_ay, 2),
            'son_30': round(son_30, 2)
        }

    @staticmethod
    def add_kart(tur, data):
        """
        Yeni bir Cari veya Fabrika kaydı oluşturur.
        """
        # Gelen türe göre hangi veritabanı tablosunu kullanacağımızı seçiyoruz
        Model = Cari if tur == 'cari' else Fabrika
        
        firma_adi = data.get("firma_adi", "").strip()
        if not firma_adi:
            raise ValueError("Firma adı zorunludur.")
            
        # Aynı isimde aktif bir kayıt var mı kontrol et (Mükerrer kaydı önle)
        mevcut = Model.query.filter_by(firma_adi=firma_adi, aktif_mi=True).first()
        if mevcut:
            raise ValueError(f"Bu firma adı zaten mevcut: {firma_adi}")
            
        # utils.py içindeki fonksiyonu kullanarak sıradaki firma kodunu üret (örn: CAR-001)
        yeni_kod = yeni_firma_kodu_uret(tur, Cari, Fabrika)
        
        # Yeni nesneyi oluştur
        yeni_kart = Model(
            firma_kodu=yeni_kod,
            firma_adi=firma_adi,
            vergi_dairesi=data.get("vergi_dairesi", "").strip(),
            vergi_numarasi=data.get("vergi_numarasi", "").strip(),
            firma_adres=data.get("firma_adres", "").strip(),
            e_posta=data.get("e_posta", "").strip(),
            telefon_no=data.get("telefon_no", "").strip()
        )
        
        # Veritabanına ekle ve işlemleri onayla (commit)
        db.session.add(yeni_kart)
        db.session.commit()
        return yeni_kod

    @staticmethod
    def edit_kart(tur, firma_kodu, data):
        """
        Mevcut bir kaydın bilgilerini günceller.
        """
        Model = Cari if tur == 'cari' else Fabrika
        # Kaydı bul, yoksa 404 hatası fırlat
        kart = Model.query.get_or_404(firma_kodu)
        
        yeni_ad = data.get("firma_adi", "").strip()
        if not yeni_ad:
            raise ValueError("Firma adı zorunludur.")
            
        # İsim değiştiyse, yeni ismin başka birinde olup olmadığını kontrol et
        mevcut = Model.query.filter(Model.firma_adi == yeni_ad, Model.firma_kodu != firma_kodu, Model.aktif_mi == True).first()
        if mevcut:
            raise ValueError(f"Bu firma adı başka bir kayıtta kullanılıyor: {yeni_ad}")
            
        # Bilgileri güncelle
        kart.firma_adi = yeni_ad
        kart.vergi_dairesi = data.get("vergi_dairesi", "").strip()
        kart.vergi_numarasi = data.get("vergi_numarasi", "").strip()
        kart.firma_adres = data.get("firma_adres", "").strip()
        kart.e_posta = data.get("e_posta", "").strip()
        kart.telefon_no = data.get("telefon_no", "").strip()
        
        db.session.commit()
        return kart

    @staticmethod
    def delete_kart(tur, firma_kodu):
        """
        Kaydı silmez, sadece 'aktif_mi' bayrağını indirir.
        Böylece geçmişe dönük veriler (fişler vs.) bozulmaz.
        """
        Model = Cari if tur == 'cari' else Fabrika
        kart = Model.query.get_or_404(firma_kodu)
        kart.aktif_mi = False  # Soft Delete (Yumuşak Silme)
        db.session.commit()
