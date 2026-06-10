import unittest
from core.duplicate_detector import DuplicateDetector
from db.models import BeneficiaryRecord

class TestDuplicateDetector(unittest.TestCase):
    def test_no_duplicates(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS002", "Name B", "Add 2", "SBOX02", "PANEL02", "Jan 2", "Rep", "Rel", "11", "21")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        
        for r in records:
            self.assertEqual(len(r.validation_errors), 0)

    def test_ias_duplicate(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS001", "Name B", "Add 2", "SBOX02", "PANEL02", "Jan 2", "Rep", "Rel", "11", "21")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        
        for r in records:
            self.assertEqual(len(r.validation_errors), 1)
            self.assertIn("Duplicate found on field 'ias_no'", r.validation_errors[0])

    def test_system_box_duplicate(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS002", "Name B", "Add 2", "SBOX01", "PANEL02", "Jan 2", "Rep", "Rel", "11", "21")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        
        for r in records:
            self.assertEqual(len(r.validation_errors), 1)
            self.assertIn("Duplicate found on field 'system_box_sn'", r.validation_errors[0])

    def test_ignores_blank_fields(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS002", "Name B", "Add 2", "", "PANEL02", "Jan 2", "Rep", "Rel", "11", "21"),
            BeneficiaryRecord(3, "EC", "IAS003", "Name C", "Add 3", "N/A", "PANEL03", "Jan 3", "Rep", "Rel", "12", "22")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        
        for r in records:
            self.assertEqual(len(r.validation_errors), 0)

    def test_name_duplicate(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS002", "Name A", "Add 2", "SBOX02", "PANEL02", "Jan 2", "Rep", "Rel", "11", "21")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        for r in records:
            self.assertEqual(len(r.validation_errors), 1)
            self.assertIn("Duplicate found on field 'name'", r.validation_errors[0])

    def test_solar_panel_duplicate(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS002", "Name B", "Add 2", "SBOX02", "PANEL01", "Jan 2", "Rep", "Rel", "11", "21")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        for r in records:
            self.assertEqual(len(r.validation_errors), 1)
            self.assertIn("Duplicate found on field 'solar_panel_sn'", r.validation_errors[0])

    def test_coordinates_duplicate(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS002", "Name B", "Add 2", "SBOX02", "PANEL02", "Jan 2", "Rep", "Rel", "10", "20")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        for r in records:
            self.assertEqual(len(r.validation_errors), 2) # lon and lat both matched
            
    def test_multiple_duplicates(self):
        records = [
            BeneficiaryRecord(1, "EC", "IAS001", "Name A", "Add 1", "SBOX01", "PANEL01", "Jan 1", "Rep", "Rel", "10", "20"),
            BeneficiaryRecord(2, "EC", "IAS001", "Name A", "Add 2", "SBOX01", "PANEL01", "Jan 2", "Rep", "Rel", "10", "20")
        ]
        detector = DuplicateDetector()
        detector.detect_duplicates(records)
        for r in records:
            self.assertTrue(len(r.validation_errors) > 1)

if __name__ == '__main__':
    unittest.main()
