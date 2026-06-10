from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QHeaderView
from PySide6.QtCore import Qt

class DuplicateReportDialog(QDialog):
    """
    Displays a dummy-proof report of exact duplicate records found in the Excel file.
    """
    def __init__(self, duplicates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Records Found")
        self.resize(700, 400)
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("<b>Blocked — duplicate record(s) found!</b><br><br>"
                          "The following rows in your Excel file have identical information. "
                          "To prevent mistakes, these records have been blocked. Please fix them in your Excel file and try again.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #E81123; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Row Number", "Duplicate Field", "Identical Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self._populate(duplicates)
        
        btn_close = QPushButton("I understand, close this")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignCenter)

    def _populate(self, duplicates):
        self.table.setRowCount(len(duplicates))
        for i, dup in enumerate(duplicates):
            self.table.setItem(i, 0, QTableWidgetItem(str(dup.get("row", "Unknown"))))
            # The field might be technical internally, we can just show it if it's "ias_no" -> "IAS No"
            field = dup.get("field", "Unknown").replace("_", " ").title()
            self.table.setItem(i, 1, QTableWidgetItem(field))
            self.table.setItem(i, 2, QTableWidgetItem(str(dup.get("value", ""))))


class ImageDuplicateReportDialog(QDialog):
    """
    Displays a dummy-proof report of image duplicate records found during pre-flight.
    """
    def __init__(self, image_duplicates, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Photos Found")
        self.resize(700, 400)
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("<b>Blocked — photo already used!</b><br><br>"
                          "We found photos that are exactly the same or visually identical to photos already used for another beneficiary. "
                          "To prevent mistakes, these records have been blocked. Please replace the photos and try again.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #E81123; font-size: 14px;")
        layout.addWidget(lbl_info)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Beneficiary", "Photo Slot", "Reason"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)
        
        self._populate(image_duplicates)
        
        btn_close = QPushButton("I understand, close this")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignCenter)

    def _populate(self, image_duplicates):
        self.table.setRowCount(len(image_duplicates))
        for i, dup in enumerate(image_duplicates):
            self.table.setItem(i, 0, QTableWidgetItem(dup.get("ias_no", "Unknown")))
            self.table.setItem(i, 1, QTableWidgetItem(f"Slot {dup.get('slot', 'Unknown')}"))
            
            # Map technical reason to plain language
            reason = dup.get("reason", "")
            if "Exact image copy" in reason:
                plain_reason = "Exact duplicate photo"
            elif "Perceptual duplicate" in reason:
                plain_reason = "Visually identical photo"
            else:
                plain_reason = "Photo already used"
                
            self.table.setItem(i, 2, QTableWidgetItem(plain_reason))
