from .extensions import db
from .utils import get_istanbul_time

class Fis(db.Model):
    __tablename__ = "fis"

    id = db.Column(db.Integer, primary_key=True)
    tarih = db.Column(db.Date, nullable=False, default=lambda: get_istanbul_time().date())
    sevk_eden_cari = db.Column(db.String(200), nullable=False)
    cari_kodu = db.Column(db.String(20), db.ForeignKey("cari.firma_kodu"), nullable=True)
    sevk_yeri_fabrika = db.Column(db.String(200), nullable=False)
    fabrika_kodu = db.Column(db.String(20), db.ForeignKey("fabrika.firma_kodu"), nullable=True)
    sevk_yeri_fis_no = db.Column(db.String(100), nullable=False)
    plaka_no = db.Column(db.String(50), nullable=False)

    cari = db.relationship("Cari", foreign_keys=[cari_kodu])
    fabrika = db.relationship("Fabrika", foreign_keys=[fabrika_kodu])

    detaylar = db.relationship(
        "FisDetayi", backref="fis", lazy=True, cascade="all, delete-orphan"
    )
    bildirimler = db.relationship(
        "StokBildirim", backref="fis_rel", lazy=True, cascade="all, delete-orphan", foreign_keys="StokBildirim.fis_id"
    )

    @property
    def guncel_sevk_eden_cari(self):
        return self.cari.firma_adi if self.cari else self.sevk_eden_cari

    @property
    def guncel_sevk_yeri_fabrika(self):
        return self.fabrika.firma_adi if self.fabrika else self.sevk_yeri_fabrika

    def __repr__(self):
        return f"<Fis {self.id} – {self.plaka_no}>"


class FisDetayi(db.Model):
    __tablename__ = "fis_detayi"

    id = db.Column(db.Integer, primary_key=True)
    fis_id = db.Column(db.Integer, db.ForeignKey("fis.id"), nullable=False)
    agac_cinsi = db.Column(db.String(100), nullable=False)
    cap = db.Column(db.String(50), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(20), nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    toplam_tutar = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<FisDetayi {self.id} – {self.agac_cinsi}>"


class Cari(db.Model):
    __tablename__ = "cari"

    firma_kodu = db.Column(db.String(20), primary_key=True)
    firma_adi = db.Column(db.String(200), nullable=False)
    vergi_dairesi = db.Column(db.String(100))
    vergi_numarasi = db.Column(db.String(50))
    firma_adres = db.Column(db.Text)
    e_posta = db.Column(db.String(100))
    telefon_no = db.Column(db.String(20))
    aktif_mi = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Cari {self.firma_kodu} - {self.firma_adi}>"


class Fabrika(db.Model):
    __tablename__ = "fabrika"

    firma_kodu = db.Column(db.String(20), primary_key=True)
    firma_adi = db.Column(db.String(200), nullable=False)
    vergi_dairesi = db.Column(db.String(100))
    vergi_numarasi = db.Column(db.String(50))
    firma_adres = db.Column(db.Text)
    e_posta = db.Column(db.String(100))
    telefon_no = db.Column(db.String(20))
    aktif_mi = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Fabrika {self.firma_kodu} - {self.firma_adi}>"


class MevcutStok(db.Model):
    __tablename__ = "mevcut_stok"
    id = db.Column(db.Integer, primary_key=True)
    cari_kodu = db.Column(db.String(20), db.ForeignKey('cari.firma_kodu'), nullable=False)
    kalem = db.Column(db.String(100), nullable=False)
    miktar = db.Column(db.Float, nullable=False, default=0.0)
    birim = db.Column(db.String(20), nullable=False, default='Ton')
    cari = db.relationship('Cari')


class GelecekStok(db.Model):
    __tablename__ = "gelecek_stok"
    id = db.Column(db.Integer, primary_key=True)
    cari_kodu = db.Column(db.String(20), db.ForeignKey('cari.firma_kodu'), nullable=False)
    kalem = db.Column(db.String(100), nullable=False)
    miktar = db.Column(db.Float, nullable=False, default=0.0)
    birim = db.Column(db.String(20), nullable=False)
    teslim_tarihi = db.Column(db.Date, nullable=False)
    cari = db.relationship('Cari')
    bildirimler = db.relationship(
        "StokBildirim", backref="gelecek_stok_rel", lazy=True, cascade="all, delete-orphan", foreign_keys="StokBildirim.gelecek_stok_id"
    )


class StokBildirim(db.Model):
    __tablename__ = "stok_bildirim"
    id = db.Column(db.Integer, primary_key=True)
    tip = db.Column(db.String(20), nullable=False)
    cari_kodu = db.Column(db.String(20), db.ForeignKey('cari.firma_kodu'), nullable=False)
    kalem = db.Column(db.String(100), nullable=False)
    islem_miktari = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(20), nullable=False, default='Ton')
    durum = db.Column(db.String(20), nullable=False, default='bekliyor')
    fis_id = db.Column(db.Integer, db.ForeignKey('fis.id'), nullable=True)
    gelecek_stok_id = db.Column(db.Integer, db.ForeignKey('gelecek_stok.id'), nullable=True)
    cari = db.relationship('Cari')
