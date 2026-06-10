from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLabel, QStackedWidget
from PySide6.QtCore import Qt
# We will assume a global qt_log_handler was created in main.py, or we can just import it.
# Actually, the user asked to replace technical jargon, but logs are naturally technical.
# "Log console when empty: 'Logs will appear here once a batch is running'"

class LogConsole(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.stack = QStackedWidget()
        
        # Empty State
        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        lbl_empty = QLabel("Logs will appear here once a batch is running")
        lbl_empty.setAlignment(Qt.AlignCenter)
        lbl_empty.setStyleSheet("color: #888888; font-size: 18px; font-weight: bold;")
        empty_layout.addWidget(lbl_empty)
        
        # Log Text Edit
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setToolTip("Shows system logs for troubleshooting.")
        
        self.stack.addWidget(self.empty_widget)
        self.stack.addWidget(self.text_edit)
        
        layout.addWidget(self.stack)
        self.is_empty = True
        
    def append_log(self, level, module, message):
        if self.is_empty:
            self.stack.setCurrentWidget(self.text_edit)
            self.is_empty = False
        
        # Dummy proof
        if "WORKER_TIMEOUT" in message:
            message = "This entry took too long and was skipped"
        if "IMAGE_DUPLICATE_BLOCKED" in message:
            message = "Blocked — photo already used"
        if "DUPLICATE_BLOCKED" in message:
            message = "Blocked — duplicate record"
            
        self.text_edit.appendPlainText(f"[{level}] {message}")
