import os
import unittest
import shutil
import tempfile
from PIL import Image
from core.image_duplicate_detector import ImageDuplicateDetector
from db.database import db

class TestImageDuplicateDetector(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test.sqlite")
        db.db_path = self.db_path
        
        # Init table
        with db.connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS image_hash_registry (
                    image_id TEXT PRIMARY KEY,
                    sha256_hash TEXT NOT NULL,
                    phash TEXT NOT NULL,
                    dhash TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    ias_no TEXT NOT NULL,
                    slot INTEGER NOT NULL,
                    registered_at TEXT NOT NULL
                )
            """)

        self.img1_path = os.path.join(self.test_dir, "img1.jpg")
        self.img2_path = os.path.join(self.test_dir, "img2.jpg")
        self.img3_path = os.path.join(self.test_dir, "img3.jpg")

        # Create exact same images
        img1 = Image.new('RGB', (100, 100), color='red')
        img1.save(self.img1_path)
        img1.save(self.img2_path)
        
        # Create different image (striped to ensure different grayscale pHash/dHash)
        img3 = Image.new('RGB', (100, 100), color='blue')
        import PIL.ImageDraw as ImageDraw
        d = ImageDraw.Draw(img3)
        d.rectangle([20, 20, 80, 80], fill="white")
        img3.save(self.img3_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_compute_hashes(self):
        detector = ImageDuplicateDetector()
        hashes1 = detector.compute_hashes(self.img1_path)
        hashes2 = detector.compute_hashes(self.img2_path)
        hashes3 = detector.compute_hashes(self.img3_path)
        
        self.assertIsNotNone(hashes1)
        self.assertEqual(hashes1, hashes2)
        self.assertNotEqual(hashes1, hashes3)

    def test_exact_duplicate_detection(self):
        detector = ImageDuplicateDetector()
        is_dup, err = detector.check_and_register("ID1", self.img1_path, "IAS001", 1)
        self.assertFalse(is_dup)
        
        # Checking the exact same image for a DIFFERENT IAS No should flag it
        is_dup, err = detector.check_and_register("ID2", self.img2_path, "IAS002", 1)
        self.assertTrue(is_dup)
        self.assertIn("Exact image copy found", err)

    def test_self_re_registration(self):
        detector = ImageDuplicateDetector()
        detector.check_and_register("ID1", self.img1_path, "IAS001", 1)
        # Re-registering same image for SAME IAS No and Slot shouldn't flag duplicate
        is_dup, err = detector.check_and_register("ID1_rev", self.img1_path, "IAS001", 1)
        self.assertFalse(is_dup)

    def test_perceptual_duplicate(self):
        # We need to simulate perceptual hashing.
        # Since generating images that have hamming distance 1 is tricky synthetically,
        # we will assume the Exact Duplicate test validates the registry flow,
        # and unit tests for perceptual will be covered if we add some slight noise.
        
        # We will save the exact same image with a slightly different quality to change the SHA256
        # but keep it perceptually identical.
        img4_path = os.path.join(self.test_dir, "img4.jpg")
        img4 = Image.open(self.img1_path)
        img4.save(img4_path, quality=85)

        detector = ImageDuplicateDetector()
        detector.check_and_register("ID1", self.img1_path, "IAS001", 1)
        
        # Same image but slightly altered -> should hit perceptual duplicate
        is_dup, err = detector.check_and_register("ID4", img4_path, "IAS004", 1)
        self.assertTrue(is_dup)
        self.assertIn("Perceptual duplicate", err)
        
    def test_different_images_same_ias(self):
        detector = ImageDuplicateDetector()
        is_dup, err = detector.check_and_register("ID1", self.img1_path, "IAS001", 1)
        self.assertFalse(is_dup)
        # Same IAS, different image -> False
        is_dup, err = detector.check_and_register("ID3", self.img3_path, "IAS001", 2)
        self.assertFalse(is_dup)
        
    def test_ignore_blank_paths(self):
        detector = ImageDuplicateDetector()
        is_dup, err = detector.check_and_register("ID1", "", "IAS001", 1)
        self.assertFalse(is_dup)
        
    def test_ignore_invalid_paths(self):
        detector = ImageDuplicateDetector()
        is_dup, err = detector.check_and_register("ID1", "fake_path.jpg", "IAS001", 1)
        self.assertFalse(is_dup)
        
    def test_clear_registry(self):
        detector = ImageDuplicateDetector()
        detector.check_and_register("ID1", self.img1_path, "IAS001", 1)
        with db.connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM image_hash_registry")
            self.assertEqual(cur.fetchone()[0], 1)
            
        detector.clear_registry()
        with db.connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM image_hash_registry")
            self.assertEqual(cur.fetchone()[0], 0)

if __name__ == '__main__':
    unittest.main()
