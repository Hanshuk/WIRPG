from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import fitz  # PyMuPDF
import logging

logger = logging.getLogger("CostPlusSolarDocs.pdf_viewer")

class PDFViewer(QWidget):
    """
    A widget that displays a PDF file using PyMuPDF.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        
        self.lbl_pdf = QLabel("No PDF to preview")
        self.lbl_pdf.setAlignment(Qt.AlignCenter)
        self.lbl_pdf.setStyleSheet("color: #888888; font-size: 16px;")
        
        self.scroll_area.setWidget(self.lbl_pdf)
        layout.addWidget(self.scroll_area)
        
        self.current_doc = None
        self.current_page_num = 0

    def load_pdf(self, pdf_path: str):
        if not pdf_path:
            self._clear()
            return
            
        try:
            self.current_doc = fitz.open(pdf_path)
            self.current_page_num = 0
            self._render_page()
        except Exception as e:
            logger.error(f"Failed to load PDF for preview: {e}")
            self.lbl_pdf.setText("Failed to load PDF preview")
            
    def _clear(self):
        if self.current_doc:
            self.current_doc.close()
            self.current_doc = None
        self.lbl_pdf.setText("No PDF to preview")
        self.lbl_pdf.setPixmap(QPixmap())

    def _render_page(self):
        if not self.current_doc: return
        try:
            page = self.current_doc.load_page(self.current_page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            
            fmt = QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888
            qim = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            self.lbl_pdf.setPixmap(QPixmap.fromImage(qim))
        except Exception as e:
            logger.error(f"Error rendering PDF page: {e}")
            self.lbl_pdf.setText("Error rendering page")
            
    def next_page(self):
        if self.current_doc and self.current_page_num < len(self.current_doc) - 1:
            self.current_page_num += 1
            self._render_page()
            
    def prev_page(self):
        if self.current_doc and self.current_page_num > 0:
            self.current_page_num -= 1
            self._render_page()
