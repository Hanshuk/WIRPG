import os
from datetime import datetime
from typing import List, Dict, Tuple
from db.database import db
from core.image_matcher import ImageMatcher
from core.pdf_validator import PDFValidator
from logging_engine.logger import app_logger

class ReprocessingSystem:
    def __init__(self, queue_manager=None):
        self.queue_manager = queue_manager
        self.matcher = ImageMatcher()

    def reset_flagged_to_pending(self) -> int:
        """
        Resets all FLAGGED records to PENDING.
        Returns the number of rows reset.
        """
        now = datetime.now().isoformat()
        with db.connection() as conn:
            cur = conn.execute("""
                UPDATE processing_queue
                SET status = 'PENDING', error_message = '', updated_at = ?, retry_count = 0
                WHERE status = 'FLAGGED'
            """)
            count = cur.rowcount
            conn.commit()
        app_logger.info(f"Reset {count} flagged records to PENDING.")
        return count

    def reset_failed_to_pending(self, force_all: bool = False) -> int:
        """
        Resets failed and skipped records to PENDING to resume processing.
        If force_all is True, resets regardless of retry_count. Otherwise, only resets if retry_count < 3.
        Returns the number of rows reset.
        """
        now = datetime.now().isoformat()
        with db.connection() as conn:
            if force_all:
                cur = conn.execute("""
                    UPDATE processing_queue
                    SET status = 'PENDING', error_message = '', updated_at = ?, retry_count = 0
                    WHERE status IN ('FAILED', 'SKIPPED')
                """, (now,))
            else:
                cur = conn.execute("""
                    UPDATE processing_queue
                    SET status = 'PENDING', error_message = '', updated_at = ?, retry_count = 0
                    WHERE status IN ('FAILED', 'SKIPPED') AND retry_count < 3
                """, (now,))
            count = cur.rowcount
            conn.commit()
        app_logger.info(f"Reset {count} failed records to PENDING for queue resume.")
        return count

    def auto_detect_corrections(self, images_folder: str) -> Tuple[int, List[str]]:
        """
        Scans the images folder and checks if flagged records with missing images
        or missing fields have been corrected.
        Returns the count of auto-corrected records and a list of their names.
        """
        if not images_folder or not os.path.exists(images_folder):
            return 0, []

        self.matcher.build_index(images_folder)
        
        corrected_count = 0
        corrected_names = []
        
        # Fetch flagged or failed records
        flagged_records = []
        with db.connection() as conn:
            cur = conn.execute("""
                SELECT queue_id, ias_no, name, error_type, missing_fields, missing_images
                FROM processing_queue
                WHERE status = 'FLAGGED' OR error_type IS NOT NULL AND error_type != ''
            """)
            flagged_records = [dict(r) for r in cur.fetchall()]

        now = datetime.now().isoformat()
        for rec in flagged_records:
            is_corrected = True
            reasons = []
            
            # 1. Check Missing Images Correction
            if rec.get("error_type") == "MISSING_IMAGES" or "image" in str(rec.get("error_type")).lower():
                match_res = self.matcher.match(rec["name"])
                if match_res.matched_folder_path:
                    # Check if all slots 1-6 are resolved
                    missing_slots = [slot for slot, path in match_res.slot_paths.items() if path is None]
                    if not missing_slots:
                        # Missing images are resolved!
                        reasons.append("All 6 image slots found")
                    else:
                        is_corrected = False
                else:
                    is_corrected = False

            # 2. Check Coordinates Correction
            # If coordinates were flagged, let's see if we corrected them.
            # In Excel mode, this means they must have been re-validated or fixed in Manual Mode.
            # If fixed in Manual Mode, they won't be flagged anymore since the user will save them.
            
            if is_corrected and reasons:
                with db.connection() as conn:
                    conn.execute("""
                        UPDATE processing_queue
                        SET status = 'PENDING', error_type = '', missing_fields = '', 
                            missing_images = '', suggested_fix = '', error_message = '',
                            updated_at = ?
                        WHERE queue_id = ?
                    """, (now, rec["queue_id"]))
                    conn.commit()
                corrected_count += 1
                corrected_names.append(rec["name"])
                app_logger.info(f"Auto-detected correction for {rec['name']}: {', '.join(reasons)}")

        return corrected_count, corrected_names
