import os
from pathlib import Path

def ensure_dir(path_str: str) -> Path:
    p = Path(path_str)
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_file_size(path_str: str) -> int:
    try:
        return os.path.getsize(path_str)
    except OSError:
        return 0
