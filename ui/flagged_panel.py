from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QTableView, 
                               QHeaderView, QMessageBox, QAbstractItemView)
from PySide6.QtCore import Qt, Signal
from ui.widgets.flagged_model import FlaggedRecordsModel
from utils.log_exporter import LogExporter
from core.reprocessing import ReprocessingSystem
from logging_engine.logger import app_logger

class FlaggedPanel(QWidget):
    load_record_to_manual = Signal(dict)
    reprocess_triggered = Signal()

    def __init__(self):
        super().__init__()
        self.reprocessor = ReprocessingSystem()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Flagged & Invalid Records Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(title)
        
        # Search & Filter Layout
        lyt_controls = QHBoxLayout()
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by IAS No. or Name...")
        self.txt_search.textChanged.connect(self.filter_data)
        
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["All", "Missing Images", "Invalid Coordinates", "Validation Failures"])
        self.cmb_filter.currentTextChanged.connect(self.filter_data)
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_data)
        
        lyt_controls.addWidget(self.txt_search, 4)
        lyt_controls.addWidget(self.cmb_filter, 2)
        lyt_controls.addWidget(btn_refresh, 1)
        layout.addLayout(lyt_controls)
        
        # Table View
        self.table_view = QTableView()
        self.model = FlaggedRecordsModel()
        self.table_view.setModel(self.model)
        
        # Customizing table visual appearance
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table_view.horizontalHeader().resizeSection(0, 110)
        self.table_view.horizontalHeader().resizeSection(1, 160)
        
        layout.addWidget(self.table_view)
        
        # Bottom Actions Bar
        lyt_actions = QHBoxLayout()
        
        btn_fix = QPushButton("Fix Inline")
        btn_fix.clicked.connect(self.fix_inline)
        
        btn_scan = QPushButton("Auto-Scan Folders")
        btn_scan.setToolTip("Auto-detect added missing images from designate folder")
        btn_scan.clicked.connect(self.auto_scan_folders)
        
        btn_export = QPushButton("Export Excel Log")
        btn_export.clicked.connect(self.export_excel)
        
        btn_reprocess = QPushButton("Reprocess Flagged")
        btn_reprocess.setStyleSheet("background-color: #107C41; color: white;") # Green shade
        btn_reprocess.clicked.connect(self.reprocess_flagged)
        
        lyt_actions.addWidget(btn_fix)
        lyt_actions.addWidget(btn_scan)
        lyt_actions.addWidget(btn_export)
        lyt_actions.addStretch()
        lyt_actions.addWidget(btn_reprocess)
        
        layout.addLayout(lyt_actions)
        
    def refresh_data(self):
        self.model.refresh_data(self.txt_search.text(), self.cmb_filter.currentText())
        
    def filter_data(self):
        self.model.refresh_data(self.txt_search.text(), self.cmb_filter.currentText())
        
    def fix_inline(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            QMessageBox.warning(self, "No Selection", "Please select a flagged record to fix.")
            return
            
        row = indexes[0].row()
        record_dict = self.model.get_record(row)
        if record_dict:
            self.load_record_to_manual.emit(record_dict)
            
    def auto_scan_folders(self):
        # We can fetch the last selected images folder from session_state
        from core.recovery_manager import RecoveryManager
        rm = RecoveryManager()
        sess = rm.get_running_session()
        
        images_dir = ""
        if sess and sess.get("images_folder"):
            images_dir = sess["images_folder"]
        else:
            # Fallback check
            with db.connection() as conn:
                cur = conn.execute("SELECT images_folder FROM session_state ORDER BY started_at DESC LIMIT 1")
                row = cur.fetchone()
                if row: images_dir = row["images_folder"]
                
        if not images_dir or not os.path.exists(images_dir):
            QMessageBox.information(self, "Images Folder Missing", 
                                    "No active batch images folder found. Please select images folder or fix record in Manual Mode.")
            return
            
        count, names = self.reprocessor.auto_detect_corrections(images_dir)
        self.refresh_data()
        
        if count > 0:
            QMessageBox.information(self, "Scan Complete", 
                                    f"Successfully auto-corrected {count} records: {', '.join(names)}.\nThey have been reset to PENDING status.")
        else:
            QMessageBox.information(self, "Scan Complete", "No new image matches or corrections were detected in the images folder.")
            
    def export_excel(self):
        try:
            paths = LogExporter.export_all()
            QMessageBox.information(self, "Export Successful", 
                                    f"Flagged records spreadsheet generated at:\n{paths.get('flagged_xlsx')}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export error spreadsheet: {e}")
            
    def reprocess_flagged(self):
        count = self.reprocessor.reset_flagged_to_pending()
        self.refresh_data()
        if count > 0:
            QMessageBox.information(self, "Reprocessing Triggered", 
                                    f"{count} flagged records were reset to PENDING and are ready for batch processing.")
            self.reprocess_triggered.emit()
        else:
            QMessageBox.information(self, "Zero Records", "No flagged records are ready to be reprocessed.")
