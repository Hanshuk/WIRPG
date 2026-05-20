from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QSplitter, QLabel
from PySide6.QtCore import Qt
from ui.dashboard_widget import DashboardWidget
from ui.batch_panel import BatchPanel
from ui.manual_panel import ManualPanel
from ui.preview_panel import PreviewPanel
from ui.log_console import LogConsole
from ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CostPlus SolarDocs v1.0.0 — Cost Plus Inc.")
        self.resize(1280, 780)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        
        self.stack = QStackedWidget()
        
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_batch = QPushButton("Batch Processing")
        self.btn_manual = QPushButton("Manual Mode")
        self.btn_preview = QPushButton("Preview PDFs")
        self.btn_logs = QPushButton("System Logs")
        self.btn_settings = QPushButton("Settings")
        
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_batch)
        sidebar_layout.addWidget(self.btn_manual)
        sidebar_layout.addWidget(self.btn_preview)
        sidebar_layout.addWidget(self.btn_logs)
        sidebar_layout.addStretch()
        sidebar_layout.addWidget(self.btn_settings)
        
        self.dashboard = DashboardWidget()
        self.batch_panel = BatchPanel()
        self.manual_panel = ManualPanel()
        self.preview_panel = PreviewPanel()
        self.log_console = LogConsole()
        
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.batch_panel)
        self.stack.addWidget(self.manual_panel)
        self.stack.addWidget(self.preview_panel)
        self.stack.addWidget(self.log_console)
        
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.stack)
        splitter.setSizes([200, 1000])
        
        self.btn_dashboard.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_batch.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_manual.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_preview.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.btn_logs.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.btn_settings.clicked.connect(self.show_settings)
        
        self.statusBar().showMessage("Ready")
        
        lbl_madeby = QLabel("Made By Hanshuk Sathe")
        self.statusBar().addPermanentWidget(lbl_madeby)
        
    def show_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
