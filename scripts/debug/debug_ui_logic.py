
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel

class DebugView(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        
        self.combo = QComboBox()
        self.layout.addWidget(self.combo)
        
        self.label = QLabel("Status: Ready")
        self.layout.addWidget(self.label)
        
        self.combo.currentIndexChanged.connect(self.on_changed)
        
        self.populate()
        
        self.setLayout(self.layout)
        
    def populate(self):
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem("Select...", None)
        self.combo.addItem("Item 1", 101)
        self.combo.addItem("Item 2", 102)
        self.combo.blockSignals(False)
        print("Populated.")
        
    def on_changed(self):
        print("Signal received.")
        data = self.combo.currentData()
        print(f"Data: {data} (Type: {type(data)})")
        self.label.setText(f"Selected: {data}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DebugView()
    window.show()
    
    # Simulate selection
    print("Simulating selection of index 1...")
    window.combo.setCurrentIndex(1)
    
    print("Simulating selection of index 2...")
    window.combo.setCurrentIndex(2)
    
    # sys.exit(app.exec_())
