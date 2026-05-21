import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from db.database import db
from config.constants import LOG_DIR
from utils.file_utils import ensure_dir

class LogExporter:
    @staticmethod
    def export_all() -> Dict[str, str]:
        """
        Queries the database and exports flagged and failed records to Excel and TXT files.
        Returns a dictionary of generated file paths.
        """
        ensure_dir(str(LOG_DIR))
        
        # 1. Fetch Flagged Records
        flagged_records = []
        with db.connection() as conn:
            cur = conn.execute("""
                SELECT ias_no, name, error_type, missing_fields, missing_images, 
                       suggested_fix, timestamp, retry_count, status
                FROM processing_queue
                WHERE status = 'FLAGGED' OR error_type IS NOT NULL AND error_type != ''
                ORDER BY timestamp DESC
            """)
            flagged_records = [dict(r) for r in cur.fetchall()]

        # 2. Fetch Failed Records
        failed_records = []
        with db.connection() as conn:
            cur = conn.execute("""
                SELECT ias_no, name, error_message, retry_count, updated_at, status
                FROM processing_queue
                WHERE status IN ('FAILED', 'SKIPPED')
                ORDER BY updated_at DESC
            """)
            failed_records = [dict(r) for r in cur.fetchall()]

        paths = {}
        
        # --- EXPORT FLAGGED RECORDS ---
        flagged_xlsx_path = LOG_DIR / "flagged_records.xlsx"
        flagged_txt_path = LOG_DIR / "flagged_records.txt"
        
        # Excel Flagged Export
        if flagged_records:
            df_flagged = pd.DataFrame(flagged_records)
            df_flagged.columns = [
                "IAS No", "Beneficiary Name", "Error Type", "Missing Fields", 
                "Missing Images", "Suggested Fix", "Timestamp", "Retry Attempts", "Status"
            ]
            # Ensure nice Excel styling and save
            df_flagged.to_excel(str(flagged_xlsx_path), index=False)
            paths["flagged_xlsx"] = str(flagged_xlsx_path)
        else:
            # Create an empty template
            df_empty = pd.DataFrame(columns=[
                "IAS No", "Beneficiary Name", "Error Type", "Missing Fields", 
                "Missing Images", "Suggested Fix", "Timestamp", "Retry Attempts", "Status"
            ])
            df_empty.to_excel(str(flagged_xlsx_path), index=False)
            paths["flagged_xlsx"] = str(flagged_xlsx_path)

        # TXT Flagged Export
        with open(flagged_txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"COSTPLUS SOLAR PV REPORT GENERATION - FLAGGED RECORDS LOG\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            if flagged_records:
                for idx, r in enumerate(flagged_records):
                    f.write(f"{idx+1}. IAS No: {r.get('ias_no')}\n")
                    f.write(f"   Beneficiary Name: {r.get('name')}\n")
                    f.write(f"   Error Type: {r.get('error_type') or 'N/A'}\n")
                    f.write(f"   Missing Fields: {r.get('missing_fields') or 'None'}\n")
                    f.write(f"   Missing Images: {r.get('missing_images') or 'None'}\n")
                    f.write(f"   Suggested Fix: {r.get('suggested_fix') or 'N/A'}\n")
                    f.write(f"   Timestamp: {r.get('timestamp') or 'N/A'}\n")
                    f.write(f"   Retry Attempts: {r.get('retry_count', 0)}\n")
                    f.write(f"   Status: {r.get('status')}\n")
                    f.write("-" * 50 + "\n")
            else:
                f.write("No flagged records found.\n")
        paths["flagged_txt"] = str(flagged_txt_path)

        # --- EXPORT FAILED RECORDS ---
        failed_xlsx_path = LOG_DIR / "failed_records.xlsx"
        failed_txt_path = LOG_DIR / "failed_records.txt"
        
        # Excel Failed Export
        if failed_records:
            df_failed = pd.DataFrame(failed_records)
            df_failed.columns = [
                "IAS No", "Beneficiary Name", "Error Message", "Retry Attempts", "Timestamp", "Status"
            ]
            df_failed.to_excel(str(failed_xlsx_path), index=False)
            paths["failed_xlsx"] = str(failed_xlsx_path)
        else:
            df_empty = pd.DataFrame(columns=[
                "IAS No", "Beneficiary Name", "Error Message", "Retry Attempts", "Timestamp", "Status"
            ])
            df_empty.to_excel(str(failed_xlsx_path), index=False)
            paths["failed_xlsx"] = str(failed_xlsx_path)

        # TXT Failed Export
        with open(failed_txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write(f"COSTPLUS SOLAR PV REPORT GENERATION - FAILED RECORDS LOG\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            if failed_records:
                for idx, r in enumerate(failed_records):
                    f.write(f"{idx+1}. IAS No: {r.get('ias_no')}\n")
                    f.write(f"   Beneficiary Name: {r.get('name')}\n")
                    f.write(f"   Error Message: {r.get('error_message') or 'N/A'}\n")
                    f.write(f"   Retry Attempts: {r.get('retry_count', 0)}\n")
                    f.write(f"   Timestamp: {r.get('updated_at')}\n")
                    f.write(f"   Status: {r.get('status')}\n")
                    f.write("-" * 50 + "\n")
            else:
                f.write("No failed records found.\n")
        paths["failed_txt"] = str(failed_txt_path)
        
        return paths
