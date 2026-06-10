import os
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QComboBox, QSpinBox, QDateEdit, 
                               QPushButton, QFileDialog, QSplitter,
                               QScrollArea, QFrame, QGridLayout)
from PySide6.QtCore import Qt, QDate, Signal, Slot
from PySide6.QtGui import QDoubleValidator
from db.database import db
from core.pdf_engine import PDFEngine
from core.validation_engine import ValidationEngine
from db.models import BeneficiaryRecord
from config.constants import DB_DIR
from ui.widgets.drag_drop_zone import DragDropZone

logger = logging.getLogger("CostPlusSolarDocs.manual_panel")

class ManualPanel(QWidget):
    fields_changed = Signal(dict, dict) # Emits record_data dict, image_paths dict
    show_banner = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.draft_path = DB_DIR / "manual_draft.json"
        self.slots: Dict[int, DragDropZone] = {}
        
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
        lbl_title.setToolTip("Fill out these fields to create a single PDF manually.")
        left_layout.addWidget(lbl_title)
        
        scroll_form = QScrollArea()
        scroll_form.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QVBoxLayout(scroll_widget)
        form_layout.setSpacing(8)
        
        # Init inputs
        self.txt_ias = self._add_field(form_layout, "IAS No. *", "Enter the unique IAS number.")
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
        ], "Select the cooperative.")
        self.txt_count = self._add_spin(form_layout, "Beneficiary Count *", 1, 100000, 2000, "Enter the number associated with this EC.")
        self.txt_name = self._add_field(form_layout, "Beneficiary Name *", "Enter the full name of the beneficiary.")
        
        self.txt_purok = self._add_field(form_layout, "Purok/Sitio", "Enter the Purok or Sitio.")
        self.txt_barangay = self._add_field(form_layout, "Barangay", "Enter the Barangay.")
        self.txt_municipality = self._add_field(form_layout, "Municipality", "Enter the Municipality.")
        
        self.txt_address = self._add_field(form_layout, "Full Address *", "The full composite address.")
        
        # Setup auto-composite
        self.txt_purok.textChanged.connect(self.auto_composite_address)
        self.txt_barangay.textChanged.connect(self.auto_composite_address)
        self.txt_municipality.textChanged.connect(self.auto_composite_address)
        
        self.txt_lon = self._add_field(form_layout, "Longitude *", "Must be a valid decimal number between -180 and 180.")
        self.txt_lon.textChanged.connect(self._validate_lon)
        self.txt_lat = self._add_field(form_layout, "Latitude *", "Must be a valid decimal number between -90 and 90.")
        self.txt_lat.textChanged.connect(self._validate_lat)
        
        self.txt_date = QDateEdit()
        self.txt_date.setCalendarPopup(True)
        self.txt_date.setDate(QDate.currentDate())
        self.txt_date.setDisplayFormat("MMMM dd, yyyy")
        self.txt_date.setToolTip("Select the date of installation.")
        self.txt_date.dateChanged.connect(self.on_changed)
        form_layout.addWidget(QLabel("Date Installed *"))
        form_layout.addWidget(self.txt_date)
        
        self.txt_sysbox = self._add_field(form_layout, "System Box S.N.", "Enter the System Box serial number.")
        self.txt_solar = self._add_field(form_layout, "Solar Panel S.N.", "Enter the Solar Panel serial number.")
        self.txt_rep = self._add_field(form_layout, "Representative Name", "Name of the person representing the beneficiary.")
        self.txt_rel = self._add_field(form_layout, "Relationship", "Relationship of the representative to the beneficiary.")
        
        scroll_form.setWidget(scroll_widget)
        left_layout.addWidget(scroll_form)
        
        # Generate & Action Buttons
        lyt_actions = QHBoxLayout()
        btn_clear = QPushButton("Clear Form")
        btn_clear.setToolTip("Clear all fields and photos to start fresh.")
        btn_clear.clicked.connect(self.clear_form)
        
        self.btn_generate = QPushButton("Generate PDF")
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; color: white; font-weight: bold; padding: 8px; border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #555555; color: #aaaaaa;
            }
        """)
        self.btn_generate.setToolTip("Please fill in all required fields and upload at least Slot 1 and Slot 2 photos.")
        self.btn_generate.setEnabled(False)
        self.btn_generate.clicked.connect(self.generate_manual_pdf)
        
        lyt_actions.addWidget(btn_clear)
        lyt_actions.addWidget(self.btn_generate)
        left_layout.addLayout(lyt_actions)
        
        # Right Panel (6 Image Slots Grid)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        lbl_images = QLabel("Geotagged Photo Documentation")
        lbl_images.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 5px;")
        lbl_images.setToolTip("Drag and drop photos for each required slot.")
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
            slot = DragDropZone(f"Slot {slot_num}: {title}")
            # Bind the slot number to the lambda
            slot.image_changed.connect(lambda path, s=slot_num: self._handle_image_changed(s, path))
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

    def _add_field(self, layout, label_text: str, tooltip: str) -> QLineEdit:
        lbl = QLabel(label_text)
        txt = QLineEdit()
        txt.setToolTip(tooltip)
        txt.textChanged.connect(self.on_changed)
        layout.addWidget(lbl)
        layout.addWidget(txt)
        return txt
        
    def _add_combo(self, layout, label_text: str, items: list, tooltip: str) -> QComboBox:
        lbl = QLabel(label_text)
        cmb = QComboBox()
        cmb.setToolTip(tooltip)
        cmb.addItems(items)
        cmb.currentTextChanged.connect(self.on_changed)
        layout.addWidget(lbl)
        layout.addWidget(cmb)
        return cmb
        
    def _add_spin(self, layout, label_text: str, min_v: int, max_v: int, val: int, tooltip: str) -> QSpinBox:
        lbl = QLabel(label_text)
        spin = QSpinBox()
        spin.setToolTip(tooltip)
        spin.setRange(min_v, max_v)
        spin.setValue(val)
        spin.valueChanged.connect(self.on_changed)
        layout.addWidget(lbl)
        layout.addWidget(spin)
        return spin
        
    def _validate_lon(self, text):
        try:
            val = float(text)
            if -180.0 <= val <= 180.0:
                self.txt_lon.setStyleSheet("")
            else:
                self.txt_lon.setStyleSheet("border: 1px solid #E81123;")
        except ValueError:
            if text: self.txt_lon.setStyleSheet("border: 1px solid #E81123;")
            else: self.txt_lon.setStyleSheet("")
        self.on_changed()

    def _validate_lat(self, text):
        try:
            val = float(text)
            if -90.0 <= val <= 90.0:
                self.txt_lat.setStyleSheet("")
            else:
                self.txt_lat.setStyleSheet("border: 1px solid #E81123;")
        except ValueError:
            if text: self.txt_lat.setStyleSheet("border: 1px solid #E81123;")
            else: self.txt_lat.setStyleSheet("")
        self.on_changed()

    def _handle_image_changed(self, slot_num, path):
        self.on_changed()

    def auto_composite_address(self):
        purok = self.txt_purok.text().strip()
        barangay = self.txt_barangay.text().strip()
        mun = self.txt_municipality.text().strip()
        parts = [p for p in [purok, barangay, mun] if p]
        self.txt_address.setText(", ".join(parts))

    def on_changed(self, *args):
        # Auto save draft
        self.save_draft()
        
        record_data = self.get_record_data()
        image_paths = {k: v.image_path for k, v in self.slots.items() if v.image_path}
        
        # Check requirements to enable/disable Generate button
        required_fields_filled = bool(
            record_data["ias_no"] and record_data["name"] and record_data["full_address"] and
            record_data["longitude"] and record_data["latitude"] and record_data["date_installed"]
        )
        required_images_filled = bool(image_paths.get(1) and image_paths.get(2))
        
        try:
            float(record_data["longitude"])
            float(record_data["latitude"])
            coords_valid = True
        except:
            coords_valid = False
            
        if required_fields_filled and required_images_filled and coords_valid:
            self.btn_generate.setEnabled(True)
            self.btn_generate.setToolTip("Ready to generate PDF!")
        else:
            self.btn_generate.setEnabled(False)
            self.btn_generate.setToolTip("Please fill in all required fields (including valid coordinates) and upload at least Slot 1 and Slot 2 photos.")
            
        # Emit signal for live preview updates
        self.fields_changed.emit(record_data, image_paths)

    def get_record_data(self) -> dict:
        return {
            "excel_row": 9999,
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
            slot.lbl_thumbnail.clear()
            slot.image_path = None
            slot.lbl_thumbnail.setText(f"Drag & Drop Image\n{slot.title}")
            slot.btn_browse.setText("Select Image")
            
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
                
        self.on_changed()

    def generate_manual_pdf(self):
        record_data = self.get_record_data()
        val = ValidationEngine.validate_record_fields(record_data)
        if not val.is_valid:
            self.show_banner.emit("error", "Cannot generate PDF due to formatting errors.")
            return
            
        image_paths = {k: v.image_path for k, v in self.slots.items() if v.image_path}
        
        out_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder for PDF")
        if not out_folder:
            return
            
        try:
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
                latitude=record_data["latitude"],
                system_box_sn=record_data["system_box_sn"],
                solar_panel_sn=record_data["solar_panel_sn"]
            )
            
            engine = PDFEngine()
            final_path = engine.generate(record, image_paths, out_folder)
            
            from core.validation_engine import PDFValidator
            val_res = PDFValidator.validate(final_path)
            if not val_res.is_valid:
                raise Exception("Generated PDF failed structural verification.")
                
            self.show_banner.emit("success", f"Successfully generated PDF: {final_path}")
            self.clear_form()
            
        except Exception as e:
            self.show_banner.emit("error", f"Failed to generate PDF: {e}")
