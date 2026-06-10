import logging
from datetime import datetime
from PySide6.QtCore import QObject, Signal
from db.database import db

class QtLogSignalSignals(QObject):
    log_emitted = Signal(str, str, str) # level, module, message

class QtSignalLogHandler(logging.Handler):
    """
    Routes standard logging to a Qt Signal so the UI (LogConsole) can display logs live.
    """
    def __init__(self):
        super().__init__()
        self.signals = QtLogSignalSignals()

    def emit(self, record):
        try:
            msg = self.format(record)
            self.signals.log_emitted.emit(record.levelname, record.name, msg)
        except Exception:
            self.handleError(record)

class SQLiteLogHandler(logging.Handler):
    """
    Routes standard logging directly into the SQLite `logs` table for persistence.
    """
    def emit(self, record):
        try:
            msg = self.format(record)
            now = datetime.now().isoformat()
            
            # Queue ID can be extracted if passed via extra, otherwise null
            q_id = getattr(record, 'queue_id', None)
            
            with db.connection() as conn:
                conn.execute(
                    "INSERT INTO logs (timestamp, level, module, queue_id, message) VALUES (?, ?, ?, ?, ?)",
                    (now, record.levelname, record.name, q_id, msg)
                )
                conn.commit()
        except Exception:
            self.handleError(record)

def setup_handlers(logger: logging.Logger):
    """
    Attach these custom handlers to the logger.
    """
    formatter = logging.Formatter('%(message)s')
    
    qt_handler = QtSignalLogHandler()
    qt_handler.setFormatter(formatter)
    
    sqlite_handler = SQLiteLogHandler()
    sqlite_handler.setFormatter(formatter)
    
    logger.addHandler(qt_handler)
    logger.addHandler(sqlite_handler)
    
    return qt_handler
