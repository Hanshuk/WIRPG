from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton
from PySide6.QtCore import Signal, Qt

class SearchPanel(QWidget):
    search_triggered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by name or number...")
        self.txt_search.setToolTip("Type a name or number here to find specific records.")
        
        self.btn_search = QPushButton("Search")
        self.btn_search.setToolTip("Click to search for the typed text.")
        self.btn_search.clicked.connect(self._on_search)
        self.txt_search.returnPressed.connect(self._on_search)
        
        layout.addWidget(self.txt_search)
        layout.addWidget(self.btn_search)
        
    def _on_search(self):
        text = self.txt_search.text().strip()
        self.search_triggered.emit(text)
