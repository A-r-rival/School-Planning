# -*- coding: utf-8 -*-
"""
Main Application Entry Point - MVC Pattern
University Schedule Management Application
"""
import sys
import os

# Import ORTools first to avoid conflict with PyQt5 (protobuf versions)
try:
    from ortools.sat.python import cp_model
except ImportError:
    pass

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import MVC components
from models.schedule_model import ScheduleModel
from views.schedule_view import ScheduleView
from controllers.schedule_controller import ScheduleController


class ScheduleApplication(QObject):
    """
    Main application class that coordinates MVC components
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize MVC components
        self.model = ScheduleModel()
        self.view = ScheduleView()
        self.controller = ScheduleController(self.model, self.view)
        
        # Connect application close event
        self.view.closeEvent = self.close_application
    
    def show(self):
        """Show the main window"""
        self.view.show()
    
    def close_application(self, event):
        """Handle application close event"""
        try:
            # Controller handles cleanup
            print("Uygulama kapatılıyor...")
            self.controller.close_application()
            event.accept()
        except Exception as e:
            print(f"Uygulama kapatılırken hata oluştu: {str(e)}")
            event.accept()

    def run(self):
        """Run the application event loop."""
        self.show()
        return QApplication.instance().exec_()


def set_dark_theme(app):
    from PyQt5.QtGui import QPalette, QColor
    from PyQt5.QtCore import Qt
    
    app.setStyle("Fusion")
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(10, 10, 10))
    dark_palette.setColor(QPalette.AlternateBase, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)
    
    app.setPalette(dark_palette)
    
    app.setStyleSheet("""
        QToolTip { 
            background-color: #2a82da; 
            color: #ffffff; 
            border: 1px solid white; 
            padding: 5px;
            font-size: 13px;
        }

        QPushButton {
            background-color: #444;
            color: white;
            border: 1px solid #555;
            padding: 5px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #555;
        }
        QLineEdit {
            background-color: #353535;
            color: white;
            border: 1px solid #555;
            padding: 3px;
        }
        QTableWidget {
            background-color: #303030;
            color: white;
            gridline-color: #555;
        }
        QHeaderView::section {
            background-color: #404040;
            color: white;
            border: 1px solid #555;
            padding: 4px;
        }
        QListWidget {
            background-color: #303030;
            color: white;
        }
    """)

def set_light_theme(app):
    from PyQt5.QtGui import QPalette, QColor
    from PyQt5.QtCore import Qt
    app.setStyle("Fusion")
    
    light_palette = QPalette()
    light_palette.setColor(QPalette.Window, QColor(240, 240, 240))
    light_palette.setColor(QPalette.WindowText, Qt.black)
    light_palette.setColor(QPalette.Base, QColor(255, 255, 255))
    light_palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    light_palette.setColor(QPalette.ToolTipBase, Qt.white)
    light_palette.setColor(QPalette.ToolTipText, Qt.black)
    light_palette.setColor(QPalette.Text, Qt.black)
    light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
    light_palette.setColor(QPalette.ButtonText, Qt.black)
    light_palette.setColor(QPalette.BrightText, Qt.red)
    light_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    light_palette.setColor(QPalette.HighlightedText, Qt.white)
    
    app.setPalette(light_palette)
    
    # Clean, lightweight native styling
    app.setStyleSheet("""
        QToolTip { 
            background-color: #444444; 
            color: #ffffff; 
            border: 1px solid #777777; 
            padding: 5px;
            font-size: 13px;
        }
        QTableWidget {
            background-color: #ffffff;
            alternate-background-color: #f5f5f5;
            gridline-color: #e0e0e0;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            padding: 4px;
            border: 1px solid #d0d0d0;
            font-weight: bold;
        }
        QTableWidget::item:selected {
            background-color: #e3f2fd;
            color: #000000;
        }
    """)

def main():
    """
    Main entry point of the application
    """
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Ders Programı Oluşturucu")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Schedule Management")
    set_light_theme(app)
    
    try:
        # Create and show main application
        schedule_app = ScheduleApplication()
        sys.exit(schedule_app.run())
        
    except Exception as e:
        print(f"Uygulama başlatılırken hata oluştu: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()