import logging
from typing import List, Dict, Set
from db.models import BeneficiaryRecord, ValidationError, ErrorCode

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
                    names = [r.name for r in matched_records]
                    names_str = " and ".join(names) if len(names) == 2 else ", ".join(names[:-1]) + ", and " + names[-1]
                    
                    field_display = field.replace('_', ' ').title()
                    if field == "ias_no": field_display = "IAS NO"
                    elif field == "system_box_sn": field_display = "System Box Serial Number"
                    elif field == "solar_panel_sn": field_display = "Solar Panel Serial Number"
                    elif field == "longitude": field_display = "Longitude value"
                    elif field == "latitude": field_display = "Latitude value"
                    
                    # Store original error value in the message (if needed) but display the nice string
                    err_msg = f"{names_str} share the same {field_display} ({val})"
                    
                    for rec in matched_records:
                        if not any(e.message == err_msg for e in rec.validation_errors):
                            rec.validation_errors.append(ValidationError(ErrorCode.EXCEL_DUPLICATE, err_msg))

        if duplicate_count > 0:
            logger.warning(f"Detected {duplicate_count} unique value collisions across {len(records)} records.")
        else:
            logger.info("No field-level duplicates detected in batch.")
