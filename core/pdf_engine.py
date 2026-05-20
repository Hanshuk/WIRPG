import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import logging

logger = logging.getLogger("CostPlusSolarDocs.pdf_engine")

PAGE_WIDTH = 594.0
PAGE_HEIGHT = 846.0

IMG_CELL_W = 236.74
IMG_CELL_H = 315.0

LOGO_RENDER_W  = 210.0
LOGO_RENDER_H  = 62.6
LOGO_X         = 192.0
LOGO_DRAW_Y    = 765.4
LOGO_FALLBACK_COLOR = (0/255, 53/255, 102/255)

class PDFEngineError(Exception):
    pass

def _save_temp_jpeg(pil_img: Image.Image) -> str:
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    pil_img.save(path, "JPEG", quality=85)
    return path

def _render_logo(canvas: canvas.Canvas, logo_path: Path) -> None:
    if logo_path and logo_path.exists() and logo_path.stat().st_size > 0:
        try:
            pil_logo = Image.open(logo_path).convert("RGB")
            tmp = _save_temp_jpeg(pil_logo)
            canvas.drawImage(
                tmp,
                LOGO_X,
                LOGO_DRAW_Y,
                width=LOGO_RENDER_W,
                height=LOGO_RENDER_H,
                preserveAspectRatio=False,
                mask="auto"
            )
            os.remove(tmp)
        except Exception as exc:
            logger.warning(f"Logo render failed: {exc} — using text fallback")
            _render_logo_fallback(canvas)
    else:
        logger.warning(f"Logo file not found at {logo_path} — using text fallback")
        _render_logo_fallback(canvas)

def _render_logo_fallback(canvas: canvas.Canvas) -> None:
    canvas.setFillColorRGB(*LOGO_FALLBACK_COLOR)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawCentredString(PAGE_WIDTH / 2, 800, "COST PLUS INC.")
    canvas.setFillColorRGB(0, 0, 0)

class PDFEngine:
    def __init__(self, template_engine=None):
        self.template = template_engine

    def _safe_str(self, val) -> str:
        if val is None or str(val).strip() == "" or str(val).lower() == "nan":
            return "N/A"
        return str(val)
        
    def _truncate_text(self, canvas: canvas.Canvas, text: str, font: str, size: float, max_width: float) -> str:
        if canvas.stringWidth(text, font, size) <= max_width:
            return text
        while len(text) > 0 and canvas.stringWidth(text + "...", font, size) > max_width:
            text = text[:-1]
        return text + "..."

    def _draw_image_cell(self, c: canvas.Canvas, x: float, y: float, w: float, h: float, img_path: Optional[str]):
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h)
        
        inner_pad = 4
        ix, iy = x + inner_pad, y + inner_pad
        iw, ih = w - 2*inner_pad, h - 2*inner_pad
        
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).convert("RGB")
                orig_w, orig_h = pil_img.size
                scale = min(iw / orig_w, ih / orig_h)
                draw_w = orig_w * scale
                draw_h = orig_h * scale
                cx = ix + (iw - draw_w) / 2
                cy = iy + (ih - draw_h) / 2
                tmp = _save_temp_jpeg(pil_img)
                c.drawImage(tmp, cx, cy, draw_w, draw_h, preserveAspectRatio=False)
                os.remove(tmp)
            except Exception:
                self._draw_placeholder(c, ix, iy, iw, ih)
        else:
            self._draw_placeholder(c, ix, iy, iw, ih)
            
    def _draw_placeholder(self, c: canvas.Canvas, x: float, y: float, w: float, h: float):
        c.setFillColorRGB(220/255, 220/255, 220/255)
        c.rect(x, y, w, h, fill=1, stroke=0)
        c.setFillColorRGB(150/255, 150/255, 150/255)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + w/2, y + h/2 - 3, "IMAGE NOT AVAILABLE")
        c.setFillColorRGB(0, 0, 0)

    def generate(self, record, image_paths: Dict[int, str], output_folder: str, logo_path: str = "") -> str:
        output_filename = f"{record.ias_no}_{record.name}.pdf".replace("/", "_").replace("\\", "_")
        final_path = Path(output_folder) / output_filename
        
        temp_dir = tempfile.mkdtemp()
        temp_pdf = Path(temp_dir) / output_filename
        
        try:
            c = canvas.Canvas(str(temp_pdf), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            self._render_page1(c, record, image_paths)
            self._render_page2(c, record, image_paths, Path(logo_path))
            self._render_page3(c, record, image_paths, Path(logo_path))
            
            c.save()
            
            if final_path.exists():
                os.remove(final_path)
            shutil.move(str(temp_pdf), str(final_path))
            return str(final_path)
            
        except Exception as e:
            logger.error(f"Failed to generate PDF for {record.ias_no}: {e}")
            raise PDFEngineError(f"PDF generation failed: {e}")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _render_page1(self, c: canvas.Canvas, record, image_paths):
        c.setPageSize((PAGE_WIDTH, PAGE_HEIGHT))
        margin = 18.0
        avail_w = PAGE_WIDTH - 2 * margin
        avail_h = PAGE_HEIGHT - 2 * margin
        img_path = image_paths.get(1)
        if img_path and os.path.exists(img_path):
            try:
                pil_img = Image.open(img_path).convert("RGB")
                orig_w, orig_h = pil_img.size
                scale = min(avail_w / orig_w, avail_h / orig_h)
                draw_w = orig_w * scale
                draw_h = orig_h * scale
                x = margin + (avail_w - draw_w) / 2
                y = margin + (avail_h - draw_h) / 2
                tmp = _save_temp_jpeg(pil_img)
                c.drawImage(tmp, x, y, draw_w, draw_h, preserveAspectRatio=False)
                os.remove(tmp)
            except Exception:
                c.setFillColorRGB(220/255, 220/255, 220/255)
                c.rect(margin, margin, avail_w, avail_h, fill=1, stroke=0)
                c.setFillColorRGB(150/255, 150/255, 150/255)
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT/2, "IMAGE NOT AVAILABLE")
                c.setFillColorRGB(0, 0, 0)
        else:
            c.setFillColorRGB(220/255, 220/255, 220/255)
            c.rect(margin, margin, avail_w, avail_h, fill=1, stroke=0)
            c.setFillColorRGB(150/255, 150/255, 150/255)
            c.setFont("Helvetica-Bold", 14)
            c.drawCentredString(PAGE_WIDTH/2, PAGE_HEIGHT/2, "IMAGE NOT AVAILABLE")
            c.setFillColorRGB(0, 0, 0)
        c.showPage()

    def _render_page2(self, c: canvas.Canvas, record, image_paths, logo_path):
        c.setPageSize((PAGE_WIDTH, PAGE_HEIGHT))
        _render_logo(c, logo_path)
        
        c.setLineWidth(0.5)
        c.rect(58, 754, 478, 36)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(297, 778, "SUPPLY, INSTALLATION, TESTING, AND COMMISSIONING OF SOLAR PV MAINSTREAMING FOR")
        c.drawCentredString(297, 766, 'COTELCO, INC."FRANCHISE AREA 2025-3000 PVM/SHS')
        
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(140, 748, self._safe_str(record.ec))
        c.drawCentredString(297, 748, "3000 -")
        c.drawCentredString(454, 748, f"{self._safe_str(record.ec)}")
        
        c.rect(58, 682, 478, 56)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(63, 728, "IAS NO.")
        c.drawString(63, 714, "NAME OF BENEFICIARY:")
        c.drawString(63, 700, "ADDRESS:")
        c.drawString(63, 686, "DATE OF INSTALLATION:")
        
        c.setFont("Helvetica", 9)
        c.drawString(200, 728, self._truncate_text(c, self._safe_str(record.ias_no), "Helvetica", 9, 320))
        c.drawString(200, 714, self._truncate_text(c, self._safe_str(record.name), "Helvetica", 9, 320))
        c.drawString(200, 700, self._truncate_text(c, self._safe_str(record.full_address), "Helvetica", 9, 320))
        c.drawString(200, 686, self._safe_str(record.date_installed))
        
        c.rect(58, 644, 478, 28)
        c.setFont("Helvetica", 8)
        c.drawString(63, 664, "In case of unavailability of registered beneficiary during installation and documentation.")
        c.drawString(63, 654, "Please fill out the necessary information:")
        
        c.rect(58, 610, 478, 26)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(63, 626, "NAME OF REPRESENTATIVE:")
        c.drawString(63, 612, "RELATIONSHIP:")
        c.setFont("Helvetica", 9)
        c.drawString(210, 626, self._safe_str(record.representative_name))
        c.drawString(210, 612, self._safe_str(record.relationship))
        
        self._draw_image_cell(c, 58, 280, IMG_CELL_W, IMG_CELL_H, image_paths.get(1))
        self._draw_image_cell(c, 316, 280, IMG_CELL_W, IMG_CELL_H, image_paths.get(2))
        
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(176.37, 267, "DULY ACCOMPLISHED IAS FORM")
        c.drawCentredString(434.37, 267, "GEOTAGGED PHOTO OF SOLAR PANEL W/BENEFICIARY")
        
        c.rect(316, 220, 236.74, 40)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(320, 252, "LONGITUDE:")
        c.drawString(320, 240, "LATITUDE:")
        c.drawString(320, 228, "DATE INSTALLED:")
        c.setFont("Helvetica", 8)
        c.drawString(380, 252, self._safe_str(record.longitude))
        c.drawString(380, 240, self._safe_str(record.latitude))
        c.drawString(400, 228, self._safe_str(record.date_installed))
        
        c.showPage()

    def _render_page3(self, c: canvas.Canvas, record, image_paths, logo_path):
        c.setPageSize((PAGE_WIDTH, PAGE_HEIGHT))
        _render_logo(c, logo_path)
        
        self._draw_image_cell(c, 58, 441, IMG_CELL_W, IMG_CELL_H, image_paths.get(3))
        self._draw_image_cell(c, 316, 441, IMG_CELL_W, IMG_CELL_H, image_paths.get(4))
        self._draw_image_cell(c, 58, 46, IMG_CELL_W, IMG_CELL_H, image_paths.get(5))
        self._draw_image_cell(c, 316, 46, IMG_CELL_W, IMG_CELL_H, image_paths.get(6))
        
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(176.37, 427, "GEOTAGGED PHOTO OF SYSTEM BOX")
        c.drawCentredString(434.37, 427, "GEOTAGGED PHOTO OF LIGHTING FIXTURE")
        c.drawCentredString(176.37, 32, "GEOTAGGED PHOTO OF FLASHLIGHT & RADIO")
        c.drawCentredString(434.37, 32, "GEOTAGGED PHOTO OF RFID CARD")
        
        cells = [
            (62, 118, 413),
            (320, 376, 413),
            (62, 118, 18),
            (320, 376, 18)
        ]
        
        for lx, vx, y in cells:
            c.setFont("Helvetica-Bold", 7)
            c.drawString(lx, y, "NAME:")
            c.drawString(lx, y - 10, "LONGITUDE:")
            c.drawString(lx, y - 20, "LATITIDE:")
            c.drawString(lx, y - 30, "DATE OF INSTALLATION:")
            
            c.setFont("Helvetica", 7)
            c.drawString(vx, y, self._truncate_text(c, self._safe_str(record.name), "Helvetica", 7, 115))
            c.drawString(vx, y - 10, self._safe_str(record.longitude))
            c.drawString(vx, y - 20, self._safe_str(record.latitude))
            c.drawString(vx, y - 30, self._safe_str(record.date_installed))
            
        c.showPage()
