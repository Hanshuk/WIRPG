from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from db.models import ErrorCode

class PreFlightReportDialog(QDialog):
    def __init__(self, excel_dups, image_dups, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pre-flight Check: Conflicts Found")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QDialog {
                background-color: palette(window);
            }
            QLabel {
                font-size: 14px;
            }
            QTableWidget {
                background-color: palette(base);
                border: 1px solid #333333;
                border-radius: 4px;
            }
            QPushButton {
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton#btn_continue {
                background-color: #D83B01;
                color: white;
            }
            QPushButton#btn_cancel {
                background-color: #333333;
                color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("We found some conflicts in your batch.")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #E81123;")
        layout.addWidget(title)

        desc = QLabel("The following records contain duplicate data or reused photos. They will be pushed to the Flagged Records list and skipped for now.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Conflict Type", "Details"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.populate_table(excel_dups, image_dups)

        h_btn = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel Batch")
        self.btn_cancel.setObjectName("btn_cancel")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_continue = QPushButton("Continue & Skip These")
        self.btn_continue.setObjectName("btn_continue")
        self.btn_continue.clicked.connect(self.accept)
        
        h_btn.addStretch()
        h_btn.addWidget(self.btn_cancel)
        h_btn.addWidget(self.btn_continue)
        
        layout.addLayout(h_btn)

    def populate_table(self, excel_dups, image_dups):
        self.table.setRowCount(len(excel_dups) + len(image_dups))
        row = 0
        
        for r in excel_dups:
            self.table.setItem(row, 0, QTableWidgetItem(r.name))
            self.table.setItem(row, 1, QTableWidgetItem("Data Duplicate"))
            errs = [e.message for e in r.validation_errors if e.code == ErrorCode.EXCEL_DUPLICATE]
            self.table.setItem(row, 2, QTableWidgetItem(errs[0] if errs else "Duplicate values found"))
            row += 1
            
        for r in image_dups:
            self.table.setItem(row, 0, QTableWidgetItem(r.name))
            self.table.setItem(row, 1, QTableWidgetItem("Photo Reused"))
            errs = [e.message for e in r.validation_errors if e.code == ErrorCode.IMAGE_DUPLICATE]
            self.table.setItem(row, 2, QTableWidgetItem(errs[0] if errs else "Reused photo detected"))
            row += 1
