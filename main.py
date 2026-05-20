import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CostPlus SolarDocs")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Cost Plus Inc.")
    
    from db.migrations import run_migrations
    run_migrations()
    
    from logging_engine.logger import setup_logger
    setup_logger()
    
    from core.recovery_manager import RecoveryManager
    rm = RecoveryManager()
    interrupted = rm.get_running_session()
    
    from ui.main_window import MainWindow
    window = MainWindow()
    window.show()
    
    from ui.theme_manager import ThemeManager
    ThemeManager.apply_theme()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
