import sys
import os
import time
from PySide6.QtWidgets import QApplication
from core.batch_processor import BatchProcessor
from db.database import db
from db.migrations import run_migrations

app = QApplication(sys.argv)
run_migrations()

processor = BatchProcessor(num_workers=2)
print("=== CHECKPOINT A & B (Simulated Pre-flight Dialog) ===")
records, excel_dups, image_dups = processor.prepare_batch("test_batch.xlsx", "test_images")

print("Excel Conflicts Dialog:")
for r in excel_dups:
    errs = [e.message for e in r.validation_errors if e.code.name == 'EXCEL_DUPLICATE']
    print(f"  - {r.name}: {errs[0] if errs else 'None'}")

print("\nImage Conflicts Dialog:")
for r in image_dups:
    errs = [e.message for e in r.validation_errors if e.code.name == 'IMAGE_DUPLICATE']
    print(f"  - {r.name}: {errs[0] if errs else 'None'}")

print("\nSimulating click 'Continue & Skip These'...")
processor.commit_batch(records, "test_batch.xlsx", "test_images", "test_output")

print("\nWaiting for worker threads to finish...")
time.sleep(10) # wait for generation

print("\n=== CHECKPOINT D (Flagged Records DB State) ===")
with db.connection() as conn:
    cur = conn.execute("SELECT ias_no, name, status, error_message FROM processing_queue")
    for row in cur.fetchall():
        print(f"[{row['status']}] {row['name']}: {row['error_message']}")

print("\n=== CHECKPOINT E (PDF Output) ===")
outputs = os.listdir("test_output")
print(f"PDFs found in test_output/: {outputs}")
