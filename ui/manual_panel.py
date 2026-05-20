from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class ManualPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Manual Panel - Under Construction"))
