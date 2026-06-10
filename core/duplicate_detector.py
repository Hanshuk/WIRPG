import logging
from typing import List, Dict, Set
from db.models import BeneficiaryRecord

logger = logging.getLogger("CostPlusSolarDocs.duplicate_detector")

class DuplicateDetector:
    """
    Detects cross-row duplicates in Excel data across specific fields.
    If a match is found on any single monitored field (ignoring empty values),
    both rows are blocked by adding a validation ERROR to them.
    """

    def __init__(self):
        self.fields_to_check = [
            "ias_no",
            "name",
            "system_box_sn",
            "solar_panel_sn",
            "longitude",
            "latitude"
        ]

    def detect_duplicates(self, records: List[BeneficiaryRecord]) -> None:
        """
        Scans the list of records and adds validation errors to ANY record
        that shares a non-empty field value with another record.
        """
        # Dictionary structure: { field_name: { field_value: [list_of_records] } }
        tracker: Dict[str, Dict[str, List[BeneficiaryRecord]]] = {
            field: {} for field in self.fields_to_check
        }

        # Step 1: Populate tracker
        for record in records:
            for field in self.fields_to_check:
                val = getattr(record, field, "")
                if not val:
                    continue  # Ignore empty strings
                val_clean = str(val).strip().upper()
                if not val_clean or val_clean == "N/A" or val_clean == "NAN":
                    continue
                
                if val_clean not in tracker[field]:
                    tracker[field][val_clean] = []
                tracker[field][val_clean].append(record)

        # Step 2: Mark duplicates
        # If any value list has length > 1, all records in that list are duplicates
        duplicate_count = 0
        for field, value_map in tracker.items():
            for val, matched_records in value_map.items():
                if len(matched_records) > 1:
                    duplicate_count += 1
                    # Block all matching rows
                    rows_involved = [str(r.excel_row) for r in matched_records]
                    err_msg = f"Duplicate found on field '{field}' with value '{val}'. Conflicting rows: {', '.join(rows_involved)}"
                    
                    for rec in matched_records:
                        if err_msg not in rec.validation_errors:
                            rec.validation_errors.append(err_msg)

        if duplicate_count > 0:
            logger.warning(f"Detected {duplicate_count} unique value collisions across {len(records)} records.")
        else:
            logger.info("No field-level duplicates detected in batch.")
