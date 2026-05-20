import unittest
from core.image_matcher import ImageMatcher
import os
import tempfile
import shutil
from pathlib import Path

class TestImageMatcher(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.matcher = ImageMatcher()
        
        os.makedirs(os.path.join(self.temp_dir, "DOE, JOHN P."))
        os.makedirs(os.path.join(self.temp_dir, "SMITH JANE"))
        
        self.matcher.build_index(self.temp_dir)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_exact_match(self):
        path, score, stage = self.matcher.match("DOE, JOHN P.")
        self.assertEqual(stage, "EXACT")
        self.assertEqual(score, 100.0)
        
    def test_fuzzy_match(self):
        path, score, stage = self.matcher.match("John Doe P")
        self.assertTrue(score > 80.0)
        self.assertTrue(stage in ["TOKEN_SORT", "PARTIAL"])
