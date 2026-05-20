import json
from pathlib import Path
from typing import Dict, Any

class TemplateEngineError(Exception):
    pass

class TemplateEngine:
    def __init__(self):
        self.template: Dict[str, Any] = {}
        self.default_path = Path(__file__).parent.parent / "config" / "template_default.json"

    def load(self, custom_path: str = None):
        if not self.default_path.exists():
            raise TemplateEngineError(f"Default template missing at {self.default_path}")
            
        with open(self.default_path, 'r') as f:
            self.template = json.load(f)
            
        if custom_path and Path(custom_path).exists():
            with open(custom_path, 'r') as f:
                custom_template = json.load(f)
                self._deep_merge(self.template, custom_template)
                
        self._resolve_inheritance(self.template)

    def _deep_merge(self, base: dict, update: dict):
        for k, v in update.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v

    def _resolve_inheritance(self, root: dict):
        for page_key, page_data in root.items():
            if not isinstance(page_data, dict):
                continue
            for element_key, element_data in page_data.items():
                if isinstance(element_data, dict) and "inherit" in element_data:
                    inherit_path = element_data["inherit"].split(".")
                    source = root
                    try:
                        for p in inherit_path:
                            source = source[p]
                        merged = source.copy()
                        merged.update({k: v for k, v in element_data.items() if k != "inherit"})
                        page_data[element_key] = merged
                    except KeyError:
                        pass

    def get(self, page: str, element: str, prop: str, default: Any = None) -> Any:
        try:
            return self.template[page][element][prop]
        except KeyError:
            return default
            
    def get_element(self, page: str, element: str) -> dict:
        try:
            return self.template[page][element]
        except KeyError:
            return {}
