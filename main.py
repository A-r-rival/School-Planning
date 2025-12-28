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


def main():
    """
    Main entry point of the application
    """
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Ders Programı Oluşturucu")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Schedule Management")
    # app.setStyle("Fusion") # Fusion removed to force native Windows style
    
    try:
        # Create and show main application
        schedule_app = ScheduleApplication()
        sys.exit(schedule_app.run())
        
    except Exception as e:
        print(f"Uygulama başlatılırken hata oluştu: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()