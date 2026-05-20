import re

def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    name = name.upper()
    name = name.encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[,\._]', '', name)
    name = name.replace('-', ' ')
    name = re.sub(r'\s+', ' ', name).strip()
    return name
