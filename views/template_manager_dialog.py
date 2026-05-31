from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt

class TemplateManagerDialog(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Ortak Ders Grupları Şablon Yöneticisi")
        self.resize(500, 400)
        
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Save new template section
        save_layout = QHBoxLayout()
        self.txt_template_name = QLineEdit()
        self.txt_template_name.setPlaceholderText("Yeni şablon adı girin...")
        btn_save = QPushButton("Geçerli Gruplamayı Şablon Olarak Kaydet")
        btn_save.setStyleSheet("background-color: #4CAF50; color: white;")
        btn_save.clicked.connect(self._save_template)
        save_layout.addWidget(self.txt_template_name)
        save_layout.addWidget(btn_save)
        self.layout.addLayout(save_layout)
        
        self.layout.addWidget(QLabel("Kayıtlı Şablonlar:"))
        self.list_templates = QListWidget()
        self.layout.addWidget(self.list_templates)
        
        # Load / Delete section
        action_layout = QHBoxLayout()
        btn_load = QPushButton("Seçili Şablonu Yükle")
        btn_load.setStyleSheet("background-color: #2196F3; color: white;")
        btn_load.clicked.connect(self._load_template)
        
        btn_delete = QPushButton("Seçili Şablonu Sil")
        btn_delete.setStyleSheet("background-color: #F44336; color: white;")
        btn_delete.clicked.connect(self._delete_template)
        
        action_layout.addWidget(btn_load)
        action_layout.addWidget(btn_delete)
        self.layout.addLayout(action_layout)
        
        self._refresh_list()
        
    def _refresh_list(self):
        self.list_templates.clear()
        templates = self.model.get_group_templates()
        for t in templates:
            item_text = f"{t['ad']} - {t['tarih'][:16]}"
            if t['aciklama']:
                item_text += f" ({t['aciklama']})"
            self.list_templates.addItem(item_text)
            
            # Store ID in UserRole
            item = self.list_templates.item(self.list_templates.count() - 1)
            item.setData(Qt.UserRole, t['sablon_id'])
            
    def _save_template(self):
        name = self.txt_template_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Hata", "Şablon adı boş olamaz.")
            return
            
        success = self.model.save_group_template(name)
        if success:
            QMessageBox.information(self, "Başarılı", f"'{name}' başarıyla kaydedildi.")
            self.txt_template_name.clear()
            self._refresh_list()
        else:
            QMessageBox.warning(self, "Hata", "Şablon kaydedilirken bir hata oluştu (aynı isimde bir şablon olabilir).")
            
    def _load_template(self):
        item = self.list_templates.currentItem()
        if not item:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen yüklenecek bir şablon seçin.")
            return
            
        sablon_id = item.data(Qt.UserRole)
        
        # Confirm
        reply = QMessageBox.question(self, "Onay", "Geçerli tüm ortak ders gruplamaları silinip şablondaki gruplar yüklenecek. Onaylıyor musunuz?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success = self.model.load_group_template(sablon_id)
            if success:
                QMessageBox.information(self, "Başarılı", "Şablon başarıyla yüklendi.")
                self.accept()
                
    def _delete_template(self):
        item = self.list_templates.currentItem()
        if not item:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen silinecek bir şablon seçin.")
            return
            
        sablon_id = item.data(Qt.UserRole)
        
        reply = QMessageBox.question(self, "Onay", "Seçili şablonu silmek istediğinize emin misiniz?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success = self.model.delete_group_template(sablon_id)
            if success:
                self._refresh_list()
