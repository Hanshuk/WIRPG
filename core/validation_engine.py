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
