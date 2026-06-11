import pandas as pd
from typing import List
from db.models import BeneficiaryRecord, ValidationError, ErrorCode
import logging
import math

logger = logging.getLogger("CostPlusSolarDocs.excel_parser")

class ExcelParserError(Exception):
    pass

class ExcelParser:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def _normalize_header(self, h: str) -> str:
        if not isinstance(h, str):
            return ""
        h = h.upper().strip()
        for char in [".", ",", "-", "_"]:
            h = h.replace(char, "")
        return " ".join(h.split())

    def _map_headers(self, columns: List[str]) -> dict:
        mapping = {}
        
        rules = {
            "ec": ["EC"],
            "ias_no": ["IAS NO", "IAS NUMBER", "IASNO"],
            "name": ["NAME", "BENEFICIARY NAME", "BENEFICIARY"],
            "full_address": ["FULL ADDRESS", "ADDRESS", "FULLADDRESS"],
            "date_installed": ["DATE INSTALLED", "DATE OF INSTALLATION", "DATE INSTALL"],
            "representative_name": ["NAME OF REPRESENTATIVE", "REPRESENTATIVE NAME", "REP NAME"],
            "relationship": ["RELATIONSHIP", "RELATION"],
            "longitude": ["LONGITUDE", "LONG", "LON"],
            "latitude": ["LATITUDE", "LAT"],
            "system_box_sn": ["SYSTEM BOX SN", "SYSTEM BOX S.N", "SYSTEM BOX", "SYS BOX"],
            "solar_panel_sn": ["SOLAR PANEL SN", "SOLAR PANEL S.N", "SOLAR PANEL", "PANEL SN"]
        }
        
        for idx, col in enumerate(columns):
            norm = self._normalize_header(col)
            for key, variants in rules.items():
                if norm in [self._normalize_header(v) for v in variants]:
                    mapping[key] = idx
                    break
        return mapping

    def parse(self) -> List[BeneficiaryRecord]:
        try:
            df = pd.read_excel(self.file_path, header=None)
        except Exception as e:
            raise ExcelParserError(f"Failed to read Excel file: {e}")

        if df.empty:
            raise ExcelParserError("Excel file is empty")

        header_row_idx = -1
        mapping = {}
        
        for idx, row in df.iterrows():
            row_vals = [str(x) if pd.notna(x) else "" for x in row]
            mapping = self._map_headers(row_vals)
            
            # Require at least these columns to consider it a header row
            if "ias_no" in mapping and "name" in mapping and "longitude" in mapping and "latitude" in mapping:
                header_row_idx = idx
                break
                
        if header_row_idx == -1:
            raise ExcelParserError("Could not find a valid header row containing required columns.")

        required_keys = ["ias_no", "name", "full_address", "date_installed", "longitude", "latitude"]
        missing = [k for k in required_keys if k not in mapping]
        if missing:
            raise ExcelParserError(f"Missing required columns after mapping: {', '.join(missing)}")

        records = []
        ias_seen = set()

        for idx, row in df.iloc[header_row_idx + 1:].iterrows():
            if row.isna().all():
                continue
                
            def get_val(key, default=""):
                if key not in mapping:
                    return default
                val = row.iloc[mapping[key]]
                if pd.isna(val):
                    return default
                return str(val).strip()

            ias_no = get_val("ias_no")
            if ias_no.endswith(" 00:00:00"):
                ias_no = ias_no[:-9]
            name = get_val("name")
            ec = get_val("ec")
            full_address = get_val("full_address")
            date_installed = get_val("date_installed")
            system_box_sn = get_val("system_box_sn", "")
            solar_panel_sn = get_val("solar_panel_sn", "")
            rep_name = get_val("representative_name", "N/A")
            relationship = get_val("relationship", "N/A")
            longitude = get_val("longitude")
            latitude = get_val("latitude")
            
            if rep_name == "": rep_name = "N/A"
            if relationship == "": relationship = "N/A"

            errors = []
            warnings = []

            if not ias_no: errors.append(ValidationError(ErrorCode.MISSING_FIELD, "Missing IAS NO"))
            if not name: errors.append(ValidationError(ErrorCode.MISSING_FIELD, "Missing NAME"))
            
            if ias_no in ias_seen:
                warnings.append(f"Duplicate IAS NO: {ias_no}")
            if ias_no:
                ias_seen.add(ias_no)

            try:
                lon_f = float(longitude)
                if not (-180 <= lon_f <= 180):
                    errors.append(ValidationError(ErrorCode.INVALID_GPS, f"Longitude out of range: {longitude}"))
            except ValueError:
                errors.append(ValidationError(ErrorCode.INVALID_GPS, f"Invalid longitude: {longitude}"))

            try:
                lat_f = float(latitude)
                if not (-90 <= lat_f <= 90):
                    errors.append(ValidationError(ErrorCode.INVALID_GPS, f"Latitude out of range: {latitude}"))
            except ValueError:
                errors.append(ValidationError(ErrorCode.INVALID_GPS, f"Invalid latitude: {latitude}"))

            # Try to coerce date
            formatted_date = date_installed
            try:
                if date_installed:
                    parsed_date = pd.to_datetime(date_installed)
                    formatted_date = parsed_date.strftime("%B %d, %Y")
            except Exception:
                warnings.append(f"Unparseable DATE INSTALLED: {date_installed}")

            records.append(BeneficiaryRecord(
                excel_row=int(idx) + 1,
                ec=ec,
                ias_no=ias_no,
                name=name,
                full_address=full_address,
                system_box_sn=system_box_sn,
                solar_panel_sn=solar_panel_sn,
                date_installed=formatted_date,
                representative_name=rep_name,
                relationship=relationship,
                longitude=longitude,
                latitude=latitude,
                validation_errors=errors,
                validation_warnings=warnings
            ))

        if not records:
            raise ExcelParserError("No valid data rows found in Excel file.")

        return records
