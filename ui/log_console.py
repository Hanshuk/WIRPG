from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit
from logging_engine.logger import log_signals

class LogConsole(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
        
        log_signals.log_message.connect(self.append_log)
        
    def append_log(self, level, module, message):
        self.text_edit.appendPlainText(f"{level}: {message}")
