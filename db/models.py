from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class BeneficiaryRecord:
    ias_no: str
    item_no: str
    name: str
    purok_sitio: str
    barangay: str
    municipality: str
    system_box_sn: str
    solar_panel_sn: str
    longitude: float
    latitude: float
    date_installed: str
    excel_row: int

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
