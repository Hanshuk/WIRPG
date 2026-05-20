from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from ui.theme_manager import ThemeManager

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)
        
        btn_dark = QPushButton("Dark Theme")
        btn_dark.clicked.connect(lambda: ThemeManager.apply_theme("dark"))
        btn_light = QPushButton("Light Theme")
        btn_light.clicked.connect(lambda: ThemeManager.apply_theme("light"))
        
        layout.addWidget(btn_dark)
        layout.addWidget(btn_light)
