from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class ProgressCard(QFrame):
    def __init__(self, title: str, value: str = "0", color: str = "#0078D4", parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 8px;
                color: white;
            }}
        """)
        self.setMinimumSize(120, 80)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 12px; font-weight: bold; color: rgba(255, 255, 255, 0.8);")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        self.lbl_value.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_value)
        
    def set_value(self, value: str):
        self.lbl_value.setText(str(value))
