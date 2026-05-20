from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)
        
        stats_layout = QHBoxLayout()
        
        self.lbl_processed = self._create_stat_card("Total Processed", "0")
        self.lbl_success = self._create_stat_card("Successful", "0")
        self.lbl_failed = self._create_stat_card("Failed", "0")
        self.lbl_skipped = self._create_stat_card("Skipped", "0")
        
        stats_layout.addWidget(self.lbl_processed)
        stats_layout.addWidget(self.lbl_success)
        stats_layout.addWidget(self.lbl_failed)
        stats_layout.addWidget(self.lbl_skipped)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
        
    def _create_stat_card(self, title: str, val: str):
        card = QWidget()
        card.setStyleSheet("background-color: palette(alternate-base); border-radius: 8px; padding: 10px;")
        lyt = QVBoxLayout(card)
        lbl_title = QLabel(title)
        lbl_val = QLabel(val)
        lbl_val.setStyleSheet("font-size: 20px; font-weight: bold;")
        lbl_val.setAlignment(Qt.AlignCenter)
        lyt.addWidget(lbl_title)
        lyt.addWidget(lbl_val)
        return card
