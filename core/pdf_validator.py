import fitz
import os
from dataclasses import dataclass
from typing import List

@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class PDFValidator:
    @staticmethod
    def validate(pdf_path: str) -> ValidationResult:
        errors = []
        warnings = []
        
        if not os.path.exists(pdf_path):
            return ValidationResult(False, [f"File not found: {pdf_path}"], [])
            
        file_size = os.path.getsize(pdf_path)
        if file_size < 10240:
            errors.append(f"PDF file size too small ({file_size} bytes). May be corrupted or empty.")
            return ValidationResult(False, errors, warnings)
            
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            return ValidationResult(False, [f"Failed to open PDF: {str(e)}"], [])
            
        try:
            if doc.needs_pass:
                errors.append("PDF is password protected.")
                
            if doc.page_count != 3:
                errors.append(f"Expected 3 pages, found {doc.page_count}.")
                
            for i in range(doc.page_count):
                try:
                    page = doc.load_page(i)
                    _ = page.get_text()
                except Exception as e:
                    errors.append(f"Failed to parse page {i+1}: {str(e)}")
                    
        finally:
            doc.close()
            
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings)
