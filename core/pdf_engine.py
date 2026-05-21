import os
import tempfile
import shutil
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from PIL import Image, ImageOps
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import logging
from config.constants import ASSETS_DIR

logger = logging.getLogger("CostPlusSolarDocs.pdf_engine")

PAGE_WIDTH = 594.0
PAGE_HEIGHT = 846.0

IMG_CELL_W = 236.74
IMG_CELL_H = 315.0

LOGO_RENDER_W  = 210.0
LOGO_RENDER_H  = 60.0
LOGO_X         = 192.0
LOGO_DRAW_Y    = 760.0
LOGO_FALLBACK_COLOR = (0/255, 53/255, 102/255)

class PDFEngineError(Exception):
    pass

def _preprocess_image(img_path: str, target_w: float, target_h: float) -> Optional[Image.Image]:
    if not img_path or not os.path.exists(img_path) or not os.path.isfile(img_path):
        return None
    try:
        pil_img = Image.open(img_path)
        # 1. EXIF orientation transposition correction
        pil_img = ImageOps.exif_transpose(pil_img).convert("RGB")
        
        # 2. Smart centered aspect ratio cropping to match bounding box perfectly
        orig_w, orig_h = pil_img.size
        target_aspect = target_w / target_h
        orig_aspect = orig_w / orig_h
        
        if abs(orig_aspect - target_aspect) > 0.01:
            if orig_aspect > target_aspect:
                # Image is too wide (landscape): crop left/right
                new_w = orig_h * target_aspect
                left = (orig_w - new_w) / 2
                pil_img = pil_img.crop((left, 0, left + new_w, orig_h))
            else:
                # Image is too tall: crop top/bottom
                new_h = orig_w / target_aspect
                top = (orig_h - new_h) / 2
                pil_img = pil_img.crop((0, top, orig_w, top + new_h))
        
        # 3. Smart anti-aliasing high-resolution scaling & compression optimization
        max_px_w = int(target_w * 4.0)
        max_px_h = int(target_h * 4.0)
        if pil_img.width > max_px_w or pil_img.height > max_px_h:
            pil_img = pil_img.resize((max_px_w, max_px_h), Image.Resampling.LANCZOS)
            
        return pil_img
    except Exception as e:
        logger.error(f"Image preprocessing failed for {img_path}: {e}")
        return None

def _save_temp_jpeg(pil_img: Image.Image) -> str:
    fd, path = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    pil_img.save(path, "JPEG", quality=90)
    return path

def _render_logo(canvas: canvas.Canvas, logo_path: Path) -> None:
    if logo_path and logo_path.exists() and logo_path.is_file() and logo_path.stat().st_size > 0:
        try:
            pil_logo = Image.open(logo_path)
            pil_logo = ImageOps.exif_transpose(pil_logo).convert("RGB")
            
            # Dynamic logo aspect-ratio fitting
            orig_w, orig_h = pil_logo.size
            scale = min(LOGO_RENDER_W / orig_w, LOGO_RENDER_H / orig_h)
            draw_w = orig_w * scale
            draw_h = orig_h * scale
            
            # Symmetrically center inside the protected header zone
            draw_x = LOGO_X + (LOGO_RENDER_W - draw_w) / 2
            draw_y = LOGO_DRAW_Y + (LOGO_RENDER_H - draw_h) / 2
            
            max_px_w = int(draw_w * 4.0)
            max_px_h = int(draw_h * 4.0)
            if pil_logo.width > max_px_w or pil_logo.height > max_px_h:
                pil_logo = pil_logo.resize((max_px_w, max_px_h), Image.Resampling.LANCZOS)
                
            tmp = _save_temp_jpeg(pil_logo)
            canvas.drawImage(
                tmp,
                draw_x,
                draw_y,
                width=draw_w,
                height=draw_h,
                preserveAspectRatio=False,
                mask="auto"
            )
            os.remove(tmp)
        except Exception as exc:
            logger.warning(f"Logo render failed: {exc} — using text fallback")
            _render_logo_fallback(canvas)
    else:
        logger.warning(f"Logo file not found or invalid at {logo_path} — using text fallback")
        _render_logo_fallback(canvas)

def _render_logo_fallback(canvas: canvas.Canvas) -> None:
    canvas.setFillColorRGB(*LOGO_FALLBACK_COLOR)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawCentredString(PAGE_WIDTH / 2, 785, "COST PLUS INC.")
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

    def _draw_scaled_string(self, canvas: canvas.Canvas, text: str, font: str, default_size: float, min_size: float, max_width: float, x: float, y: float, anchor: str = "left"):
        size = default_size
        while size >= min_size:
            if canvas.stringWidth(text, font, size) <= max_width:
                break
            size -= 0.5
        
        final_text = text
        if canvas.stringWidth(text, font, size) > max_width:
            final_text = self._truncate_text(canvas, text, font, size, max_width)
            
        canvas.setFont(font, size)
        if anchor == "center":
            canvas.drawCentredString(x, y, final_text)
        elif anchor == "right":
            canvas.drawRightString(x, y, final_text)
        else:
            canvas.drawString(x, y, final_text)

    def _draw_image_cell(self, c: canvas.Canvas, x: float, y: float, w: float, h: float, img_path: Optional[str]):
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h)
        
        inner_pad = 4
        ix, iy = x + inner_pad, y + inner_pad
        iw, ih = w - 2*inner_pad, h - 2*inner_pad
        
        pil_img = _preprocess_image(img_path, iw, ih) if img_path else None
        if pil_img:
            try:
                tmp = _save_temp_jpeg(pil_img)
                c.drawImage(tmp, ix, iy, iw, ih, preserveAspectRatio=False)
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

    def _get_fixed_total_records(self, ec: str) -> int:
        ec_clean = str(ec).upper().strip()
        # 1. COTABATO / COTELCO with PPALMA (check this first before general Cotabato)
        if "PPALMA" in ec_clean:
            return 2000
        # 2. COTABATO / COTELCO general
        elif "COTABATO" in ec_clean or "COTELCO" in ec_clean:
            return 2000
        # 3. ORIENTAL MINDORO / ORMECO
        elif "ORIENTAL MINDORO" in ec_clean or "ORMECO" in ec_clean:
            return 2000
        # 4. ALBAY / ALECO
        elif "ALBAY" in ec_clean or "ALECO" in ec_clean:
            return 1000
        # 5. LANAO DEL SUR / LASURECO
        elif "LANAO DEL SUR" in ec_clean or "LASURECO" in ec_clean:
            return 1000
        # 6. DAVAO DEL SUR / DASURECO
        elif "DAVAO DEL SUR" in ec_clean or "DASURECO" in ec_clean:
            return 1000
        # 7. LEYTE / LEYECO
        elif "LEYTE" in ec_clean or "LEYECO" in ec_clean:
            return 1000
        # 8. QUEZON / QUEZELCO
        elif "QUEZON" in ec_clean or "QUEZELCO" in ec_clean:
            return 1000
        # 9. FIRST BUKIDNON / FIBECO
        elif "FIRST BUKIDNON" in ec_clean or "FIBECO" in ec_clean:
            return 1000
        return 3000

    def generate(self, record, image_paths: Dict[int, str], output_folder: str, logo_path: str = "", total_records: int = 3000) -> str:
        safe_ias = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(record.ias_no))
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(record.name))
        output_filename = f"{safe_ias}_{safe_name}.pdf"
        
        final_path = Path(output_folder) / output_filename
        
        temp_dir = tempfile.mkdtemp()
        temp_pdf = Path(temp_dir) / output_filename
        
        logo = Path(logo_path) if logo_path else ASSETS_DIR / "logo" / "costplus_logo.png"
        if not logo.exists() or not logo.is_file():
            logo = ASSETS_DIR / "logo" / "costplus_logo.png"

        try:
            c = canvas.Canvas(str(temp_pdf), pagesize=(PAGE_WIDTH, PAGE_HEIGHT))
            
            # Map dynamic total records based on EC cooperative name mapping table
            fixed_total = self._get_fixed_total_records(record.ec)
            
            self._render_page1(c, record, image_paths)
            self._render_page2(c, record, image_paths, logo, fixed_total)
            self._render_page3(c, record, image_paths, logo)
            
            c.save()
            
            try:
                if final_path.exists():
                    os.remove(final_path)
                shutil.move(str(temp_pdf), str(final_path))
            except OSError as e:
                logger.info(f"File {final_path} is locked: {e}. Saving with a unique name.")
                timestamp = datetime.now().strftime("%H%M%S")
                output_filename = f"{safe_ias}_{safe_name}_{timestamp}.pdf"
                final_path = Path(output_folder) / output_filename
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
        
        pil_img = _preprocess_image(img_path, avail_w, avail_h) if img_path else None
        if pil_img:
            try:
                tmp = _save_temp_jpeg(pil_img)
                c.drawImage(tmp, margin, margin, avail_w, avail_h, preserveAspectRatio=False)
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

    def _render_page2(self, c: canvas.Canvas, record, image_paths, logo_path, total_records: int):
        c.setPageSize((PAGE_WIDTH, PAGE_HEIGHT))
        _render_logo(c, logo_path)
        
        y_cursor = 752.0  # Spacing below logo
        
        # 1. Dynamic Title Block (Outline Box Removed for Cleaner, Premium Layout)
        title_box_h = 48.0
        title_box_y = y_cursor - title_box_h
        
        c.setFont("Helvetica-Bold", 8.0)
        c.drawCentredString(297, title_box_y + 36, "SUPPLY, INSTALLATION, TESTING, AND COMMISSIONING OF SOLAR PV MAINSTREAMING FOR")
        
        ec_val = self._safe_str(record.ec).upper()
        self._draw_scaled_string(c, ec_val, "Helvetica-Bold", 9.0, 7.5, 468, 297, title_box_y + 24, "center")
        
        c.setFont("Helvetica-Bold", 8.0)
        c.drawCentredString(297, title_box_y + 12, f'"FRANCHISE AREA 2025-{total_records} PVM/SHS"')
        
        y_cursor = title_box_y - 10.0
        
        # 2. Beneficiary Info Block (Outline Box Removed as Requested)
        info_box_h = 56.0
        info_box_y = y_cursor - info_box_h
        
        c.setFont("Helvetica-Bold", 9)
        c.drawString(63, info_box_y + 44, "IAS NO.")
        c.drawString(63, info_box_y + 31, "NAME OF BENEFICIARY:")
        c.drawString(63, info_box_y + 18, "ADDRESS:")
        c.drawString(63, info_box_y + 5, "DATE OF INSTALLATION:")
        
        c.setFont("Helvetica", 9)
        # Shift values horizontally to align beautifully
        self._draw_scaled_string(c, self._safe_str(record.ias_no), "Helvetica", 9, 7.5, 320, 200, info_box_y + 44)
        self._draw_scaled_string(c, self._safe_str(record.name), "Helvetica", 9, 7.5, 320, 200, info_box_y + 31)
        self._draw_scaled_string(c, self._safe_str(record.full_address), "Helvetica", 9, 7.5, 320, 200, info_box_y + 18)
        self._draw_scaled_string(c, self._safe_str(record.date_installed), "Helvetica", 9, 7.5, 320, 200, info_box_y + 5)
        
        y_cursor = info_box_y - 8.0
        
        # 3. Unavailability Instruction Warning
        c.setFont("Helvetica", 7.5)
        c.drawString(63, y_cursor - 8, "In case of unavailability of registered beneficiary during installation and documentation,")
        c.drawString(63, y_cursor - 18, "please fill out the necessary information:")
        
        y_cursor = y_cursor - 22.0
        
        # 4. Representative Box (Outline Box Removed as Requested)
        rep_box_h = 24.0
        rep_box_y = y_cursor - rep_box_h
        
        c.setFont("Helvetica-Bold", 8.5)
        c.drawString(63, rep_box_y + 13, "NAME OF REPRESENTATIVE:")
        c.drawString(63, rep_box_y + 3, "RELATIONSHIP:")
        
        c.setFont("Helvetica", 8.5)
        self._draw_scaled_string(c, self._safe_str(record.representative_name), "Helvetica", 8.5, 7.5, 280, 210, rep_box_y + 13)
        self._draw_scaled_string(c, self._safe_str(record.relationship), "Helvetica", 8.5, 7.5, 280, 210, rep_box_y + 3)
        
        y_cursor = rep_box_y - 12.0
        
        # 5. Image cells (Taller Image cells set to 320.0 pt for signatures visibility)
        image_h = 320.0
        image_y = y_cursor - image_h
        
        self._draw_image_cell(c, 58, image_y, IMG_CELL_W, image_h, image_paths.get(1))
        self._draw_image_cell(c, 316, image_y, IMG_CELL_W, image_h, image_paths.get(2))
        
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(176.37, image_y - 10, "DULY ACCOMPLISHED IAS FORM")
        c.drawCentredString(434.37, image_y - 10, "GEOTAGGED PHOTO OF SOLAR PANEL W/BENEFICIARY")
        
        # 6. GPS Box under right image
        gps_box_h = 36.0
        gps_box_y = image_y - 54.0
        c.rect(316, gps_box_y, 236.74, gps_box_h)
        
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(320, gps_box_y + 25, "LONGITUDE:")
        c.drawString(320, gps_box_y + 15, "LATITUDE:")
        c.drawString(320, gps_box_y + 5, "DATE INSTALLED:")
        
        c.setFont("Helvetica", 7.5)
        self._draw_scaled_string(c, self._safe_str(record.longitude), "Helvetica", 7.5, 6.5, 150, 390, gps_box_y + 25)
        self._draw_scaled_string(c, self._safe_str(record.latitude), "Helvetica", 7.5, 6.5, 150, 390, gps_box_y + 15)
        self._draw_scaled_string(c, self._safe_str(record.date_installed), "Helvetica", 7.5, 6.5, 150, 405, gps_box_y + 5)
        
        c.showPage()

    def _render_page3(self, c: canvas.Canvas, record, image_paths, logo_path):
        c.setPageSize((PAGE_WIDTH, PAGE_HEIGHT))
        _render_logo(c, logo_path)
        
        # Redesigned 2x2 portrait layout (Image heights expanded to 265.0 pt)
        # Row 1 Cells
        self._draw_image_cell(c, 58, 475, IMG_CELL_W, 265, image_paths.get(3))
        self._draw_image_cell(c, 316, 475, IMG_CELL_W, 265, image_paths.get(4))
        
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(176.37, 460, "GEOTAGGED PHOTO OF SYSTEM BOX")
        c.drawCentredString(434.37, 460, "GEOTAGGED PHOTO OF LIGHTING FIXTURE")
        
        # Row 2 Cells
        self._draw_image_cell(c, 58, 110, IMG_CELL_W, 265, image_paths.get(5))
        self._draw_image_cell(c, 316, 110, IMG_CELL_W, 265, image_paths.get(6))
        
        c.setFont("Helvetica-Bold", 7.5)
        c.drawCentredString(176.37, 95, "GEOTAGGED PHOTO OF FLASHLIGHT & RADIO")
        c.drawCentredString(434.37, 95, "GEOTAGGED PHOTO OF RFID CARD")
        
        # Metadata rendering with Lessened separation gaps and Date overlap protection
        # VX has been moved further right to 175/435 specifically for DATE to prevent label overlap
        cells = [
            (62, 125, 175, 445),   # Row 1 Left:  (lx, vx, date_vx, y)
            (320, 383, 435, 445),  # Row 1 Right: (lx, vx, date_vx, y)
            (62, 125, 175, 80),    # Row 2 Left:  (lx, vx, date_vx, y)
            (320, 383, 435, 80)    # Row 2 Right: (lx, vx, date_vx, y)
        ]
        
        for lx, vx, date_vx, y in cells:
            c.setFont("Helvetica-Bold", 7.5)
            c.drawString(lx, y, "NAME:")
            c.drawString(lx, y - 10, "LONGITUDE:")
            c.drawString(lx, y - 20, "LATITUDE:")
            c.drawString(lx, y - 30, "DATE OF INSTALLATION:")
            
            c.setFont("Helvetica", 7.5)
            self._draw_scaled_string(c, self._safe_str(record.name), "Helvetica", 7.5, 6.0, 160, vx, y)
            self._draw_scaled_string(c, self._safe_str(record.longitude), "Helvetica", 7.5, 6.0, 160, vx, y - 10)
            self._draw_scaled_string(c, self._safe_str(record.latitude), "Helvetica", 7.5, 6.0, 160, vx, y - 20)
            # Use shifted date_vx to prevent overlapping with "DATE OF INSTALLATION:" label
            self._draw_scaled_string(c, self._safe_str(record.date_installed), "Helvetica", 7.5, 6.0, 110, date_vx, y - 30)
            
        c.showPage()
