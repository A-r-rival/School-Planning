import sys
import sqlite3
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QPushButton, QTimeEdit, QVBoxLayout, 
    QListWidget, QComboBox, QLabel, QHBoxLayout, QCompleter, QMessageBox
)
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QRegExp

class GenelArayuz(QWidget):
    def __init__(self):
        super().__init__()
        self.veritabani_olustur()
        self.setWindowTitle("Ders Programı Oluşturucu")
        self.setGeometry(100, 100, 400, 600)  # Increased height for better visibility

        # Main layout
        layout = QVBoxLayout()

        # Course input fields
        self.ders_input = QLineEdit()
        self.ders_input.setPlaceholderText("Ders Adı")
        layout.addWidget(self.ders_input)

        # Teacher input with autocomplete
        self.hoca_input = QLineEdit()
        self.hoca_input.setPlaceholderText("Hoca Adı")
        layout.addWidget(self.hoca_input)

        # Day selection
        self.gun_input = QComboBox()
        self.gun_input.addItems(["Pazartesi", "Salı", "Çarşamba", "Perşembe", 
                                "Cuma", "Cumartesi", "Pazar"])
        layout.addWidget(self.gun_input)

        # Time inputs
        # Improved time input ergonomics
        saat_layout = QHBoxLayout()
        self.saat_baslangic = QTimeEdit()
        self.saat_baslangic.setDisplayFormat("HH:mm")
        self.saat_baslangic.setTime(self.saat_baslangic.minimumTime())
        self.saat_bitis = QTimeEdit()
        self.saat_bitis.setDisplayFormat("HH:mm")
        self.saat_bitis.setTime(self.saat_bitis.minimumTime())
        
        # Auto-fill end time when start time changes
        self.saat_baslangic.timeChanged.connect(self.auto_fill_end_time)
        
        saat_layout.addWidget(QLabel("Başlangıç:"))
        saat_layout.addWidget(self.saat_baslangic)
        saat_layout.addWidget(QLabel("Bitiş:"))
        saat_layout.addWidget(self.saat_bitis)
        layout.addLayout(saat_layout)

        # Buttons
        self.ekle_button = QPushButton("Dersi Ekle")
        self.ekle_button.clicked.connect(self.ders_ekle)
        layout.addWidget(self.ekle_button)

        self.sil_button = QPushButton("Seçili Dersi Sil")
        self.sil_button.clicked.connect(self.ders_sil)
        layout.addWidget(self.sil_button)

        # Course list
        self.ders_listesi = QListWidget()
        layout.addWidget(self.ders_listesi)

        self.setLayout(layout)
        self.eski_verileri_yukle()
        self.hoca_input.setCompleter(QCompleter(self.hocalari_getir()))

    def auto_fill_end_time(self):
        """Automatically set end time to 50 minutes after start time"""
        start_time = self.saat_baslangic.time()
        end_time = start_time.addSecs(55 * 60)  # Add 50 minutes
        self.saat_bitis.setTime(end_time)

    def ders_ekle(self):
        ders = self.ders_input.text().strip()
        hoca = self.hoca_input.text().strip()
        gun = self.gun_input.currentText()
        bas = self.saat_baslangic.time().toString("HH:mm")
        bit = self.saat_bitis.time().toString("HH:mm")
        
        # Validation
        if not ders or not hoca:
            self.show_error("Ders adı ve hoca adı boş olamaz!")
            return
        
        if self.saat_baslangic.time() >= self.saat_bitis.time():
            self.show_error("Başlangıç saati bitiş saatinden önce olmalıdır!")
            return
            
        # Check for time conflicts
        if self.zaman_cakismasi_kontrol(gun, bas, bit):
            self.show_error("Bu saat aralığında zaten bir ders var!")
            return
        
        saat = f"{bas}-{bit}"

        # Add to database
        self.cursor.execute("INSERT INTO dersler (ders, hoca, gun, saat) VALUES (?, ?, ?, ?)",
                          (ders, hoca, gun, saat))
        self.conn.commit()

        # Add to list
        bilgi = f"{ders} - {hoca} - {gun} {saat}"
        self.ders_listesi.addItem(bilgi)

        # Clear inputs
        self.ders_input.clear()
        self.hoca_input.clear()
        self.saat_baslangic.setTime(self.saat_baslangic.minimumTime())
        self.saat_bitis.setTime(self.saat_bitis.minimumTime())

        # Update autocomplete
        self.hoca_input.setCompleter(QCompleter(self.hocalari_getir()))

    def ders_sil(self):
        secili = self.ders_listesi.currentItem()
        if not secili:
            return

        try:
            parts = secili.text().split(" - ")
            if len(parts) == 3:
                ders, hoca, time_info = parts
                gun, saat = time_info.split(" ")
                
                self.cursor.execute("""
                    DELETE FROM dersler 
                    WHERE ders=? AND hoca=? AND gun=? AND saat=?
                """, (ders, hoca, gun, saat))
                self.conn.commit()
                
                self.ders_listesi.takeItem(self.ders_listesi.row(secili))
        except Exception as e:
            print(f"Silme hatası: {e}")

    def hocalari_getir(self):
        self.cursor.execute("SELECT DISTINCT hoca FROM dersler WHERE hoca IS NOT NULL AND hoca != ''")
        return [satir[0] for satir in self.cursor.fetchall()]

    def veritabani_olustur(self):
        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(script_dir, "dersler.db")
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS dersler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ders TEXT NOT NULL,
                hoca TEXT NOT NULL,
                gun TEXT NOT NULL,
                saat TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def eski_verileri_yukle(self):
        self.cursor.execute("SELECT ders, hoca, gun, saat FROM dersler")
        for ders, hoca, gun, saat in self.cursor.fetchall():
            bilgi = f"{ders} - {hoca} - {gun} {saat}"
            self.ders_listesi.addItem(bilgi)

    def show_error(self, message):
        """Show error message to user"""
        QMessageBox.warning(self, "Hata", message)
    
    def zaman_cakismasi_kontrol(self, gun, baslangic, bitis):
        """Check for time conflicts on the same day"""
        self.cursor.execute("SELECT saat FROM dersler WHERE gun = ?", (gun,))
        mevcut_saatler = self.cursor.fetchall()
        
        for (saat_str,) in mevcut_saatler:
            mevcut_bas, mevcut_bit = saat_str.split('-')
            # Check if time ranges overlap
            if (baslangic < mevcut_bit and bitis > mevcut_bas):
                return True
        return False

    def closeEvent(self, event):
        self.conn.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = GenelArayuz()
    pencere.show()
    sys.exit(app.exec_())