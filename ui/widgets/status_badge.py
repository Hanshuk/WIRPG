from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class StatusBadge(QLabel):
    def __init__(self, text: str, color: str = "#888888", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
        self.setFixedHeight(20)

    def set_status(self, text: str, color: str):
        self.setText(text)
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 10px;
                padding: 2px 8px;
                font-weight: bold;
                font-size: 11px;
            }}
        """)
