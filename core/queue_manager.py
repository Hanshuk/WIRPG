import uuid
import hashlib
import json
from datetime import datetime
from typing import List, Optional, Dict
from db.models import QueueEntry, BeneficiaryRecord
from db.database import db
import threading

class QueueStats:
    def __init__(self, pending=0, processing=0, completed=0, failed=0, skipped=0):
        self.pending = pending
        self.processing = processing
        self.completed = completed
        self.failed = failed
        self.skipped = skipped
        self.total = pending + processing + completed + failed + skipped

class QueueManager:
    def __init__(self):
        self._lock = threading.Lock()
        
    def _generate_checksum(self, record: BeneficiaryRecord) -> str:
        data = f"{record.ias_no}|{record.name}|{record.longitude}|{record.latitude}"
        return hashlib.sha256(data.encode()).hexdigest()

    def enqueue(self, records: List[BeneficiaryRecord]):
        now = datetime.now().isoformat()
        with self._lock, db.connection() as conn:
            for rec in records:
                checksum = self._generate_checksum(rec)
                cur = conn.execute("SELECT queue_id FROM processing_queue WHERE checksum = ? AND status IN ('PENDING', 'PROCESSING')", (checksum,))
                if cur.fetchone():
                    continue
                    
                q_id = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO processing_queue 
                    (queue_id, ias_no, name, excel_row, status, retry_count, error_message, output_path, created_at, updated_at, checksum)
                    VALUES (?, ?, ?, ?, 'PENDING', 0, '', '', ?, ?, ?)
                """, (q_id, rec.ias_no, rec.name, rec.excel_row, now, now, checksum))
            conn.commit()

    def dequeue_next(self) -> Optional[Dict]:
        with self._lock, db.connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cur = conn.execute("""
                SELECT * FROM processing_queue 
                WHERE status = 'PENDING' 
                ORDER BY created_at ASC LIMIT 1
            """)
            row = cur.fetchone()
            if row:
                now = datetime.now().isoformat()
                conn.execute("UPDATE processing_queue SET status = 'PROCESSING', updated_at = ? WHERE queue_id = ?", (now, row['queue_id']))
                conn.commit()
                return dict(row)
            conn.commit()
            return None

    def mark_completed(self, queue_id: str, output_path: str):
        now = datetime.now().isoformat()
        with self._lock, db.connection() as conn:
            conn.execute("UPDATE processing_queue SET status = 'COMPLETED', output_path = ?, updated_at = ? WHERE queue_id = ?",
                         (output_path, now, queue_id))
            conn.commit()

    def mark_failed(self, queue_id: str, error_message: str, increment_retry: bool = True):
        now = datetime.now().isoformat()
        with self._lock, db.connection() as conn:
            cur = conn.execute("SELECT retry_count FROM processing_queue WHERE queue_id = ?", (queue_id,))
            row = cur.fetchone()
            if not row: return
            
            retries = row['retry_count']
            if increment_retry:
                retries += 1
                
            status = 'FAILED'
            if retries >= 3:
                status = 'SKIPPED'
                
            conn.execute("UPDATE processing_queue SET status = ?, error_message = ?, retry_count = ?, updated_at = ? WHERE queue_id = ?",
                         (status, error_message, retries, now, queue_id))
            conn.commit()

    def get_queue_stats(self) -> QueueStats:
        stats = QueueStats()
        with self._lock, db.connection() as conn:
            cur = conn.execute("SELECT status, COUNT(*) as count FROM processing_queue GROUP BY status")
            for row in cur.fetchall():
                if row['status'] == 'PENDING': stats.pending = row['count']
                elif row['status'] == 'PROCESSING': stats.processing = row['count']
                elif row['status'] == 'COMPLETED': stats.completed = row['count']
                elif row['status'] == 'FAILED': stats.failed = row['count']
                elif row['status'] == 'SKIPPED': stats.skipped = row['count']
        stats.total = stats.pending + stats.processing + stats.completed + stats.failed + stats.skipped
        return stats

    def restore_interrupted(self):
        now = datetime.now().isoformat()
        with self._lock, db.connection() as conn:
            conn.execute("UPDATE processing_queue SET status = 'PENDING', updated_at = ? WHERE status = 'PROCESSING'", (now,))
            conn.commit()

    def get_failed_entries(self) -> List[Dict]:
        with self._lock, db.connection() as conn:
            cur = conn.execute("SELECT * FROM processing_queue WHERE status = 'FAILED' ORDER BY updated_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def clear_completed(self):
        with self._lock, db.connection() as conn:
            conn.execute("DELETE FROM processing_queue WHERE status IN ('COMPLETED', 'SKIPPED')")
            conn.commit()
