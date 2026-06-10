import unittest
import pandas as pd
from core.excel_parser import ExcelParser, ExcelParserError
from db.models import BeneficiaryRecord
import os
import tempfile

class TestExcelParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.valid_excel = os.path.join(self.temp_dir, "valid.xlsx")
        
        df = pd.DataFrame({
            "IAS No": ["IAS001"], "Item No": ["1"], "Name": ["John Doe"],
            "Full Address": ["123 Fake St, Brgy 1, Muni 1"],
            "System Box S.N": ["BX1"],
            "Solar Panel S.N": ["SP1"], "Longitude": [121.0],
            "Latitude": [14.0], "Date Installed": ["2024-01-01"]
        })
        df.to_excel(self.valid_excel, index=False)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
        
    def test_valid_excel(self):
        parser = ExcelParser(self.valid_excel)
        records = parser.parse()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].ias_no, "IAS001")
