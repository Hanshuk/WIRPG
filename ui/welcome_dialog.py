import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QRadioButton, QButtonGroup, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from config.settings import AppSettings

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to CostPlus SolarDocs")
        self.setFixedSize(500, 450)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        lbl_title = QLabel("Welcome to CostPlus SolarDocs")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0078D4;")
        layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Let's set up your workspace in 3 quick steps")
        lbl_subtitle.setStyleSheet("font-size: 14px; color: #555555; margin-bottom: 20px;")
        layout.addWidget(lbl_subtitle)
        
        # Step 1: Output Folder
        lbl_step1 = QLabel("Step 1: Set your default output folder")
        lbl_step1.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_step1)
        
        h_out = QHBoxLayout()
        self.txt_output = QLineEdit()
        self.txt_output.setPlaceholderText("Select folder to save generated PDFs...")
        self.txt_output.setReadOnly(True)
        btn_out = QPushButton("Browse")
        btn_out.clicked.connect(self._browse_output)
        h_out.addWidget(self.txt_output)
        h_out.addWidget(btn_out)
        layout.addLayout(h_out)
        
        # Step 2: Logo
        lbl_step2 = QLabel("Step 2: Set your logo file")
        lbl_step2.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_step2)
        
        h_logo = QHBoxLayout()
        self.txt_logo = QLineEdit()
        self.txt_logo.setPlaceholderText("Select your organization's logo...")
        self.txt_logo.setReadOnly(True)
        btn_logo = QPushButton("Browse")
        btn_logo.clicked.connect(self._browse_logo)
        h_logo.addWidget(self.txt_logo)
        h_logo.addWidget(btn_logo)
        layout.addLayout(h_logo)
        
        self.lbl_logo_preview = QLabel()
        self.lbl_logo_preview.setFixedHeight(50)
        self.lbl_logo_preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_logo_preview)
        
        # Step 3: Theme
        lbl_step3 = QLabel("Step 3: Choose your preferred theme")
        lbl_step3.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_step3)
        
        h_theme = QHBoxLayout()
        self.rb_light = QRadioButton("Light Mode")
        self.rb_dark = QRadioButton("Dark Mode")
        self.rb_light.setChecked(True)
        h_theme.addWidget(self.rb_light)
        h_theme.addWidget(self.rb_dark)
        h_theme.addStretch()
        layout.addLayout(h_theme)
        
        layout.addStretch()
        
        # Get Started
        self.btn_start = QPushButton("Get Started")
        self.btn_start.setStyleSheet("background-color: #0078D4; color: white; font-weight: bold; padding: 10px; border-radius: 4px;")
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self._finish_setup)
        layout.addWidget(self.btn_start)

    def _browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Default Output Folder")
        if folder:
            self.txt_output.setText(folder)

    def _browse_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self.txt_logo.setText(path)
            pix = QPixmap(path)
            self.lbl_logo_preview.setPixmap(pix.scaled(200, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _finish_setup(self):
        if not self.txt_output.text():
            QMessageBox.warning(self, "Missing Info", "Please select a default output folder in Step 1.")
            return
        if not self.txt_logo.text():
            QMessageBox.warning(self, "Missing Info", "Please select a logo in Step 2.")
            return
            
        AppSettings.set("default_output_folder", self.txt_output.text())
        AppSettings.set("logo_path", self.txt_logo.text())
        AppSettings.set("theme", "dark" if self.rb_dark.isChecked() else "light")
        
        # Mark as not first run
        AppSettings.set("first_run_complete", True)
        
        self.accept()
