import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QSpinBox, QDateEdit, 
                               QPushButton, QFileDialog, QMessageBox, QSplitter,
                               QScrollArea, QFrame, QGridLayout)
from PySide6.QtCore import Qt, QDate, Signal, Slot
from PySide6.QtGui import QDoubleValidator, QPixmap
from db.database import db
from core.pdf_engine import PDFEngine
from core.validation_engine import ValidationEngine
from config.constants import DB_DIR

logger = logging.getLogger("CostPlusSolarDocs.manual_panel")

class ImageUploadSlot(QFrame):
    image_changed = Signal(int, str) # slot_num, path

    def __init__(self, slot_num: int, title: str):
        super().__init__()
        self.slot_num = slot_num
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
        self.lbl_thumbnail.setText(f"Drag & Drop Image\nSlot {self.slot_num}\n{self.title}")
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
            self, f"Select Image for Slot {self.slot_num}", "", 
            "Image Files (*.jpg *.jpeg *.png *.webp)"
        )
        if path:
            self.load_image_path(path)
            
    def load_image_path(self, path: str):
        if not path or not os.path.exists(path):
            return
            
        suffix = Path(path).suffix.lower()
        if suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
            QMessageBox.critical(self, "Invalid Format", f"Format {suffix} is not supported. Please upload JPG, JPEG, PNG, or WEBP.")
            return
            
        try:
            from PIL import Image
            with Image.open(path) as img:
                img.verify()
                
            self.image_path = path
            pix = QPixmap(path)
            scaled = pix.scaled(150, 95, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_thumbnail.setPixmap(scaled)
            self.btn_browse.setText("Replace")
            self.image_changed.emit(self.slot_num, path)
        except Exception as e:
            QMessageBox.critical(self, "Corrupted Image", f"Failed to load image. It may be corrupted:\n{e}")

    def clear_slot(self):
        self.image_path = None
        self.lbl_thumbnail.clear()
        self.lbl_thumbnail.setText(f"Drag & Drop Image\nSlot {self.slot_num}\n{self.title}")
        self.btn_browse.setText("Select Image")
        self.image_changed.emit(self.slot_num, "")


class ManualPanel(QWidget):
    fields_changed = Signal(dict, dict) # Emits record_data dict, image_paths dict

    def __init__(self):
        super().__init__()
        self.draft_path = DB_DIR / "manual_draft.json"
        self.slots: Dict[int, ImageUploadSlot] = {}
        
        # Main Splitter Layout for premium spacing control
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left Panel (Fields Scrollable Grid Form)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_title = QLabel("Manual Data Entry Form")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        left_layout.addWidget(lbl_title)
        
        scroll_form = QScrollArea()
        scroll_form.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setSpacing(8)
        
        # Init inputs
        self.txt_ias = self._add_field(form_layout, "IAS No. *")
        self.cmb_ec = self._add_combo(form_layout, "EC Number *", [
            "ORIENTAL MINDORO ELECTRIC COOPERATIVE, INC.",
            "ALBAY ELECTRIC COOPERATIVE, INC.",
            "COTABATO ELECTRIC COOPERATIVE, INC.",
            "LANAO DEL SUR ELECTRIC COOPERATIVE, INC.",
            "COTABATO ELECTRIC COOPERATIVE, INC. - PPALMA",
            "DAVAO DEL SUR ELECTRIC COOPERATIVE, INC.",
            "LEYTE ELECTRIC COOPERATIVE, INC.",
            "QUEZON ELECTRIC COOPERATIVE, INC.",
            "FIRST BUKIDNON ELECTRIC COOPERATIVE, INC."
        ])
        self.txt_count = self._add_spin(form_layout, "Beneficiary Count *", 1, 100000, 2000)
        self.txt_name = self._add_field(form_layout, "Beneficiary Name *")
        
        self.txt_purok = self._add_field(form_layout, "Purok/Sitio")
        self.txt_barangay = self._add_field(form_layout, "Barangay")
        self.txt_municipality = self._add_field(form_layout, "Municipality")
        
        self.txt_address = self._add_field(form_layout, "Full Address *")
        
        # Setup auto-composite
        self.txt_purok.textChanged.connect(self.auto_composite_address)
        self.txt_barangay.textChanged.connect(self.auto_composite_address)
        self.txt_municipality.textChanged.connect(self.auto_composite_address)
        
        self.txt_lon = self._add_field(form_layout, "Longitude *")
        self.txt_lon.setValidator(QDoubleValidator(-180.0, 180.0, 7))
        self.txt_lat = self._add_field(form_layout, "Latitude *")
        self.txt_lat.setValidator(QDoubleValidator(-90.0, 90.0, 7))
        
        self.txt_date = QDateEdit()
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDate(QDate.currentDate())
        self.txt_date.setDisplayFormat("MMMM dd, yyyy")
        self.txt_date.dateChanged.connect(self.on_changed)
        form_layout.addWidget(QLabel("Date Installed *"))
        form_layout.addWidget(self.txt_date)
        
        self.txt_sysbox = self._add_field(form_layout, "System Box S.N.")
        self.txt_solar = self._add_field(form_layout, "Solar Panel S.N.")
        self.txt_rep = self._add_field(form_layout, "Representative Name")
        self.txt_rel = self._add_field(form_layout, "Relationship")
        
        scroll_form.setWidget(scroll_widget)
        left_layout.addWidget(scroll_form)
        
        # Generate & Action Buttons
        lyt_actions = QHBoxLayout()
        btn_clear = QPushButton("Clear Form")
        btn_clear.clicked.connect(self.clear_form)
        
        btn_generate = QPushButton("Generate PDF")
        btn_generate.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold;")
        btn_generate.clicked.connect(self.generate_manual_pdf)
        
        lyt_actions.addWidget(btn_clear)
        lyt_actions.addWidget(btn_generate)
        left_layout.addLayout(lyt_actions)
        
        # Right Panel (6 Image Slots Grid)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_images = QLabel("Geotagged Photo Documentation")
        lbl_images.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        right_layout.addWidget(lbl_images)
        
        grid_images = QGridLayout()
        grid_images.setSpacing(10)
        
        image_titles = {
            1: "Beneficiary / IAS Form",
            2: "Solar Panel with Beneficiary",
            3: "System Box",
            4: "Lighting Fixture",
            5: "Flashlight & Radio",
            6: "RFID Card"
        }
        
        for slot_num, title in image_titles.items():
            slot = ImageUploadSlot(slot_num, title)
            slot.image_changed.connect(self.on_changed)
            self.slots[slot_num] = slot
            
            row = (slot_num - 1) // 2
            col = (slot_num - 1) % 2
            grid_images.addWidget(slot, row, col)
            
        right_layout.addLayout(grid_images)
        right_layout.addStretch()
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([450, 550])
        
        # Restore saved draft if exists
        self.restore_draft()

    def _add_field(self, layout, label_text: str) -> QLineEdit:
        lbl = QLabel(label_text)
        txt = QLineEdit()
        txt.textChanged.connect(self.on_changed)
        layout.addWidget(lbl)
        layout.addWidget(txt)
        return txt
        
    def _add_combo(self, layout, label_text: str, items: list) -> QComboBox:
        lbl = QLabel(label_text)
        cmb = QComboBox()
        cmb.addItems(items)
        cmb.currentTextChanged.connect(self.on_changed)
        layout.addWidget(lbl)
        layout.addWidget(cmb)
        return cmb
        
    def _add_spin(self, layout, label_text: str, min_v: int, max_v: int, val: int) -> QSpinBox:
        lbl = QLabel(label_text)
        spin = QSpinBox()
        spin.setRange(min_v, max_v)
        spin.setValue(val)
        spin.valueChanged.connect(self.on_changed)
        layout.addWidget(lbl)
        layout.addWidget(spin)
        return spin

    def auto_composite_address(self):
        purok = self.txt_purok.text().strip()
        barangay = self.txt_barangay.text().strip()
        mun = self.txt_municipality.text().strip()
        parts = [p for p in [purok, barangay, mun] if p]
        self.txt_address.setText(", ".join(parts))

    def on_changed(self, *args):
        # Auto save draft
        self.save_draft()
        
        # Emit signal for live preview updates
        record_data = self.get_record_data()
        image_paths = {k: v.image_path for k, v in self.slots.items() if v.image_path}
        self.fields_changed.emit(record_data, image_paths)

    def get_record_data(self) -> dict:
        return {
            "excel_row": 9999, # Manual Mode signifier
            "ec": self.cmb_ec.currentText(),
            "ias_no": self.txt_ias.text().strip(),
            "name": self.txt_name.text().strip(),
            "full_address": self.txt_address.text().strip(),
            "purok": self.txt_purok.text().strip(),
            "barangay": self.txt_barangay.text().strip(),
            "municipality": self.txt_municipality.text().strip(),
            "longitude": self.txt_lon.text().strip(),
            "latitude": self.txt_lat.text().strip(),
            "date_installed": self.txt_date.text().strip(),
            "system_box_sn": self.txt_sysbox.text().strip(),
            "solar_panel_sn": self.txt_solar.text().strip(),
            "representative_name": self.txt_rep.text().strip() or "N/A",
            "relationship": self.txt_rel.text().strip() or "N/A"
        }

    def save_draft(self):
        try:
            data = {
                "fields": self.get_record_data(),
                "images": {k: v.image_path for k, v in self.slots.items() if v.image_path}
            }
            # Atomic autosave
            tmp_path = str(self.draft_path) + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(tmp_path, str(self.draft_path))
        except Exception as e:
            logger.error(f"Failed to auto-save manual draft: {e}")

    def restore_draft(self):
        if not self.draft_path.exists():
            return
        try:
            with open(self.draft_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            fields = data.get("fields", {})
            self._set_ec_combobox(fields.get("ec", ""))
            self.txt_ias.setText(fields.get("ias_no", ""))
            self.txt_name.setText(fields.get("name", ""))
            self.txt_purok.setText(fields.get("purok", ""))
            self.txt_barangay.setText(fields.get("barangay", ""))
            self.txt_municipality.setText(fields.get("municipality", ""))
            self.txt_address.setText(fields.get("full_address", ""))
            self.txt_lon.setText(fields.get("longitude", ""))
            self.txt_lat.setText(fields.get("latitude", ""))
            self.txt_sysbox.setText(fields.get("system_box_sn", ""))
            self.txt_solar.setText(fields.get("solar_panel_sn", ""))
            self.txt_rep.setText(fields.get("representative_name", ""))
            self.txt_rel.setText(fields.get("relationship", ""))
            
            dt = fields.get("date_installed", "")
            if dt:
                qdt = QDate.fromString(dt, "MMMM dd, yyyy")
                if qdt.isValid():
                    self.txt_date.setDate(qdt)
                    
            images = data.get("images", {})
            for k, path in images.items():
                slot_num = int(k)
                if slot_num in self.slots and path:
                    self.slots[slot_num].load_image_path(path)
                    
        except Exception as e:
            logger.error(f"Failed to restore manual draft: {e}")

    def clear_form(self):
        self.txt_ias.clear()
        self.txt_name.clear()
        self.txt_purok.clear()
        self.txt_barangay.clear()
        self.txt_municipality.clear()
        self.txt_address.clear()
        self.txt_lon.clear()
        self.txt_lat.clear()
        self.txt_sysbox.clear()
        self.txt_solar.clear()
        self.txt_rep.clear()
        self.txt_rel.clear()
        self.txt_date.setDate(QDate.currentDate())
        
        for slot in self.slots.values():
            slot.clear_slot()
            
        if self.draft_path.exists():
            try:
                os.remove(self.draft_path)
            except OSError:
                pass
        self.on_changed()

    def _set_ec_combobox(self, ec_value: str):
        ec_clean = str(ec_value).upper().strip()
        mapped = None
        if "ORMECO" in ec_clean or "ORIENTAL MINDORO" in ec_clean:
            mapped = "ORIENTAL MINDORO ELECTRIC COOPERATIVE, INC."
        elif "ALECO" in ec_clean or "ALBAY" in ec_clean:
            mapped = "ALBAY ELECTRIC COOPERATIVE, INC."
        elif "COTELCO PPALMA" in ec_clean or "COTABATO ELECTRIC COOPERATIVE, INC. - PPALMA" in ec_clean:
            mapped = "COTABATO ELECTRIC COOPERATIVE, INC. - PPALMA"
        elif "COTELCO" in ec_clean or "COTABATO" in ec_clean:
            mapped = "COTABATO ELECTRIC COOPERATIVE, INC."
        elif "LASURECO" in ec_clean or "LANAO DEL SUR" in ec_clean:
            mapped = "LANAO DEL SUR ELECTRIC COOPERATIVE, INC."
        elif "DASURECO" in ec_clean or "DAVAO DEL SUR" in ec_clean:
            mapped = "DAVAO DEL SUR ELECTRIC COOPERATIVE, INC."
        elif "LEYECO" in ec_clean or "LEYTE" in ec_clean:
            mapped = "LEYTE ELECTRIC COOPERATIVE, INC."
        elif "QUEZELCO" in ec_clean or "QUEZON" in ec_clean:
            mapped = "QUEZON ELECTRIC COOPERATIVE, INC."
        elif "FIBECO" in ec_clean or "FIRST BUKIDNON" in ec_clean:
            mapped = "FIRST BUKIDNON ELECTRIC COOPERATIVE, INC."
            
        if mapped:
            self.cmb_ec.setCurrentText(mapped)
        else:
            self.cmb_ec.setCurrentText("ORIENTAL MINDORO ELECTRIC COOPERATIVE, INC.")

    def load_record(self, record_dict: dict):
        self._set_ec_combobox(record_dict.get("ec", ""))
        self.txt_ias.setText(record_dict.get("ias_no", ""))
        self.txt_name.setText(record_dict.get("name", ""))
        self.txt_address.setText(record_dict.get("full_address", ""))
        self.txt_lon.setText(record_dict.get("longitude", ""))
        self.txt_lat.setText(record_dict.get("latitude", ""))
        self.txt_sysbox.setText(record_dict.get("system_box_sn", ""))
        self.txt_solar.setText(record_dict.get("solar_panel_sn", ""))
        self.txt_rep.setText(record_dict.get("representative_name", ""))
        self.txt_rel.setText(record_dict.get("relationship", ""))
        
        # Extract Purok/Sitio etc if formatted as comma separated
        address = record_dict.get("full_address", "")
        parts = [p.strip() for p in address.split(",")]
        if len(parts) >= 3:
            self.txt_purok.setText(parts[0])
            self.txt_barangay.setText(parts[1])
            self.txt_municipality.setText(", ".join(parts[2:]))
            
        dt = record_dict.get("date_installed", "")
        if dt:
            qdt = QDate.fromString(dt, "MMMM dd, yyyy")
            if qdt.isValid():
                self.txt_date.setDate(qdt)
                
        # Fuzzy match folder in standard assets and auto-load if available
        # But for inline correction, user will drag and drop the corrected image
        self.on_changed()

    def generate_manual_pdf(self):
        record_data = self.get_record_data()
        val = ValidationEngine.validate_record_fields(record_data)
        if not val.is_valid:
            QMessageBox.critical(self, "Validation Failed", 
                                 f"Cannot generate PDF due to formatting errors:\n- " + "\n- ".join(val.errors))
            return
            
        image_paths = {k: v.image_path for k, v in self.slots.items() if v.image_path}
        
        # Verify slot 1 & 2 are uploaded as they are absolutely critical for Page 2
        if not image_paths.get(1) or not image_paths.get(2):
            QMessageBox.warning(self, "Missing Photos", 
                                "Slot 1 (IAS Form) and Slot 2 (Solar Panel Photo) are mandatory for layout rendering.")
            return

        out_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder for PDF")
        if not out_folder:
            return
            
        try:
            # Create a full record
            record = BeneficiaryRecord(
                excel_row=9999,
                ec=record_data["ec"],
                ias_no=record_data["ias_no"],
                name=record_data["name"],
                full_address=record_data["full_address"],
                date_installed=record_data["date_installed"],
                representative_name=record_data["representative_name"],
                relationship=record_data["relationship"],
                longitude=record_data["longitude"],
                latitude=record_data["latitude"]
            )
            
            engine = PDFEngine()
            final_path = engine.generate(record, image_paths, out_folder)
            
            val_res = PDFValidator.validate(final_path)
            if not val_res.is_valid:
                raise Exception(f"Generated PDF failed structural verification: {', '.join(val_res.errors)}")
                
            QMessageBox.information(self, "PDF Generated", 
                                    f"Successfully generated whitelabeled ReportLab PDF:\n{final_path}")
            
            # Reset draft since we exported successfully
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(self, "Generation Failed", f"Failed to compile ReportLab PDF:\n{e}")
