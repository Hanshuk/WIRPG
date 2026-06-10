from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QPushButton, QTableView, 
                               QHeaderView, QMessageBox, QAbstractItemView, QStackedWidget)
from PySide6.QtCore import Qt, Signal
from ui.widgets.flagged_model import FlaggedRecordsModel
from utils.log_exporter import LogExporter
from core.reprocessing import ReprocessingSystem
from logging_engine.logger import app_logger
from db.database import db
import os

class FlaggedPanel(QWidget):
    load_record_to_manual = Signal(dict)
    reprocess_triggered = Signal()
    show_banner = Signal(str, str) # type ("success", "warning", "error"), message

    def __init__(self):
        super().__init__()
        self.reprocessor = ReprocessingSystem()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Flagged Records")
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
        title.setToolTip("Records that failed processing and need your attention.")
        layout.addWidget(title)
        
        # Search & Filter Layout
        lyt_controls = QHBoxLayout()
        
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Search by Name...")
        self.txt_search.setToolTip("Type a name to find specific flagged records.")
        self.txt_search.textChanged.connect(self.filter_data)
        
        self.cmb_filter = QComboBox()
        self.cmb_filter.addItems(["All", "Missing Images", "Invalid Coordinates", "Validation Failures"])
        self.cmb_filter.setToolTip("Filter the list by type of problem.")
        self.cmb_filter.currentTextChanged.connect(self.filter_data)
        
        btn_refresh = QPushButton("Refresh")
        btn_refresh.setToolTip("Click to update the list.")
        btn_refresh.clicked.connect(self.refresh_data)
        
        lyt_controls.addWidget(self.txt_search, 4)
        lyt_controls.addWidget(self.cmb_filter, 2)
        lyt_controls.addWidget(btn_refresh, 1)
        layout.addLayout(lyt_controls)
        
        self.stack = QStackedWidget()
        
        # Empty State
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        lbl_empty = QLabel("No issues found — all records are clean")
        lbl_empty.setAlignment(Qt.AlignCenter)
        lbl_empty.setStyleSheet("color: #888888; font-size: 18px; font-weight: bold;")
        empty_layout.addWidget(lbl_empty)
        
        # Table View
        self.table_view = QTableView()
        self.table_view.setToolTip("List of records that need to be fixed.")
        self.model = FlaggedRecordsModel()
        self.model.modelReset.connect(self._check_empty)
        self.table_view.setModel(self.model)
        
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table_view.horizontalHeader().resizeSection(0, 110)
        self.table_view.horizontalHeader().resizeSection(1, 160)
        
        self.stack.addWidget(self.empty_widget)
        self.stack.addWidget(self.table_view)
        layout.addWidget(self.stack)
        
        # Bottom Actions Bar
        lyt_actions = QHBoxLayout()
        
        btn_fix = QPushButton("Fix Inline")
        btn_fix.setToolTip("Fix the selected record manually.")
        btn_fix.clicked.connect(self.fix_inline)
        
        btn_scan = QPushButton("Auto-Scan Folders")
        btn_scan.setToolTip("Automatically detect if you added missing photos.")
        btn_scan.clicked.connect(self.auto_scan_folders)
        
        btn_export = QPushButton("Export Excel Log")
        btn_export.setToolTip("Save this list as an Excel file.")
        btn_export.clicked.connect(self.export_excel)
        
        btn_reprocess = QPushButton("Reprocess Flagged")
        btn_reprocess.setStyleSheet("background-color: #107C41; color: white;")
        btn_reprocess.setToolTip("Try to process the flagged records again.")
        btn_reprocess.clicked.connect(self.reprocess_flagged)
        
        lyt_actions.addWidget(btn_fix)
        lyt_actions.addWidget(btn_scan)
        lyt_actions.addWidget(btn_export)
        lyt_actions.addStretch()
        lyt_actions.addWidget(btn_reprocess)
        
        layout.addLayout(lyt_actions)
        self._check_empty()
        
    def _check_empty(self):
        if self.model.rowCount() == 0:
            self.stack.setCurrentWidget(self.empty_widget)
        else:
            self.stack.setCurrentWidget(self.table_view)

    def refresh_data(self):
        self.model.refresh_data(self.txt_search.text(), self.cmb_filter.currentText())
        
    def filter_data(self):
        self.model.refresh_data(self.txt_search.text(), self.cmb_filter.currentText())
        
    def fix_inline(self):
        indexes = self.table_view.selectionModel().selectedRows()
        if not indexes:
            self.show_banner.emit("warning", "Please select a record to fix.")
            return
            
        row = indexes[0].row()
        record_dict = self.model.get_record(row)
        if record_dict:
            self.load_record_to_manual.emit(record_dict)
            
    def auto_scan_folders(self):
        from core.recovery_manager import RecoveryManager
        rm = RecoveryManager()
        sess = rm.get_running_session()
        
        images_dir = ""
        if sess and sess.get("images_folder"):
            images_dir = sess["images_folder"]
        else:
            with db.connection() as conn:
                cur = conn.execute("SELECT images_folder FROM session_state ORDER BY started_at DESC LIMIT 1")
                row = cur.fetchone()
                if row: images_dir = row["images_folder"]
                
        if not images_dir or not os.path.exists(images_dir):
            self.show_banner.emit("warning", "No photos folder found. Select it in the Batch panel first.")
            return
            
        count, names = self.reprocessor.auto_detect_corrections(images_dir)
        self.refresh_data()
        
        if count > 0:
            self.show_banner.emit("success", f"Successfully auto-corrected {count} records. They are ready to process.")
        else:
            self.show_banner.emit("warning", "No new photo matches were detected.")
            
    def export_excel(self):
        try:
            paths = LogExporter.export_all()
            self.show_banner.emit("success", f"List saved to: {paths.get('flagged_xlsx')}")
        except Exception as e:
            self.show_banner.emit("error", f"Failed to save spreadsheet: {e}")
            
    def reprocess_flagged(self):
        count = self.reprocessor.reset_flagged_to_pending()
        self.refresh_data()
        if count > 0:
            self.show_banner.emit("success", f"{count} records are ready to be processed again.")
            self.reprocess_triggered.emit()
        else:
            self.show_banner.emit("warning", "No flagged records are ready to be reprocessed.")
