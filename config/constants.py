import os
from pathlib import Path

APP_NAME = "Costplus IR Report Generator"
APP_VERSION = "1.0.0"
APP_ORG = "Cost Plus Inc."

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db_data" # Renamed to db_data to avoid conflict with module db
LOG_DIR = BASE_DIR / "logs"
ASSETS_DIR = BASE_DIR / "assets"

DB_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "costplus.sqlite"

EXCEL_REQUIRED_COLUMNS = [
    "IAS No", "Item No", "Name", "Purok/Sitio", "Barangay",
    "Municipality", "System Box S.N", "Solar Panel S.N",
    "Longitude", "Latitude", "Date Installed"
]
