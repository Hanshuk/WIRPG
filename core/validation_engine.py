import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import openpyxl
from utils.image_utils import validate_image_file

@dataclass
class ValidationReport:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ValidationEngine:
    @staticmethod
    def validate_excel(path: str) -> ValidationReport:
        errors = []
        warnings = []
        if not os.path.exists(path):
            return ValidationReport(False, [f"Excel file not found: {path}"], [])
            
        try:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
            wb.close()
        except Exception as e:
            errors.append(f"Excel file corrupted or invalid: {str(e)}")
            return ValidationReport(False, errors, warnings)
            
        return ValidationReport(True, errors, warnings)
        
    @staticmethod
    def validate_images_folder(path: str) -> ValidationReport:
        errors = []
        warnings = []
        if not os.path.exists(path):
            return ValidationReport(False, [f"Images folder not found: {path}"], [])
            
        p = Path(path)
        if not p.is_dir():
            errors.append("Images path is not a directory.")
            return ValidationReport(False, errors, warnings)
            
        subdirs = [x for x in p.iterdir() if x.is_dir()]
        if not subdirs:
            warnings.append("Images folder contains no subdirectories.")
            
        return ValidationReport(len(errors) == 0, errors, warnings)
        
    @staticmethod
    def validate_record_fields(data: dict) -> ValidationReport:
        errors = []
        warnings = []
        
        # IAS No
        ias = str(data.get("ias_no", "")).strip()
        if not ias:
            errors.append("Missing IAS No.")
            
        # Name
        name = str(data.get("name", "")).strip()
        if not name:
            errors.append("Missing Beneficiary Name.")
            
        # EC
        ec = str(data.get("ec", "")).strip()
        if not ec:
            errors.append("Missing EC Number.")
            
        # Longitude
        lon = str(data.get("longitude", "")).strip()
        if not lon:
            errors.append("Missing Longitude.")
        else:
            try:
                lon_f = float(lon)
                if not (-180 <= lon_f <= 180):
                    errors.append(f"Longitude must be between -180 and 180 (found: {lon})")
            except ValueError:
                errors.append(f"Longitude must be a valid decimal number (found: {lon})")
                
        # Latitude
        lat = str(data.get("latitude", "")).strip()
        if not lat:
            errors.append("Missing Latitude.")
        else:
            try:
                lat_f = float(lat)
                if not (-90 <= lat_f <= 90):
                    errors.append(f"Latitude must be between -90 and 90 (found: {lat})")
            except ValueError:
                errors.append(f"Latitude must be a valid decimal number (found: {lat})")
                
        # Date Installed
        dt = str(data.get("date_installed", "")).strip()
        if not dt:
            errors.append("Missing Date Installed.")
            
        # Optional fields check but log warn/info if empty
        if not str(data.get("full_address", "")).strip():
            warnings.append("Address is empty.")
            
        return ValidationReport(len(errors) == 0, errors, warnings)
