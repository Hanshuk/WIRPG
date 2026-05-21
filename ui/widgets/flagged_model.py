from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from db.database import db

class FlaggedRecordsModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.headers = [
            "IAS No.", "Beneficiary Name", "Error Type", 
            "Missing Fields", "Missing Images", "Suggested Fix", 
            "Timestamp", "Retry Count", "Status"
        ]
        self.records = []
        self.refresh_data()

    def rowCount(self, parent=QModelIndex()):
        return len(self.records)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
            
        record = self.records[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0: return record.get("ias_no", "N/A")
            elif col == 1: return record.get("name", "N/A")
            elif col == 2: return record.get("error_type", "N/A")
            elif col == 3: return record.get("missing_fields") or "None"
            elif col == 4: return record.get("missing_images") or "None"
            elif col == 5: return record.get("suggested_fix") or "N/A"
            elif col == 6: return record.get("timestamp") or "N/A"
            elif col == 7: return str(record.get("retry_count", 0))
            elif col == 8: return record.get("status", "N/A")
            
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter | (Qt.AlignLeft if col in [0, 1, 3, 4, 5] else Qt.AlignCenter)
            
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if 0 <= section < len(self.headers):
                return self.headers[section]
        return None

    def refresh_data(self, search_query: str = "", filter_type: str = "All"):
        self.beginResetModel()
        with db.connection() as conn:
            query = """
                SELECT queue_id, ias_no, name, error_type, missing_fields, missing_images, 
                       suggested_fix, timestamp, retry_count, status
                FROM processing_queue
                WHERE (status = 'FLAGGED' OR error_type IS NOT NULL AND error_type != '')
            """
            params = []
            
            if filter_type == "Missing Images":
                query += " AND (error_type = 'MISSING_IMAGES' OR missing_images IS NOT NULL AND missing_images != '')"
            elif filter_type == "Invalid Coordinates":
                query += " AND (error_type = 'INVALID_COORDINATES' OR missing_fields LIKE '%coordinate%')"
            elif filter_type == "Validation Failures":
                query += " AND (status = 'FLAGGED' AND error_type = 'VALIDATION_FAILURE')"
                
            if search_query:
                query += " AND (ias_no LIKE ? OR name LIKE ?)"
                params.extend([f"%{search_query}%", f"%{search_query}%"])
                
            query += " ORDER BY timestamp DESC"
            cur = conn.execute(query, params)
            self.records = [dict(r) for r in cur.fetchall()]
        self.endResetModel()
        
    def get_record(self, row: int) -> dict:
        if 0 <= row < len(self.records):
            return self.records[row]
        return {}
