import os
import hashlib
import logging
from typing import Tuple, List, Optional
from datetime import datetime
from PIL import Image
logger = logging.getLogger("CostPlusSolarDocs.image_duplicate_detector")

try:
    import imagehash
except ImportError as e:
    logger.error("DEBUG: FAILED TO IMPORT imagehash! Image duplicate detection will fail.")
    raise

from db.database import db

class ImageDuplicateDetector:
    def __init__(self):
        self.threshold = 4

    def compute_hashes(self, image_path: str) -> Optional[Tuple[str, str, str]]:
        """
        Computes SHA256, pHash, and dHash for the given image.
        Returns a tuple (sha256_hash, phash, dhash).
        """
        if not os.path.exists(image_path) or not os.path.isfile(image_path):
            return None

        try:
            # Compute exact hash (SHA256)
            sha256 = hashlib.sha256()
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            sha_hex = sha256.hexdigest()

            # Compute perceptual hashes
            img = Image.open(image_path).convert("RGB")
            ph = str(imagehash.phash(img))
            dh = str(imagehash.dhash(img))

            return sha_hex, ph, dh
        except Exception as e:
            logger.error(f"Failed to compute hashes for {image_path}: {e}")
            return None

    def check_and_register(self, image_id: str, image_path: str, ias_no: str, slot: int) -> Tuple[bool, Optional[str]]:
        """
        Checks if the image is a duplicate of a previously registered image.
        Returns (is_duplicate, conflict_details).
        If not a duplicate, registers it.
        """
        hashes = self.compute_hashes(image_path)
        if not hashes:
            return False, "Failed to read image"

        sha256_hash, p_hash_str, d_hash_str = hashes
        
        try:
            p_hash = imagehash.hex_to_hash(p_hash_str)
            d_hash = imagehash.hex_to_hash(d_hash_str)
        except Exception:
            return False, "Failed to parse perceptual hashes"

        with db.connection() as conn:
            # Tier 1: Check SHA256 (exact duplicate)
            cursor = conn.execute(
                "SELECT ias_no, slot, file_path FROM image_hash_registry WHERE sha256_hash = ?",
                (sha256_hash,)
            )
            exact_match = cursor.fetchone()
            if exact_match:
                if exact_match["ias_no"] == ias_no and exact_match["slot"] == slot:
                    # Same exact record, not a conflict
                    return False, None
                return True, exact_match['ias_no']

            # Tier 2: Check Perceptual Hashes
            cursor = conn.execute("SELECT ias_no, slot, phash, dhash, file_path FROM image_hash_registry")
            all_records = cursor.fetchall()
            
            for row in all_records:
                if row["ias_no"] == ias_no and row["slot"] == slot:
                    continue  # Ignore self

                try:
                    existing_p = imagehash.hex_to_hash(row["phash"])
                    existing_d = imagehash.hex_to_hash(row["dhash"])
                    
                    p_diff = p_hash - existing_p
                    d_diff = d_hash - existing_d
                    
                    if p_diff <= self.threshold and d_diff <= self.threshold:
                        return True, row['ias_no']
                except Exception:
                    continue

            # If no duplicate found, register it
            now = datetime.now().isoformat()
            # Replace existing if any for this exact slot
            conn.execute(
                "DELETE FROM image_hash_registry WHERE ias_no = ? AND slot = ?", 
                (ias_no, slot)
            )
            conn.execute(
                """
                INSERT INTO image_hash_registry 
                (image_id, sha256_hash, phash, dhash, file_path, ias_no, slot, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (image_id, sha256_hash, p_hash_str, d_hash_str, image_path, ias_no, slot, now)
            )
            conn.commit()
            
        return False, None

    def clear_registry(self):
        """Clear all registered image hashes. Useful for tests or resetting."""
        try:
            with db.connection() as conn:
                conn.execute("DELETE FROM image_hash_registry")
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear image hash registry: {e}")
