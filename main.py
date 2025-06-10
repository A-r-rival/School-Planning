import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QPushButton,
    QVBoxLayout, QListWidget, QComboBox, QLabel, QHBoxLayout, QCompleter
)
from PyQt5.QtGui import QIntValidator

class GenelArayuz(QWidget):
    def __init__(self):
        super().__init__() #Eğer super().__init__() yazılmazsa, QWidget sınıfının başlatıcısı (constructor) çağrılmaz
        self.veritabani_olustur()
        self.setWindowTitle("Ders Programı Oluşturucu")
        self.setGeometry(100, 100, 400, 400)

        # Giriş alanları
        self.ders_input = QLineEdit()
        self.ders_input.setPlaceholderText("Ders Adı")

        self.hoca_input = QLineEdit()
        self.hoca_input.setPlaceholderText("Hoca Adı")
        self.hoca_input.setCompleter(QCompleter(self.hocalari_getir()))

        self.gun_input = QComboBox()
        self.gun_input.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])

        # Saat giriş alanları
        saat_layout = QHBoxLayout()
        self.saat_baslangic = QLineEdit()
        self.saat_baslangic.setPlaceholderText("Başlangıç (hhmm)")
        self.saat_baslangic.setMaxLength(5)
        self.saat_baslangic.setValidator(QIntValidator(0, 12359))

        self.saat_bitis = QLineEdit()
        self.saat_bitis.setPlaceholderText("Bitiş (hhmm)")
        self.saat_bitis.setMaxLength(5)
        self.saat_bitis.setValidator(QIntValidator(0, 12359))

        saat_layout.addWidget(self.saat_baslangic)
        saat_layout.addWidget(QLabel(" - "))
        saat_layout.addWidget(self.saat_bitis)

        # Buton ve liste
        self.ekle_button = QPushButton("Dersi Ekle")
        self.ekle_button.clicked.connect(self.ders_ekle)

        self.sil_button = QPushButton("Seçili Dersi Sil")
        self.sil_button.clicked.connect(self.ders_sil)

        self.ders_listesi = QListWidget()

        # Arayüz düzeni
        layout = QVBoxLayout()
        layout.addWidget(self.ders_input)
        layout.addWidget(self.hoca_input)
        layout.addWidget(self.gun_input)
        layout.addLayout(saat_layout)
        layout.addWidget(self.ekle_button)
        layout.addWidget(self.sil_button)
        layout.addWidget(self.ders_listesi)

        self.setLayout(layout)
        self.eski_verileri_yukle()

    def format_saat(self, s):
        s = s.replace(":", "").zfill(4)
        return f"{s[:2]}:{s[2:]}" if len(s) == 4 else s

    def ders_ekle(self):
        ders = self.ders_input.text()
        hoca = self.hoca_input.text()
        gun = self.gun_input.currentText()
        bas = self.format_saat(self.saat_baslangic.text())
        bit = self.format_saat(self.saat_bitis.text())
        saat = f"{bas}-{bit}"

        # Veritabanına ekle
        self.cursor.execute("INSERT INTO dersler (ders, hoca, gun, saat) VALUES (?, ?, ?, ?)",
                            (ders, hoca, gun, saat))
        self.conn.commit()

        bilgi = f"{ders} - {hoca} - {gun} {saat}"
        self.ders_listesi.addItem(bilgi)

        # Temizle
        self.ders_input.clear()
        self.hoca_input.clear()
        self.saat_baslangic.clear()
        self.saat_bitis.clear()

        self.hoca_input.setCompleter(QCompleter(self.hocalari_getir()))

    def ders_sil(self):
        secili = self.ders_listesi.currentItem()
        if secili:
            metin = secili.text()
            try:
                ders, hoca, kalan = metin.split(" - ")
                gun, saat = kalan.split(" ")
                self.cursor.execute("DELETE FROM dersler WHERE ders=? AND hoca=? AND gun=? AND saat=?",
                                    (ders, hoca, gun, saat))
                self.conn.commit()
                self.ders_listesi.takeItem(self.ders_listesi.row(secili))
            except:
                pass

    def hocalari_getir(self):
        self.cursor.execute("SELECT DISTINCT hoca FROM dersler")
        return [satir[0] for satir in self.cursor.fetchall() if satir[0]]

    def veritabani_olustur(self):
        self.conn = sqlite3.connect("dersler.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dersler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ders TEXT,
                hoca TEXT,
                gun TEXT,
                saat TEXT
            )
        """)
        self.conn.commit()

    def eski_verileri_yukle(self):
        self.cursor.execute("SELECT ders, hoca, gun, saat FROM dersler")
        for ders, hoca, gun, saat in self.cursor.fetchall():
            bilgi = f"{ders} - {hoca} - {gun} {saat}"
            self.ders_listesi.addItem(bilgi)

    def closeEvent(self, event):
        self.conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = GenelArayuz()
    pencere.show()
    sys.exit(app.exec_())
