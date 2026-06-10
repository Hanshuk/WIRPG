import os
import pandas as pd
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from core.batch_processor import BatchProcessor

class StepWidget(QFrame):
    def __init__(self, step_num, title, tooltip):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: palette(alternate-base);
                border-radius: 8px;
                border: 1px solid #333333;
            }
        """)
        self.setToolTip(tooltip)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        h_title = QHBoxLayout()
        self.lbl_step = QLabel(f"Step {step_num}: {title}")
        self.lbl_step.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.lbl_check = QLabel("")
        self.lbl_check.setStyleSheet("color: #107C10; font-weight: bold; font-size: 16px;")
        self.lbl_check.hide()
        
        h_title.addWidget(self.lbl_step)
        h_title.addStretch()
        h_title.addWidget(self.lbl_check)
        self.layout.addLayout(h_title)
        
        h_input = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.txt_path.setReadOnly(True)
        self.txt_path.setStyleSheet("padding: 5px; border-radius: 4px; background-color: palette(base);")
        
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setCursor(Qt.PointingHandCursor)
        self.btn_browse.setStyleSheet("padding: 5px 15px; background-color: #333333; color: white; border-radius: 4px;")
        
        h_input.addWidget(self.txt_path)
        h_input.addWidget(self.btn_browse)
        self.layout.addLayout(h_input)
        
        self.lbl_validation = QLabel("")
        self.lbl_validation.setStyleSheet("font-size: 12px; color: #888888;")
        self.layout.addWidget(self.lbl_validation)
        
    def set_enabled(self, enabled: bool):
        self.txt_path.setEnabled(enabled)
        self.btn_browse.setEnabled(enabled)
        self.lbl_step.setStyleSheet("font-weight: bold; font-size: 14px;" + ("" if enabled else "color: #666666;"))
        if not enabled:
            self.lbl_validation.setText("")
            self.lbl_check.hide()

    def set_validation(self, is_valid: bool, msg: str):
        self.lbl_validation.setText(msg)
        if is_valid:
            self.lbl_validation.setStyleSheet("font-size: 12px; color: #107C10;")
            self.lbl_check.setText("✓")
            self.lbl_check.show()
            self.setStyleSheet("""
                QFrame {
                    background-color: palette(alternate-base);
                    border-radius: 8px;
                    border: 1px solid #107C10;
                }
            """)
        else:
            self.lbl_validation.setStyleSheet("font-size: 12px; color: #E81123;")
            self.lbl_check.setText("X")
            self.lbl_check.setStyleSheet("color: #E81123; font-weight: bold; font-size: 16px;")
            self.lbl_check.show()
            self.setStyleSheet("""
                QFrame {
                    background-color: palette(alternate-base);
                    border-radius: 8px;
                    border: 1px solid #E81123;
                }
            """)


class BatchPanel(QWidget):
    batch_started = Signal()
    show_banner = Signal(str, str)
    
    def __init__(self):
        super().__init__()
        self.processor = BatchProcessor(num_workers=4)
        self.processor.batch_progress.connect(self.update_progress)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        lbl_title = QLabel("Start a New Batch")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold;")
        lbl_title.setToolTip("Follow the 3 steps below to start turning your records into PDFs.")
        layout.addWidget(lbl_title)
        
        # Step 1
        self.step1 = StepWidget(1, "Load your Excel file", "Select the Excel file containing the beneficiary list.")
        self.step1.btn_browse.clicked.connect(self.browse_excel)
        layout.addWidget(self.step1)
        
        # Step 2
        self.step2 = StepWidget(2, "Select your Images folder", "Select the main folder containing the sub-folders of photos.")
        self.step2.btn_browse.clicked.connect(self.browse_img)
        self.step2.set_enabled(False)
        layout.addWidget(self.step2)
        
        # Step 3
        self.step3 = StepWidget(3, "Choose your Output folder", "Select where you want the finished PDFs to be saved.")
        self.step3.btn_browse.clicked.connect(self.browse_out)
        self.step3.set_enabled(False)
        layout.addWidget(self.step3)
        
        self.btn_start = QPushButton("Step 4: Start Batch")
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #0078D4; 
                color: white; 
                font-size: 16px; 
                font-weight: bold; 
                padding: 15px; 
                border-radius: 8px;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setToolTip("Please complete Steps 1, 2, and 3 first.")
        self.btn_start.setEnabled(False)
        self.btn_start.clicked.connect(self.start_batch)
        layout.addWidget(self.btn_start, 0, Qt.AlignCenter)
        
        layout.addStretch()
        
    def browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self.step1.txt_path.setText(path)
            try:
                df = pd.read_excel(path)
                count = len(df)
                if count > 0:
                    self.step1.set_validation(True, f"✓ {count} beneficiaries found")
                    self.step2.set_enabled(True)
                else:
                    self.step1.set_validation(False, "X Excel file is empty")
                    self.step2.set_enabled(False)
            except Exception:
                self.step1.set_validation(False, "X File cannot be read")
                self.step2.set_enabled(False)
            self._check_all_steps()
                
    def browse_img(self):
        path = QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if path:
            self.step2.txt_path.setText(path)
            subdirs = [x for x in os.listdir(path) if os.path.isdir(os.path.join(path, x))]
            if subdirs:
                self.step2.set_validation(True, f"✓ {len(subdirs)} beneficiary folders found")
                self.step3.set_enabled(True)
            else:
                self.step2.set_validation(False, "X Folder is empty — check your selection")
                self.step3.set_enabled(False)
            self._check_all_steps()
                
    def browse_out(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path:
            self.step3.txt_path.setText(path)
            if os.access(path, os.W_OK):
                self.step3.set_validation(True, "✓ Ready")
            else:
                self.step3.set_validation(False, "X Folder is not writable — check permissions")
            self._check_all_steps()
            
    def _check_all_steps(self):
        if self.step1.lbl_check.text() == "✓" and self.step2.lbl_check.text() == "✓" and self.step3.lbl_check.text() == "✓":
            self.btn_start.setEnabled(True)
            self.btn_start.setToolTip("Everything looks good! Click to begin processing.")
        else:
            self.btn_start.setEnabled(False)
            self.btn_start.setToolTip("Please complete Steps 1, 2, and 3 first.")

    def start_batch(self):
        self.batch_started.emit()
        self.show_banner.emit("success", "Batch started! Switching to Dashboard...")
        self.processor.start_batch(self.step1.txt_path.text(), self.step2.txt_path.text(), self.step3.txt_path.text())
        
    def update_progress(self, completed, total):
        pass # UI updates handled elsewhere now via dashboard
