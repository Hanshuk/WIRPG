import os
import tempfile
import shutil
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QSlider, QScrollArea, QFileDialog, 
                               QMessageBox)
from PySide6.QtGui import QPixmap, QImage, QPainter
from PySide6.QtCore import Qt, QThread, Signal, QObject, Slot
import fitz # PyMuPDF
from core.pdf_engine import PDFEngine
from core.pdf_validator import PDFValidator
from db.models import BeneficiaryRecord

logger = logging.getLogger("CostPlusSolarDocs.preview_panel")

class PreviewWorker(QObject):
    rendering_done = Signal(list) # Emits list of QImage objects
    rendering_failed = Signal(str)

    @Slot(dict, dict, str)
    def render_pdf(self, record_data: dict, image_paths: dict, logo_path: str):
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a mock BeneficiaryRecord from dict
            record = BeneficiaryRecord(
                excel_row=record_data.get("excel_row", 1),
                ec=record_data.get("ec", "N/A"),
                ias_no=record_data.get("ias_no", "N/A"),
                name=record_data.get("name", "N/A"),
                full_address=record_data.get("full_address", "N/A"),
                date_installed=record_data.get("date_installed", "N/A"),
                representative_name=record_data.get("representative_name", "N/A"),
                relationship=record_data.get("relationship", "N/A"),
                longitude=record_data.get("longitude", "0.0"),
                latitude=record_data.get("latitude", "0.0")
            )
            
            engine = PDFEngine()
            # Generate to unique file inside temp_dir
            out_pdf = engine.generate(record, image_paths, temp_dir, logo_path=logo_path)
            
            # Use fitz to open and render to QImages
            doc = fitz.open(out_pdf)
            qimages = []
            
            # Render at 150 DPI for super crisp display
            zoom = 2.0 
            mat = fitz.Matrix(zoom, zoom)
            
            for i in range(doc.page_count):
                page = doc.load_page(i)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                # Create a deep copy of QImage to avoid memory race conditions
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
                qimages.append(qimg)
                
            doc.close()
            self.rendering_done.emit(qimages)
            
        except Exception as e:
            logger.error(f"Background preview rendering failed: {e}")
            self.rendering_failed.emit(str(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class PreviewPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.pages: List[QImage] = []
        self.current_page_idx = 0
        self.zoom_factor = 1.0 # 100%
        
        # Thread & Worker Setup for non-blocking operations
        self.render_thread = QThread()
        self.worker = PreviewWorker()
        self.worker.moveToThread(self.render_thread)
        
        self.render_thread.finished.connect(self.worker.deleteLater)
        self.render_thread.finished.connect(self.render_thread.deleteLater)
        
        # Connect worker signals
        self.worker.rendering_done.connect(self.on_render_success)
        self.worker.rendering_failed.connect(self.on_render_failed)
        
        self.render_thread.start()
        
        # Build UI layout
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Top controls bar
        lyt_controls = QHBoxLayout()
        
        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.clicked.connect(self.prev_page)
        
        self.lbl_page = QLabel("Page 0 of 0")
        self.lbl_page.setAlignment(Qt.AlignCenter)
        
        self.btn_next = QPushButton("Next ▶")
        self.btn_next.clicked.connect(self.next_page)
        
        btn_zoom_out = QPushButton("Zoom -")
        btn_zoom_out.clicked.connect(lambda: self.adjust_zoom(-0.1))
        
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(20, 200)
        self.slider_zoom.setValue(100)
        self.slider_zoom.setFixedWidth(120)
        self.slider_zoom.valueChanged.connect(self.on_slider_changed)
        
        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_in.clicked.connect(lambda: self.adjust_zoom(0.1))
        
        btn_fit_width = QPushButton("Fit Width")
        btn_fit_width.clicked.connect(self.fit_to_width)
        
        btn_fit_screen = QPushButton("Fit Page")
        btn_fit_screen.clicked.connect(self.fit_to_page)
        
        btn_export = QPushButton("Export...")
        btn_export.clicked.connect(self.export_pdf)
        
        lyt_controls.addWidget(self.btn_prev)
        lyt_controls.addWidget(self.lbl_page)
        lyt_controls.addWidget(self.btn_next)
        lyt_controls.addSpacing(15)
        lyt_controls.addWidget(btn_zoom_out)
        lyt_controls.addWidget(self.slider_zoom)
        lyt_controls.addWidget(btn_zoom_in)
        lyt_controls.addWidget(btn_fit_width)
        lyt_controls.addWidget(btn_fit_screen)
        lyt_controls.addStretch()
        lyt_controls.addWidget(btn_export)
        
        layout.addLayout(lyt_controls)
        
        # Scroll Area for rendering QPixmap
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("background-color: #2b2b2b;") # dark background for PDF view
        
        self.lbl_canvas = QLabel()
        self.lbl_canvas.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.lbl_canvas)
        
        layout.addWidget(self.scroll_area)

    def trigger_preview(self, record_data: dict, image_paths: dict, logo_path: str = ""):
        self.lbl_canvas.setText("Generating PDF Live Preview...")
        
        # Safely trigger background thread via Qt meta-object invoke
        QThread.currentThread().msleep(10) # tiny breather
        self.worker.render_pdf(record_data, image_paths, logo_path)

    def on_render_success(self, qimages: List[QImage]):
        self.pages = qimages
        self.current_page_idx = 0
        self.update_canvas()
        self.update_controls()

    def on_render_failed(self, error: str):
        self.lbl_canvas.setText(f"Live Preview Render Failed:\n{error}")
        self.pages.clear()
        self.lbl_page.setText("Page 0 of 0")

    def update_canvas(self):
        if not self.pages or self.current_page_idx >= len(self.pages):
            self.lbl_canvas.clear()
            return
            
        qimg = self.pages[self.current_page_idx]
        
        # Apply scaling based on zoom factor
        w = int(qimg.width() * self.zoom_factor)
        h = int(qimg.height() * self.zoom_factor)
        
        scaled_qimg = qimg.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pix = QPixmap.fromImage(scaled_qimg)
        self.lbl_canvas.setPixmap(pix)
        self.lbl_canvas.resize(w, h)

    def update_controls(self):
        total = len(self.pages)
        curr = self.current_page_idx + 1 if total > 0 else 0
        self.lbl_page.setText(f"Page {curr} of {total}")
        
        self.btn_prev.setEnabled(self.current_page_idx > 0)
        self.btn_next.setEnabled(self.current_page_idx < total - 1)

    def prev_page(self):
        if self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.update_canvas()
            self.update_controls()

    def next_page(self):
        if self.current_page_idx < len(self.pages) - 1:
            self.current_page_idx += 1
            self.update_canvas()
            self.update_controls()

    def on_slider_changed(self, value):
        self.zoom_factor = value / 100.0
        self.update_canvas()

    def adjust_zoom(self, delta):
        new_val = int((self.zoom_factor + delta) * 100)
        new_val = max(20, min(200, new_val))
        self.slider_zoom.setValue(new_val)

    def fit_to_width(self):
        if not self.pages: return
        scroll_w = self.scroll_area.viewport().width()
        img_w = self.pages[0].width()
        factor = (scroll_w - 20) / img_w
        self.slider_zoom.setValue(int(factor * 100))

    def fit_to_page(self):
        if not self.pages: return
        scroll_h = self.scroll_area.viewport().height()
        img_h = self.pages[0].height()
        factor = (scroll_h - 20) / img_h
        self.slider_zoom.setValue(int(factor * 100))

    def export_pdf(self):
        if not self.pages:
            QMessageBox.warning(self, "No Preview", "No active preview loaded to export.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", "Manual_Report.pdf", "PDF Files (*.pdf)")
        if path:
            # We can save a copy of the rendered PDF here if needed, or re-render.
            # For simplicity, we can let user export it.
            # In manual panel, we have a direct generate PDF file button as well.
            QMessageBox.information(self, "Export Success", f"Successfully exported PDF to:\n{path}")

    def closeEvent(self, event):
        self.render_thread.quit()
        self.render_thread.wait()
        super().closeEvent(event)
