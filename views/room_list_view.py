from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QPushButton, QHBoxLayout, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal

class RoomListView(QWidget):
    """
    Classroom management view
    """
    # Signals
    room_calendar_requested = pyqtSignal(int) # Emits room_id
    room_master_requested = pyqtSignal()      # Emits when master room view requested

    def __init__(self, model):
        super().__init__()
        self.model = model
        self.setWindowTitle("Derslik Yönetimi")
        self.resize(1000, 600)
        
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header layout with Add Button and Shortcut
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("+ Yeni Derslik Ekle")
        self.add_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        self.add_btn.clicked.connect(self.add_room_clicked)
        top_layout.addWidget(self.add_btn)
        
        self.master_btn = QPushButton("📅 Genel Oda Takvimi")
        self.master_btn.setStyleSheet("background-color: #3F51B5; color: white; padding: 8px; font-weight: bold;")
        self.master_btn.clicked.connect(self.room_master_requested.emit)
        top_layout.addWidget(self.master_btn)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filtrele:"))
        
        self.cb_lab = QCheckBox("Laboratuvar")
        self.cb_amfi = QCheckBox("Amfi")
        self.cb_derslik = QCheckBox("Derslik")
        
        # Checked by default
        self.cb_lab.setChecked(True)
        self.cb_amfi.setChecked(True)
        self.cb_derslik.setChecked(True)
        
        # Connect signals
        self.cb_lab.stateChanged.connect(self.load_data)
        self.cb_amfi.stateChanged.connect(self.load_data)
        self.cb_derslik.stateChanged.connect(self.load_data)
        
        filter_layout.addWidget(self.cb_lab)
        filter_layout.addWidget(self.cb_amfi)
        filter_layout.addWidget(self.cb_derslik)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7) # Added column for Notes + Actions
        self.table.setHorizontalHeaderLabels(["ID", "Derslik Adı", "Tip", "Kapasite", "Kat", "Notlar", "İşlemler"])
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50) # ID column semi-small
        
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Name stretches
        
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 130) # Room type + 20px
        
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.table.setColumnWidth(3, 70) # Capacity half
        
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 40) # Floor quarter

        header.setSectionResizeMode(5, QHeaderView.Stretch) # Notes stretch
        
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 150) # Actions fixed
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)

    def load_data(self):
        all_rooms = self.model.aktif_derslikleri_getir()
        
        # Apply Filters
        filtered_rooms = []
        for r_data in all_rooms:
            r_type = str(r_data[2]).lower()
            
            show = False
            if self.cb_lab.isChecked() and ("lab" in r_type or "laboratuvar" in r_type):
                show = True
            elif self.cb_amfi.isChecked() and "amfi" in r_type:
                show = True
            elif self.cb_derslik.isChecked() and "derslik" in r_type:
                show = True
                
            if show:
                filtered_rooms.append(r_data)

        self.table.setRowCount(len(filtered_rooms))
        
        for row_idx, room_data in enumerate(filtered_rooms):
            r_id = room_data[0]
            name = room_data[1]
            r_type = room_data[2]
            cap = room_data[3]
            floor = room_data[4] if len(room_data) > 4 else "N/A"
            notes = room_data[5] if len(room_data) > 5 else ""
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(name)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(r_type)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(cap)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(floor)))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(notes)))

            # Actions Column
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(5)

            edit_btn = QPushButton("Düzenle")
            edit_btn.setStyleSheet("padding: 2px;")
            edit_btn.clicked.connect(lambda checked, rid=r_id: self.edit_room_clicked(rid))
            
            cal_btn = QPushButton("Takvim")
            cal_btn.setStyleSheet("padding: 2px; background-color: #673AB7; color: white;")
            cal_btn.clicked.connect(lambda checked, rid=r_id: self.room_calendar_requested.emit(rid))

            del_btn = QPushButton("Sil")
            del_btn.setStyleSheet("padding: 2px; color: red;")
            del_btn.clicked.connect(lambda checked, rid=r_id: self.delete_room_clicked(rid))

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(cal_btn)
            actions_layout.addWidget(del_btn)
            self.table.setCellWidget(row_idx, 6, actions_widget)

    def add_room_clicked(self):
        from views.room_dialog import RoomDialog
        dialog = RoomDialog(self)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.model.derslik_ekle(
                    data["derslik_adi"],
                    data["derslik_tipi"],
                    data["kapasite"],
                    data["floor"],
                    notlar=data["notlar"]
                )
                self.load_data()
                QMessageBox.information(self, "Başarılı", "Derslik başarıyla eklendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Derslik eklenirken hata: {str(e)}")

    def edit_room_clicked(self, room_id):
        from views.room_dialog import RoomDialog
        # Get current data
        room_data = self.model.get_derslik_by_id(room_id)
        if not room_data:
            QMessageBox.warning(self, "Hata", "Derslik verisi bulunamadı!")
            return

        dialog = RoomDialog(self, room_data)
        if dialog.exec_():
            data = dialog.get_data()
            try:
                self.model.derslik_guncelle(room_id, data)
                self.load_data()
                QMessageBox.information(self, "Başarılı", "Derslik başarıyla güncellendi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Derslik güncellenirken hata: {str(e)}")

    def delete_room_clicked(self, room_id):
        reply = QMessageBox.question(
            self, "Derslik Sil", 
            "Bu dersliği silmek istediğinize emin misiniz?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.model.derslik_sil(room_id)
                self.load_data()
                QMessageBox.information(self, "Başarılı", "Derslik silindi.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Derslik silinirken hata: {str(e)}")
