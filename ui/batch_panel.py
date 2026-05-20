from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QFileDialog, QProgressBar
from core.batch_processor import BatchProcessor

class BatchPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.processor = BatchProcessor(num_workers=4)
        self.processor.batch_progress.connect(self.update_progress)
        
        layout = QVBoxLayout(self)
        
        lyt_excel = QHBoxLayout()
        self.txt_excel = QLineEdit()
        self.txt_excel.setPlaceholderText("Select Excel File...")
        btn_excel = QPushButton("Browse")
        btn_excel.clicked.connect(self.browse_excel)
        lyt_excel.addWidget(self.txt_excel)
        lyt_excel.addWidget(btn_excel)
        layout.addLayout(lyt_excel)
        
        lyt_img = QHBoxLayout()
        self.txt_img = QLineEdit()
        self.txt_img.setPlaceholderText("Select Images Folder...")
        btn_img = QPushButton("Browse")
        btn_img.clicked.connect(self.browse_img)
        lyt_img.addWidget(self.txt_img)
        lyt_img.addWidget(btn_img)
        layout.addLayout(lyt_img)
        
        lyt_out = QHBoxLayout()
        self.txt_out = QLineEdit()
        self.txt_out.setPlaceholderText("Select Output Folder...")
        btn_out = QPushButton("Browse")
        btn_out.clicked.connect(self.browse_out)
        lyt_out.addWidget(self.txt_out)
        lyt_out.addWidget(btn_out)
        layout.addLayout(lyt_out)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        lyt_action = QHBoxLayout()
        self.btn_start = QPushButton("Start Batch")
        self.btn_start.clicked.connect(self.start_batch)
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.processor.cancel_batch)
        lyt_action.addWidget(self.btn_start)
        lyt_action.addWidget(self.btn_cancel)
        layout.addLayout(lyt_action)
        
        layout.addStretch()

    def browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel", "", "Excel Files (*.xlsx *.xls)")
        if path: self.txt_excel.setText(path)
        
    def browse_img(self):
        path = QFileDialog.getExistingDirectory(self, "Select Images Folder")
        if path: self.txt_img.setText(path)
        
    def browse_out(self):
        path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if path: self.txt_out.setText(path)

    def start_batch(self):
        self.progress.setValue(0)
        self.processor.start_batch(self.txt_excel.text(), self.txt_img.text(), self.txt_out.text())
        
    def update_progress(self, completed, total):
        self.progress.setMaximum(total)
        self.progress.setValue(completed)
