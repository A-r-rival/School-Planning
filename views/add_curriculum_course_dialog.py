# -*- coding: utf-8 -*-
"""
Add Curriculum Course Dialog
Dialog for adding new courses to the curriculum (Template).
Populates 'Dersler' and 'Ders_Sinif_Iliskisi' tables.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, 
    QComboBox, QSpinBox, QLabel, QPushButton, QMessageBox,
    QFormLayout, QGroupBox, QRadioButton
)
from PyQt5.QtCore import Qt

class AddCurriculumCourseDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Müfredata Yeni Ders Ekle (Template)")
        self.setGeometry(300, 300, 500, 450)
        self._setup_ui()
        self._load_departments()

    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # --- Type Selection (Class vs Pool) ---
        type_group = QGroupBox("Ders Türü")
        type_layout = QHBoxLayout()
        
        self.radio_class = QRadioButton("Sınıfa Zorunlu Ekle")
        self.radio_class.setChecked(True)
        self.radio_class.toggled.connect(self._on_type_changed)
        
        self.radio_pool = QRadioButton("Havuza Ekle")
        self.radio_pool.toggled.connect(self._on_type_changed)
        
        type_layout.addWidget(self.radio_class)
        type_layout.addWidget(self.radio_pool)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        form_layout = QFormLayout()
        
        # Course Name
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Örn: İleri İngilizce")
        form_layout.addRow("Ders Adı:", self.name_input)
        
        # Course Code
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Örn: ENG301")
        form_layout.addRow("Ders Kodu:", self.code_input)
        
        # Department
        self.dept_combo = QComboBox()
        self.dept_combo.setEditable(False) # Strict selection
        form_layout.addRow("Bölüm:", self.dept_combo)
        
        # Pool Code (Hidden by default)
        self.pool_code_input = QLineEdit()
        self.pool_code_input.setPlaceholderText("Örn: MÜH (Mühendislik Seçmeli)")
        self.lbl_pool = QLabel("Havuz Kodu:")
        form_layout.addRow(self.lbl_pool, self.pool_code_input)
        
        # Class Year
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1, 4)
        self.lbl_year = QLabel("Sınıf Düzeyi:")
        form_layout.addRow(self.lbl_year, self.year_spin)
        
        # Hours Group
        hours_group = QGroupBox("Ders Saatleri")
        hours_layout = QHBoxLayout()
        
        # T
        hours_layout.addWidget(QLabel("Teori:"))
        self.t_spin = QSpinBox()
        self.t_spin.setRange(0, 10)
        self.t_spin.setValue(3)
        hours_layout.addWidget(self.t_spin)
        
        # U
        hours_layout.addWidget(QLabel("Uygulama:"))
        self.u_spin = QSpinBox()
        self.u_spin.setRange(0, 10)
        hours_layout.addWidget(self.u_spin)
        
        # L
        hours_layout.addWidget(QLabel("Lab:"))
        self.l_spin = QSpinBox()
        self.l_spin.setRange(0, 10)
        hours_layout.addWidget(self.l_spin)
        
        hours_group.setLayout(hours_layout)
        layout.addLayout(form_layout)
        layout.addWidget(hours_group)
        
        # AKTS
        akts_layout = QHBoxLayout()
        akts_layout.addWidget(QLabel("AKTS:"))
        self.akts_spin = QSpinBox()
        self.akts_spin.setRange(0, 30)
        self.akts_spin.setValue(5)
        akts_layout.addWidget(self.akts_spin)
        akts_layout.addStretch()
        layout.addLayout(akts_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Kaydet ve Ekle")
        save_btn.clicked.connect(self._save)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        # Initial state update
        self._on_type_changed()

    def _on_type_changed(self):
        is_pool = self.radio_pool.isChecked()
        
        # Toggle Pool Input
        self.pool_code_input.setVisible(is_pool)
        self.lbl_pool.setVisible(is_pool)
        
        # Toggle Year (Optional: Pools might not strictly need year, but technically schema might link them?)
        # For now, let's keep year visible as "Target Year" or similar, or just keep it enabled.
        # User requirement implies choice between "Sınıfa Zorunlu" vs "Havuza".
        # If "Havuza", maybe we don't force a specific class year?
        # But `Ders_Havuz_Iliskisi` doesn't have `sinif_duzeyi`.
        # `Ders_Sinif_Iliskisi` has `donem_sinif_num`.
        
        self.year_spin.setEnabled(not is_pool)
        if is_pool:
            self.year_spin.setSpecialValueText("Genel")
            self.year_spin.setValue(0) # Or hidden
        else:
            self.year_spin.setSpecialValueText("")
            self.year_spin.setValue(1)

    def _load_departments(self):
        try:
            # We need to access model to get departments.
            # Assuming controller has access to model
            faculties = self.controller.model.get_faculties()
            for fac_id, fac_name in faculties:
                depts = self.controller.model.get_departments_by_faculty(fac_id)
                for dept_id, dept_name in depts:
                     self.dept_combo.addItem(f"{dept_name} ({fac_name})", dept_id)
        except Exception as e:
            print(f"Error loading depts: {e}")

    def _save(self):
        name = self.name_input.text().strip()
        code = self.code_input.text().strip()
        is_pool = self.radio_pool.isChecked()
        pool_code = self.pool_code_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Hata", "Ders adı boş olamaz!")
            return
            
        if is_pool and not pool_code:
            QMessageBox.warning(self, "Hata", "Havuz Kodu girilmelidir!")
            return
            
        data = {
            'name': name,
            'code': code if code else name[:3].upper(),
            'dept_id': self.dept_combo.currentData(),
            'year': self.year_spin.value() if not is_pool else None,
            't': self.t_spin.value(),
            'u': self.u_spin.value(),
            'l': self.l_spin.value(),
            'akts': self.akts_spin.value(),
            'is_pool': is_pool,
            'pool_code': pool_code
        }
        
        success = self.controller.add_curriculum_course_as_template(data)
        if success:
            QMessageBox.information(self, "Başarılı", "Ders müfredata eklendi.\nOtomatik programlamaya hazırdır.")
            self.accept()
