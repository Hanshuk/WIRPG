from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class BeneficiaryRecord:
    excel_row: int
    ec: str
    ias_no: str
    name: str
    full_address: str
    system_box_sn: str
    solar_panel_sn: str
    date_installed: str          
    representative_name: str     
    relationship: str            
    longitude: str               
    latitude: str                
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

@dataclass
class QueueEntry:
    queue_id: str
    ias_no: str
    name: str
    excel_row: int
    status: str
    retry_count: int
    error_message: str
    output_path: str
    created_at: datetime
    updated_at: datetime
    checksum: str
