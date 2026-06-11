import os
import random
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFont

def generate_excel():
    wb = Workbook()
    ws = wb.active
    ws.append([
        "IAS No.", "Name", "Full Address", "System Box S.N", "Solar Panel S.N",
        "Longitude", "Latitude", "Date Installed", "EC", "Name of Representative", "Relationship"
    ])
    
    rows = [
        ["IAS-001", "DELA CRUZ, PEDRO", "Purok 1, Brgy. San Jose, Leyte", "SB-001", "SP-001", "124.123456", "10.123456", "2024-01-15", "COTELCO", "DELA CRUZ, ANA", "SPOUSE"],
        ["IAS-002", "REYES, MARIA", "Purok 2, Brgy. Santo Nino, Leyte", "SB-002", "SP-002", "124.654321", "10.654321", "2024-01-16", "COTELCO", "REYES, JOSE", "SPOUSE"],
        ["IAS-003", "SANTOS, JOSE", "Purok 3, Brgy. Poblacion, Leyte", "SB-003", "SP-003", "124.123456", "10.999999", "2024-01-17", "COTELCO", "SANTOS, CLARA", "SPOUSE"],
        ["IAS-004", "GARCIA, LUZ", "Purok 4, Brgy. Remedios, Leyte", "SB-004", "SP-001", "124.777777", "10.777777", "2024-01-18", "COTELCO", "GARCIA, RAMON", "SPOUSE"],
        ["IAS-005", "BAUTISTA, CARLO", "Purok 5, Brgy. San Isidro, Leyte", "SB-005", "SP-005", "124.888888", "10.888888", "2024-01-19", "COTELCO", "BAUTISTA, LISA", "SPOUSE"]
    ]
    
    for r in rows:
        ws.append(r)
        
    wb.save("test_batch.xlsx")
    print("test_batch.xlsx created")

def generate_images():
    base_dir = "test_images"
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs("test_output", exist_ok=True)

    beneficiaries = [
        "DELA CRUZ, PEDRO",
        "REYES, MARIA",
        "SANTOS, JOSE",
        "GARCIA, LUZ",
        "BAUTISTA, CARLO"
    ]
    
    colors = [
        ("red", "blue", "green", "yellow", "purple", "orange"),
        ("cyan", "red", "pink", "brown", "gray", "lime"), # slot 2 is red (same as PEDRO slot 1)
        ("white", "black", "magenta", "teal", "navy", "maroon"),
        ("olive", "silver", "gold", "coral", "indigo", "violet"),
        ("salmon", "plum", "orchid", "khaki", "azure", "ivory")
    ]
    
    for i, name in enumerate(beneficiaries):
        folder = os.path.join(base_dir, name)
        os.makedirs(folder, exist_ok=True)
        
        for slot in range(1, 7):
            color = colors[i][slot-1]
            img = Image.new("RGB", (800, 600), color)
            d = ImageDraw.Draw(img)
            
            # Draw random noise but SEED it so it's perfectly unique per image but deterministic
            random.seed(f"{name}_{slot}")
            for _ in range(30):
                x1 = random.randint(0, 800)
                y1 = random.randint(0, 600)
                x2 = random.randint(0, 800)
                y2 = random.randint(0, 600)
                d.line((x1, y1, x2, y2), fill="white", width=15)
            
            d.text((50, 400), f"{name} - Slot {slot}", fill="black")
            img.save(os.path.join(folder, f"{slot}.jpg"))

    print("test_images and test_output created")

    # Make the exact duplicate copy for the test trigger
    import shutil
    src = os.path.join(base_dir, "DELA CRUZ, PEDRO", "1.jpg")
    dst = os.path.join(base_dir, "REYES, MARIA", "2.jpg")
    shutil.copy(src, dst)
    print("Exact duplicate copy created")

if __name__ == "__main__":
    generate_excel()
    generate_images()
