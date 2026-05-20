import os
import re
import unicodedata
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional
import rapidfuzz
import logging

logger = logging.getLogger("CostPlusSolarDocs.image_matcher")

@dataclass
class ImageMatchResult:
    excel_name: str
    matched_folder_path: Optional[Path]
    match_stage: str
    confidence: float
    flagged: bool
    slot_paths: Dict[int, Optional[Path]]

    def __iter__(self):
        yield self.matched_folder_path
        yield self.confidence
        yield self.match_stage

class ImageMatcher:
    def __init__(self):
        self.index: Dict[str, Path] = {}
        self.supported_exts = {".jpg", ".jpeg", ".png", ".webp"}

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        # 1. Uppercase & 2. Strip
        t = text.upper().strip()
        # 7. Replace hyphens with space
        t = t.replace("-", " ")
        # 4, 5, 6. Remove commas, periods, underscores
        for char in [",", ".", "_"]:
            t = t.replace(char, "")
        
        # 8 & 9. Remove non-ASCII and Unicode Cf
        chars = []
        for c in t:
            if ord(c) > 127: continue
            if unicodedata.category(c) == 'Cf': continue
            chars.append(c)
        t = "".join(chars)
        
        # 3. Collapse whitespace & 10. Strip again
        t = " ".join(t.split())
        return t.strip()

    def build_index(self, root_folder: str):
        self.index.clear()
        root_path = Path(root_folder)
        if not root_path.exists() or not root_path.is_dir():
            logger.error(f"Root folder does not exist: {root_folder}")
            return
            
        for entry in root_path.iterdir():
            if entry.is_dir():
                norm_name = self._normalize(entry.name)
                self.index[norm_name] = entry
                
        logger.info(f"Built image index with {len(self.index)} folders.")

    def _find_slots(self, folder_path: Path) -> Dict[int, Optional[Path]]:
        slots = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
        if not folder_path:
            return slots
            
        for entry in folder_path.iterdir():
            if entry.is_file() and entry.suffix.lower() in self.supported_exts:
                stem = entry.stem
                # Check if stem is exactly '1', '2', etc.
                if stem in [str(i) for i in range(1, 7)]:
                    slot = int(stem)
                    slots[slot] = entry
        
        for i in range(1, 7):
            if not slots[i]:
                logger.warning(f"Missing slot {i} in folder {folder_path.name}")
                
        return slots

    def get_image_paths(self, folder_path: Path) -> Dict[int, Optional[str]]:
        slots = {1: None, 2: None, 3: None, 4: None, 5: None, 6: None}
        if not folder_path:
            return slots
        p = Path(folder_path)
        if not p.exists() or not p.is_dir():
            return slots
        for entry in p.iterdir():
            if entry.is_file() and entry.suffix.lower() in self.supported_exts:
                stem = entry.stem
                if stem in [str(i) for i in range(1, 7)]:
                    slot = int(stem)
                    slots[slot] = str(entry)
        return slots

    def match(self, excel_name: str) -> ImageMatchResult:
        norm_excel = self._normalize(excel_name)
        
        if not self.index:
            return ImageMatchResult(excel_name, None, "UNMATCHED", 0.0, False, self._find_slots(None))

        # Stage 1: Exact
        if norm_excel in self.index:
            path = self.index[norm_excel]
            logger.info(f"EXACT match for {excel_name}")
            return ImageMatchResult(excel_name, path, "EXACT", 100.0, False, self._find_slots(path))
            
        # Prepare for fuzzy
        best_score = 0.0
        best_match = None
        best_norm = ""
        
        # Stage 2: Token Sort Ratio
        for norm_folder, path in self.index.items():
            score = rapidfuzz.fuzz.token_sort_ratio(norm_excel, norm_folder)
            if score > best_score:
                best_score = score
                best_match = path
                best_norm = norm_folder
                
        if best_score >= 92.0:
            logger.info(f"TOKEN_SORT match ({best_score}) for {excel_name} -> {best_norm}")
            return ImageMatchResult(excel_name, best_match, "TOKEN_SORT", best_score, False, self._find_slots(best_match))
            
        # Stage 3: Partial Ratio
        best_score = 0.0
        for norm_folder, path in self.index.items():
            score = rapidfuzz.fuzz.partial_ratio(norm_excel, norm_folder)
            if score > best_score:
                best_score = score
                best_match = path
                best_norm = norm_folder
                
        if best_score >= 88.0:
            logger.warning(f"PARTIAL match ({best_score}) for {excel_name} -> {best_norm} [FLAGGED]")
            return ImageMatchResult(excel_name, best_match, "PARTIAL", best_score, True, self._find_slots(best_match))
            
        # Stage 4: WRatio
        best_score = 0.0
        for norm_folder, path in self.index.items():
            score = rapidfuzz.fuzz.WRatio(norm_excel, norm_folder)
            if score > best_score:
                best_score = score
                best_match = path
                best_norm = norm_folder
                
        if best_score >= 85.0:
            logger.warning(f"WRATIO match ({best_score}) for {excel_name} -> {best_norm} [FLAGGED]")
            return ImageMatchResult(excel_name, best_match, "WRATIO", best_score, True, self._find_slots(best_match))
            
        # Stage 5: No match
        logger.warning(f"UNMATCHED for {excel_name}")
        return ImageMatchResult(excel_name, None, "UNMATCHED", 0.0, False, self._find_slots(None))
