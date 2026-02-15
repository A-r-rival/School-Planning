from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLabel, QPushButton, QHBoxLayout)
from PyQt5.QtCore import Qt

class RoomListView(QWidget):
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.init_ui()

        self.setWindowTitle("Derslik Listesi")
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("Derslik Listesi")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        header_layout.addWidget(title)
        
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.load_data)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Derslik Adı", "Tip", "Kapasite", "Kat"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        # Initial Load
        self.load_data()

    def load_data(self):
        rooms = self.model.aktif_derslikleri_getir()
        self.table.setRowCount(len(rooms))
        
        for row_idx, room_data in enumerate(rooms):
            # room_data expected: (id, name, type, capacity, floor)
            # If floor is missing in DB return, it might be 4 items. Model handles this now?
            # Let's handle it safely.
            
            r_id = room_data[0]
            name = room_data[1]
            r_type = room_data[2]
            cap = room_data[3]
            floor = room_data[4] if len(room_data) > 4 else "N/A"
            
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(r_id)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(name)))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(r_type)))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(cap)))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(floor)))
