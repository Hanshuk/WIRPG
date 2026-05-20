from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Preview Panel - Under Construction"))
