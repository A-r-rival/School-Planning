import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QListWidget
)

class GenelArayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ders Programı Oluşturucu")
        self.setGeometry(100, 100, 400, 300)

        # Giriş alanları
        self.ders_input = QLineEdit()
        self.ders_input.setPlaceholderText("Ders Adı")

        self.hoca_input = QLineEdit()
        self.hoca_input.setPlaceholderText("Hoca Adı")

        self.gun_input = QLineEdit()
        self.gun_input.setPlaceholderText("Gün (örn: Pazartesi)")

        self.saat_input = QLineEdit()
        self.saat_input.setPlaceholderText("Saat (örn: 09:00-11:00)")

        # Dersi Ekle butonu
        self.ekle_button = QPushButton("Dersi Ekle")
        self.ekle_button.clicked.connect(self.ders_ekle)

        # Eklenen dersleri gösterecek liste
        self.ders_listesi = QListWidget()

        self.veritabani_olustur()
        self.eski_verileri_yukle()

        # Arayüz düzeni
        layout = QVBoxLayout()
        layout.addWidget(self.ders_input)
        layout.addWidget(self.hoca_input)
        layout.addWidget(self.gun_input)
        layout.addWidget(self.saat_input)
        layout.addWidget(self.ekle_button)
        layout.addWidget(self.ders_listesi)

        self.setLayout(layout)
    

    def ders_ekle(self):
        ders = self.ders_input.text()
        hoca = self.hoca_input.text()
        gun = self.gun_input.text()
        saat = self.saat_input.text()

        # Veritabanına ekle
        self.cursor.execute("INSERT INTO dersler (ders, hoca, gun, saat) VALUES (?, ?, ?, ?)",
                            (ders, hoca, gun, saat))
        self.conn.commit()

        bilgi = f"{ders} - {hoca} - {gun} {saat}"
        self.ders_listesi.addItem(bilgi)

        # Alanları temizle
        self.ders_input.clear()
        self.hoca_input.clear()
        self.gun_input.clear()
        self.saat_input.clear()

                
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
