from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView, QLabel, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QAbstractTableModel, QTimer, Signal
from PySide6.QtGui import QColor

class QueueTableModel(QAbstractTableModel):
    def __init__(self, data=None):
        super().__init__()
        self._data = data or []
        self.headers = ["Beneficiary", "IAS No", "Status", "Attempt", "Details"]

    def data(self, index, role):
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.ForegroundRole, Qt.ToolTipRole):
            return None
        
        row = self._data[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0: return row.get("name", "")
            if col == 1: return row.get("ias_no", "")
            if col == 2:
                # Dummy-proof status
                s = row.get("status", "")
                if s == "PENDING": return "Waiting in list"
                if s == "PROCESSING": return "Working on it..."
                if s == "COMPLETED": return "Done"
                if s == "FAILED": return "Failed"
                return s
            if col == 3: return str(row.get("retry_count", 0))
            if col == 4:
                err = row.get("error_message", "")
                if "WORKER_TIMEOUT" in err: return "This entry took too long and was skipped"
                if "IMAGE_DUPLICATE_BLOCKED" in err: return "Blocked — photo already used"
                if "DUPLICATE_BLOCKED" in err: return "Blocked — duplicate record"
                return err
                
        elif role == Qt.ForegroundRole:
            if col == 2:
                s = row.get("status", "")
                if s == "COMPLETED": return QColor("#107C10")
                if s == "FAILED": return QColor("#E81123")
                if s == "PROCESSING": return QColor("#0078D4")
                return QColor("#888888")
                
        elif role == Qt.ToolTipRole:
            return "This row shows the current progress of a specific beneficiary."
                
        return None

    def rowCount(self, index=None):
        return len(self._data)

    def columnCount(self, index=None):
        return len(self.headers)

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None

    def update_data(self, new_data):
        self.beginResetModel()
        self._data = new_data
        self.endResetModel()

class QueueMonitor(QWidget):
    def __init__(self, queue_manager, parent=None):
        super().__init__(parent)
        self.queue_manager = queue_manager
        
        layout = QVBoxLayout(self)
        
        h_header = QHBoxLayout()
        lbl_title = QLabel("Processing List")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        lbl_title.setToolTip("Shows all records currently being turned into PDFs.")
        h_header.addWidget(lbl_title)
        
        self.btn_clear = QPushButton("Clear Completed")
        self.btn_clear.setToolTip("Removes finished items from this list. Does not delete PDFs.")
        self.btn_clear.clicked.connect(self._clear_completed)
        h_header.addWidget(self.btn_clear)
        h_header.addStretch()
        
        layout.addLayout(h_header)
        
        self.table = QTableView()
        self.table.setToolTip("The list of all records waiting to be processed.")
        self.model = QueueTableModel()
        self.table.setModel(self.model)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.table)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_data)
        self.timer.start(2000)
        
    def _refresh_data(self):
        # Fetch queue data from queue_manager
        # Assuming queue_manager has a method get_all()
        if hasattr(self.queue_manager, "get_all"):
            data = self.queue_manager.get_all()
            self.model.update_data(data)
            
    def _clear_completed(self):
        # The prompt says to show a confirmation dialog
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, 
            "Clear completed?", 
            "This will remove all completed records from the list. The generated PDFs will not be deleted. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if hasattr(self.queue_manager, "clear_completed"):
                self.queue_manager.clear_completed()
                self._refresh_data()
