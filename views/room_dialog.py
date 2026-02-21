# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QComboBox, QSpinBox, QDialogButtonBox, QMessageBox)

class RoomDialog(QDialog):
    def __init__(self, parent=None, room_data=None):
        super().__init__(parent)
        self.room_data = room_data # If editing, this will contain room details
        
        self.init_ui()
        
        if self.room_data:
            self.setWindowTitle("Derslik Düzenle")
            self.load_data()
        else:
            self.setWindowTitle("Yeni Derslik Ekle")

    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Derslik", "Amfi", "Laboratuvar"])
        
        self.cap_spin = QSpinBox()
        self.cap_spin.setRange(1, 1000)
        self.cap_spin.setValue(40)
        
        self.floor_spin = QSpinBox()
        self.floor_spin.setRange(-2, 10)
        self.floor_spin.setValue(0)
        
        self.notlar_edit = QLineEdit()
        self.notlar_edit.setPlaceholderText("Ek özellikler, notlar...")
        
        form_layout.addRow("Derslik Adı:", self.name_edit)
        form_layout.addRow("Derslik Tipi:", self.type_combo)
        form_layout.addRow("Kapasite:", self.cap_spin)
        form_layout.addRow("Kat:", self.floor_spin)
        form_layout.addRow("Notlar:", self.notlar_edit)
        
        layout.addLayout(form_layout)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        self.setLayout(layout)

    def load_data(self):
        # room_data: (id, name, type, cap, floor)
        self.name_edit.setText(str(self.room_data[1]))
        
        # Set type
        curr_type = str(self.room_data[2])
        idx = self.type_combo.findText(curr_type)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)
        else:
            # Maybe it's "Lab" instead of "Laboratuvar" in DB
            if "lab" in curr_type.lower():
                self.type_combo.setCurrentIndex(2)
        
        self.cap_spin.setValue(int(self.room_data[3]))
        self.floor_spin.setValue(int(self.room_data[4]))
        self.notlar_edit.setText(str(self.room_data[5]) if len(self.room_data) > 5 and self.room_data[5] else "")

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Hata", "Derslik adı boş olamaz!")
            return
        self.accept()

    def get_data(self):
        return {
            "derslik_adi": self.name_edit.text().strip(),
            "derslik_tipi": self.type_combo.currentText(),
            "kapasite": self.cap_spin.value(),
            "floor": self.floor_spin.value(),
            "notlar": self.notlar_edit.text().strip()
        }
