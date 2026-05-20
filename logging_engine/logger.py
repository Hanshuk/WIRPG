import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal
import queue
from config.constants import LOG_DIR
from db.database import db

class LogSignals(QObject):
    log_message = Signal(str, str, str) # level, module, message

class SQLiteHandler(logging.Handler):
    def emit(self, record):
        if record.levelno < logging.WARNING:
            return
        timestamp = datetime.fromtimestamp(record.created).isoformat()
        queue_id = getattr(record, 'queue_id', None)
        try:
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO logs (timestamp, level, module, queue_id, message) VALUES (?, ?, ?, ?, ?)",
                    (timestamp, record.levelname, record.module, queue_id, record.getMessage())
                )
                conn.commit()
        except Exception:
            pass

class UILogHandler(logging.Handler):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

    def emit(self, record):
        msg = self.format(record)
        self.signals.log_message.emit(record.levelname, record.module, msg)

log_signals = LogSignals()

def setup_logger():
    logger = logging.getLogger("CostplusIR")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s')

    # File Handler
    log_file = LOG_DIR / f"costplus_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=7
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # SQLite Handler
    sqlite_handler = SQLiteHandler()
    sqlite_handler.setLevel(logging.WARNING)
    
    # UI Handler
    ui_handler = UILogHandler(log_signals)
    ui_handler.setLevel(logging.DEBUG)
    ui_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(sqlite_handler)
    logger.addHandler(ui_handler)
    
    return logger

app_logger = setup_logger()
