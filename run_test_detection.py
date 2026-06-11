from core.excel_parser import ExcelParser
from core.duplicate_detector import DuplicateDetector
from core.image_matcher import ImageMatcher
from core.image_duplicate_detector import ImageDuplicateDetector
from db.models import ErrorCode
from db.migrations import run_migrations

# Initialize the DB
run_migrations()

records = ExcelParser("test_batch.xlsx").parse()
print(f"Parsed {len(records)} records")

# 1. Detect Excel duplicates
DuplicateDetector().detect_duplicates(records)
excel_dups = [r for r in records if any(e.code == ErrorCode.EXCEL_DUPLICATE for e in r.validation_errors)]

print(f"Excel duplicates — blocked rows: {[r.ias_no for r in excel_dups]}")
for r in excel_dups:
    for e in r.validation_errors:
        if e.code == ErrorCode.EXCEL_DUPLICATE:
            print(f"  Conflict: {e.message}")

# 2. Detect Image duplicates
im = ImageMatcher()
im.build_index("test_images")
img_detector = ImageDuplicateDetector()
img_detector.clear_registry() # Ensure clean state

image_dups = []
record_dict = {r.ias_no: r for r in records}

for r in records:
    matched_path, _, _ = im.match(r.name)
    if matched_path:
        image_paths = im.get_image_paths(matched_path)
        for slot, path in image_paths.items():
            is_dup, matched_ias = img_detector.check_and_register(f"{r.ias_no}_s{slot}", path, r.ias_no, slot)
            if is_dup:
                matched_name = record_dict[matched_ias].name if matched_ias in record_dict else matched_ias
                msg = f"{r.name} has a photo that is an exact copy of a photo already used for {matched_name}"
                print(f"  Image Duplicate found for {r.name} Slot {slot}: {msg}")
                if r not in image_dups:
                    image_dups.append(r)

print(f"Image duplicates — blocked beneficiaries: {[r.name for r in image_dups]}")
