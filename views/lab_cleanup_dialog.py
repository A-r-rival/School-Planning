from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QComboBox, QSpinBox, QMessageBox, QHeaderView,
                             QGroupBox, QFormLayout, QTimeEdit, QCheckBox)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtGui import QColor

class LabCleanupDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Laboratuvar Temizlik Ayarları")
        self.resize(800, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        info_lbl = QLabel("Laboratuvarlar için her dersten sonra otomatik boş bırakılacak veya haftalık bloklanacak temizlik süresini ayarlayabilirsiniz.\n"
                          "Varsayılan olarak laboratuvarlarda temizlik süresi (NONE) yoktur ve peş peşe ders atanabilir.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #AAAAAA; font-style: italic; margin-bottom: 10px;")
        layout.addWidget(info_lbl)

        # Category Toggle
        self.chk_show_category = QCheckBox("Kategori Sütununu Göster")
        self.chk_show_category.setChecked(False)
        self.chk_show_category.toggled.connect(lambda checked: self.table.setColumnHidden(2, not checked))
        layout.addWidget(self.chk_show_category)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Lab ID", "Lab Adı", "Kategori", "Temizlik Tipi", "Süre (dk)", "Gün", "Saat"])
        self.table.setColumnWidth(0, 50) # Reduce ID column width
        self.table.setColumnHidden(2, True) # Hide category by default
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        layout.addWidget(self.table)

        # Edit Controls
        edit_group = QGroupBox("Seçili Lab Ayarını Düzenle")
        form_layout = QFormLayout(edit_group)

        self.combo_type = QComboBox()
        self.combo_type.addItems(["NONE (Normal Kurallar)", "Her Ders Sonrası (AFTER_LESSON)", "Haftalık Belirli Saat (WEEKLY)"])
        self.combo_type.currentIndexChanged.connect(self.on_type_changed)
        
        self.combo_day = QComboBox()
        self.combo_day.addItems(["", "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"])
        
        self.time_start = QTimeEdit()
        self.time_start.setDisplayFormat("HH:mm")
        
        self.spin_duration = QSpinBox()
        self.spin_duration.setRange(0, 120)
        self.spin_duration.setSingleStep(30)
        self.spin_duration.setValue(30)
        self.spin_duration.setSuffix(" dk")

        form_layout.addRow("Temizlik Tipi:", self.combo_type)
        form_layout.addRow("Gün (Sadece Haftalık):", self.combo_day)
        form_layout.addRow("Başlangıç (Sadece Haftalık):", self.time_start)
        form_layout.addRow("Temizlik Süresi:", self.spin_duration)

        btn_save = QPushButton("💾 Seçili Laba Kaydet")
        btn_save.clicked.connect(self.save_selected)
        btn_save.setStyleSheet("background-color: #2962FF; color: white; font-weight: bold; padding: 6px;")
        
        btn_apply_all = QPushButton("📋 Aynı Kategorideki Tüm Lablara Uygula")
        btn_apply_all.clicked.connect(self.apply_to_category)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_apply_all)
        form_layout.addRow("", btn_layout)

        layout.addWidget(edit_group)

        self.btn_close = QPushButton("Kapat")
        self.btn_close.clicked.connect(self.accept)
        layout.addWidget(self.btn_close, alignment=Qt.AlignRight)

    def get_category(self, lab_name):
        name_lower = lab_name.lower()
        if "bilgisayar" in name_lower or "yazılım" in name_lower or "pc" in name_lower:
            return "Bilgisayar"
        elif "kimya" in name_lower:
            return "Kimya"
        elif "fizik" in name_lower:
            return "Fizik"
        elif "mekatronik" in name_lower or "makine" in name_lower:
            return "Mekatronik"
        elif "elektrik" in name_lower or "elektronik" in name_lower:
            return "Elektrik/Elektronik"
        return "Diğer Lab"

    def load_data(self):
        try:
            rooms = self.controller.model.aktif_derslikleri_getir()
            settings = self.controller.model.get_lab_cleanup_settings()

            lab_rooms = []
            for r in rooms:
                r_id = r[0]
                r_name = r[1]
                r_type = r[2] if len(r) > 2 else ""
                if r_type and "lab" in r_type.lower() or "lab" in r_name.lower():
                    lab_rooms.append(r)

            self.table.setRowCount(len(lab_rooms))
            for i, r in enumerate(lab_rooms):
                r_id = r[0]
                r_name = r[1]
                category = self.get_category(r_name)
                
                lab_set = settings.get(r_id, {'temizlik_tipi': 'NONE', 'sure_dk': 0, 'gun': '', 'baslangic': ''})
                t_type = lab_set['temizlik_tipi']
                mins = lab_set['sure_dk']
                gun = lab_set.get('gun') or ""
                baslangic = lab_set.get('baslangic') or ""

                item_id = QTableWidgetItem(str(r_id))
                item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 0, item_id)

                item_name = QTableWidgetItem(r_name)
                item_name.setFlags(item_name.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 1, item_name)

                item_cat = QTableWidgetItem(category)
                item_cat.setFlags(item_cat.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 2, item_cat)

                type_str = "Her Ders Sonrası" if t_type == "AFTER_LESSON" else ("Haftalık" if t_type == "WEEKLY" else "Yok (NONE)")
                item_type = QTableWidgetItem(type_str)
                item_type.setFlags(item_type.flags() & ~Qt.ItemIsEditable)
                
                if t_type == "AFTER_LESSON":
                    item_type.setForeground(QColor("#FFB300"))
                elif t_type == "WEEKLY":
                    item_type.setForeground(QColor("#00B0FF"))
                self.table.setItem(i, 3, item_type)

                item_min = QTableWidgetItem(str(mins))
                item_min.setFlags(item_min.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 4, item_min)
                
                item_gun = QTableWidgetItem(gun)
                item_gun.setFlags(item_gun.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 5, item_gun)
                
                item_saat = QTableWidgetItem(baslangic)
                item_saat.setFlags(item_saat.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(i, 6, item_saat)
                
            self.table.setSortingEnabled(True)
            self.on_type_changed(self.combo_type.currentIndex()) # set initial enabled states
            
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Veri yüklenirken hata: {e}")

    def on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        t_type_str = self.table.item(row, 3).text()
        mins_str = self.table.item(row, 4).text()
        gun_str = self.table.item(row, 5).text()
        saat_str = self.table.item(row, 6).text()

        if "Her Ders Sonrası" in t_type_str:
            self.combo_type.setCurrentIndex(1)
        elif "Haftalık" in t_type_str:
            self.combo_type.setCurrentIndex(2)
        else:
            self.combo_type.setCurrentIndex(0)
            
        self.spin_duration.setValue(int(mins_str) if mins_str.isdigit() else 30)
        
        if gun_str:
            idx = self.combo_day.findText(gun_str)
            if idx >= 0: self.combo_day.setCurrentIndex(idx)
            
        if saat_str:
            try:
                h, m = map(int, saat_str.split(':'))
                self.time_start.setTime(QTime(h, m))
            except:
                pass

    def on_type_changed(self, idx):
        if idx == 0:
            self.spin_duration.setValue(0)
            self.spin_duration.setEnabled(False)
            self.combo_day.setEnabled(False)
            self.time_start.setEnabled(False)
        elif idx == 1:
            if self.spin_duration.value() == 0:
                self.spin_duration.setValue(30)
            self.spin_duration.setEnabled(True)
            self.combo_day.setEnabled(False)
            self.time_start.setEnabled(False)
        else: # WEEKLY
            if self.spin_duration.value() == 0:
                self.spin_duration.setValue(60)
            self.spin_duration.setEnabled(True)
            self.combo_day.setEnabled(True)
            self.time_start.setEnabled(True)

    def save_selected(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir lab seçin.")
            return
            
        row = selected[0].row()
        lab_id = int(self.table.item(row, 0).text())
        
        idx = self.combo_type.currentIndex()
        if idx == 1:
            t_type = "AFTER_LESSON"
        elif idx == 2:
            t_type = "WEEKLY"
        else:
            t_type = "NONE"
            
        mins = self.spin_duration.value()
        gun = self.combo_day.currentText() if idx == 2 else ""
        baslangic = self.time_start.time().toString("HH:mm") if idx == 2 else ""
        
        if idx == 2 and not gun:
            QMessageBox.warning(self, "Hata", "Lütfen haftalık kural için bir gün seçin.")
            return
            
        if self.controller.model.set_lab_cleanup_settings(lab_id, t_type, mins, gun, baslangic):
            self.load_data()
            
    def apply_to_category(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Uyarı", "Lütfen örnek alnacak bir lab seçin.")
            return
            
        row = selected[0].row()
        target_cat = self.table.item(row, 2).text()
        
        idx = self.combo_type.currentIndex()
        if idx == 1: t_type = "AFTER_LESSON"
        elif idx == 2: t_type = "WEEKLY"
        else: t_type = "NONE"
            
        mins = self.spin_duration.value()
        gun = self.combo_day.currentText() if idx == 2 else ""
        baslangic = self.time_start.time().toString("HH:mm") if idx == 2 else ""
        
        if idx == 2 and not gun:
            QMessageBox.warning(self, "Hata", "Lütfen haftalık kural için bir gün seçin.")
            return
        
        reply = QMessageBox.question(self, "Onay", f"Seçili ayarlar tüm '{target_cat}' kategorisindeki lablara uygulansın mı?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success = True
            for i in range(self.table.rowCount()):
                if self.table.item(i, 2).text() == target_cat:
                    lab_id = int(self.table.item(i, 0).text())
                    if not self.controller.model.set_lab_cleanup_settings(lab_id, t_type, mins, gun, baslangic):
                        success = False
            
            if success:
                QMessageBox.information(self, "Başarılı", "Tüm kategoriye uygulandı.")
                self.load_data()
