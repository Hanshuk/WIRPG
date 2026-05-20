import uuid
from datetime import datetime
from typing import Optional, Dict
from db.database import db

class RecoveryManager:
    def __init__(self):
        pass
        
    def start_session(self, excel_path: str, images_folder: str, output_folder: str, template_path: str, total_rows: int) -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with db.connection() as conn:
            conn.execute("""
                INSERT INTO session_state 
                (session_id, excel_path, images_folder, output_folder, template_path, total_rows, processed_count, failed_count, started_at, last_checkpoint_at, status)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?, 'RUNNING')
            """, (session_id, excel_path, images_folder, output_folder, template_path, total_rows, now, now))
            conn.commit()
        return session_id

    def get_running_session(self) -> Optional[Dict]:
        with db.connection() as conn:
            cur = conn.execute("SELECT * FROM session_state WHERE status = 'RUNNING' ORDER BY started_at DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                return dict(row)
        return None

    def update_checkpoint(self, session_id: str, processed_count: int, failed_count: int):
        now = datetime.now().isoformat()
        with db.connection() as conn:
            conn.execute("""
                UPDATE session_state 
                SET processed_count = ?, failed_count = ?, last_checkpoint_at = ?
                WHERE session_id = ?
            """, (processed_count, failed_count, now, session_id))
            conn.commit()

    def mark_completed(self, session_id: str):
        with db.connection() as conn:
            conn.execute("UPDATE session_state SET status = 'COMPLETED' WHERE session_id = ?", (session_id,))
            conn.commit()
            
    def mark_interrupted(self, session_id: str):
        with db.connection() as conn:
            conn.execute("UPDATE session_state SET status = 'INTERRUPTED' WHERE session_id = ?", (session_id,))
            conn.commit()
