from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
from pathlib import Path
from PIL import Image, ImageOps

class DragDropZone(QFrame):
    image_changed = Signal(str)

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.image_path = None
        
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumSize(180, 140)
        
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #0078D4;
                border-radius: 6px;
                background-color: palette(alternate-base);
            }
            QFrame:hover {
                border-color: #106EBE;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setAlignment(Qt.AlignCenter)
        
        self.lbl_thumbnail = QLabel()
        self.lbl_thumbnail.setAlignment(Qt.AlignCenter)
        self.lbl_thumbnail.setText(f"Drag & Drop Image\n{self.title}")
        self.lbl_thumbnail.setStyleSheet("font-size: 10px; color: #888888; border: none; background: transparent;")
        
        self.btn_browse = QPushButton("Select Image")
        self.btn_browse.setStyleSheet("font-size: 10px; padding: 2px 8px;")
        self.btn_browse.clicked.connect(self.browse_file)
        
        layout.addWidget(self.lbl_thumbnail, 1)
        layout.addWidget(self.btn_browse, 0, Qt.AlignCenter)
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("border: 2px dashed #106EBE; background-color: palette(base); border-radius: 6px;")
            
    def dragLeaveEvent(self, event):
        self.reset_style()
        
    def dropEvent(self, event):
        self.reset_style()
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.load_image_path(path)
            
    def reset_style(self):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #0078D4;
                border-radius: 6px;
                background-color: palette(alternate-base);
            }
        """)
        
    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, f"Select Image for {self.title}", "", 
            "Image Files (*.jpg *.jpeg *.png *.webp)"
        )
        if path:
            self.load_image_path(path)
            
    def load_image_path(self, path: str):
        if not path or not os.path.exists(path):
            return
            
        suffix = Path(path).suffix.lower()
        if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
            QMessageBox.critical(self, "Invalid Format", f"Format {suffix} is not supported.")
            return
            
        try:
            pil_img = Image.open(path)
            pil_img = ImageOps.exif_transpose(pil_img)
            
            aspect = pil_img.width / pil_img.height
            if aspect > 1:
                new_w = 160
                new_h = int(160 / aspect)
            else:
                new_h = 120
                new_w = int(120 * aspect)
                
            pil_img.thumbnail((new_w, new_h), Image.Resampling.LANCZOS)
            
            if pil_img.mode != "RGBA":
                pil_img = pil_img.convert("RGBA")
            data = pil_img.tobytes("raw", "RGBA")
            
            from PySide6.QtGui import QImage
            qim = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
            pix = QPixmap.fromImage(qim)
            
            self.lbl_thumbnail.setPixmap(pix)
            self.image_path = path
            self.image_changed.emit(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
