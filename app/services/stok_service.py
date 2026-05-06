from datetime import date, datetime
from app.extensions import db
from app.models import MevcutStok, GelecekStok, StokBildirim

class StokService:
    @staticmethod
    def process_future_stocks():
        bugun = date.today()
        zamani_gelenler = GelecekStok.query.filter(GelecekStok.teslim_tarihi <= bugun).all()
        if zamani_gelenler:
            aktif_bildirimler = StokBildirim.query.filter(StokBildirim.durum.in_(['bekliyor', 'reddedildi'])).all()
            aktif_gelecek_stok_idleri = {b.gelecek_stok_id for b in aktif_bildirimler if b.gelecek_stok_id is not None}
            
            yeni_bildirimler = []
            for g in zamani_gelenler:
                if g.id not in aktif_gelecek_stok_idleri:
                    yeni_bildirimler.append(StokBildirim(
                        tip='ekleme',
                        cari_kodu=g.cari_kodu,
                        kalem=g.kalem,
                        islem_miktari=g.miktar,
                        birim=g.birim,
                        durum='bekliyor',
                        gelecek_stok_id=g.id
                    ))
            if yeni_bildirimler:
                db.session.bulk_save_objects(yeni_bildirimler)
                db.session.commit()

    @staticmethod
    def approve_notification(bildirim_id):
        bildirim = StokBildirim.query.get_or_404(bildirim_id)
        if bildirim.durum != 'bekliyor':
            return False

        mevcut = MevcutStok.query.filter_by(cari_kodu=bildirim.cari_kodu, kalem=bildirim.kalem, birim=bildirim.birim).first()
        if bildirim.tip == 'dusum':
            if mevcut:
                mevcut.miktar = max(0.0, mevcut.miktar - bildirim.islem_miktari)
            else:
                yeni_stok = MevcutStok(
                    cari_kodu=bildirim.cari_kodu,
                    kalem=bildirim.kalem,
                    miktar=0.0,
                    birim=bildirim.birim
                )
                db.session.add(yeni_stok)
        elif bildirim.tip == 'ekleme':
            if mevcut:
                mevcut.miktar += bildirim.islem_miktari
            else:
                yeni_stok = MevcutStok(
                    cari_kodu=bildirim.cari_kodu,
                    kalem=bildirim.kalem,
                    miktar=bildirim.islem_miktari,
                    birim=bildirim.birim
                )
                db.session.add(yeni_stok)
        
        bildirim.durum = 'onaylandi'
        if bildirim.gelecek_stok_id:
            g_stok = GelecekStok.query.get(bildirim.gelecek_stok_id)
            if g_stok:
                db.session.delete(g_stok)
                
        db.session.commit()
        return True

    @staticmethod
    def reject_notification(bildirim_id):
        bildirim = StokBildirim.query.get_or_404(bildirim_id)
        if bildirim.durum != 'bekliyor':
            return False
        
        bildirim.durum = 'reddedildi'
        db.session.commit()
        return True

    @staticmethod
    def add_manual_stock(veri):
        cari_kodu = veri.get("cari_kodu")
        kalem = veri.get("kalem")
        miktar = float(veri.get("miktar", 0))
        birim = veri.get("birim", "Ton")
        
        mevcut = MevcutStok.query.filter_by(cari_kodu=cari_kodu, kalem=kalem, birim=birim).first()
        if mevcut:
            mevcut.miktar += miktar
        else:
            yeni = MevcutStok(cari_kodu=cari_kodu, kalem=kalem, miktar=miktar, birim=birim)
            db.session.add(yeni)
        
        db.session.commit()

    @staticmethod
    def add_future_stock(veri):
        cari_kodu = veri.get("cari_kodu")
        kalem = veri.get("kalem")
        miktar = float(veri.get("miktar", 0))
        birim = veri.get("birim", "Ton")
        teslim_tarihi_str = veri.get("teslim_tarihi")
        
        tarih = datetime.strptime(teslim_tarihi_str, "%Y-%m-%d").date() if teslim_tarihi_str else date.today()
        yeni = GelecekStok(cari_kodu=cari_kodu, kalem=kalem, miktar=miktar, birim=birim, teslim_tarihi=tarih)
        db.session.add(yeni)
        db.session.commit()

    @staticmethod
    def delete_stock(tip, id):
        if tip == 'mevcut':
            kayit = MevcutStok.query.get_or_404(id)
        elif tip == 'gelecek':
            kayit = GelecekStok.query.get_or_404(id)
            StokBildirim.query.filter_by(gelecek_stok_id=kayit.id).delete()
        else:
            raise ValueError("Geçersiz işlem tipi.")
            
        db.session.delete(kayit)
        db.session.commit()

    @staticmethod
    def update_stock(tip, id, veri):
        if tip == 'mevcut':
            kayit = MevcutStok.query.get_or_404(id)
            kayit.cari_kodu = veri.get("cari_kodu")
            kayit.kalem = veri.get("kalem")
            kayit.miktar = float(veri.get("miktar", 0))
            kayit.birim = veri.get("birim", "Ton")
        elif tip == 'gelecek':
            kayit = GelecekStok.query.get_or_404(id)
            kayit.cari_kodu = veri.get("cari_kodu")
            kayit.kalem = veri.get("kalem")
            kayit.miktar = float(veri.get("miktar", 0))
            kayit.birim = veri.get("birim", "Ton")
            teslim_tarihi_str = veri.get("teslim_tarihi")
            if teslim_tarihi_str:
                kayit.teslim_tarihi = datetime.strptime(teslim_tarihi_str, "%Y-%m-%d").date()
                
            bildirim = StokBildirim.query.filter_by(gelecek_stok_id=kayit.id).filter(StokBildirim.durum.in_(['bekliyor', 'reddedildi'])).first()
            if bildirim:
                if kayit.teslim_tarihi > date.today():
                    db.session.delete(bildirim)
                else:
                    if bildirim.durum == 'reddedildi':
                        bildirim.durum = 'bekliyor'
                    bildirim.cari_kodu = kayit.cari_kodu
                    bildirim.kalem = kayit.kalem
                    bildirim.islem_miktari = kayit.miktar
                    bildirim.birim = kayit.birim
        else:
            raise ValueError("Geçersiz işlem tipi.")
            
        db.session.commit()
