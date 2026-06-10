from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QColor

class NotificationBanner(QWidget):
    """
    A non-blocking notification banner that slides down from the top of its parent,
    displays a message for 6 seconds, and then fades out.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # Non-blocking clicks
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(20, 0, 20, 0)
        
        self.lbl_icon = QLabel()
        self.lbl_icon.setFixedWidth(30)
        
        self.lbl_text = QLabel()
        self.lbl_text.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        
        self.layout.addWidget(self.lbl_icon)
        self.layout.addWidget(self.lbl_text, 1)
        
        self.hide()
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_banner)
        
        # Opacity effect for fade out
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(500)
        
    def show_success(self, message: str):
        self._show_banner(message, "#107C10", "✓")
        
    def show_warning(self, message: str):
        self._show_banner(message, "#D83B01", "!")
        
    def show_error(self, message: str):
        self._show_banner(message, "#E81123", "X")

    def _show_banner(self, message: str, bg_color: str, icon_text: str):
        self.lbl_text.setText(message)
        self.lbl_icon.setText(f"<span style='color: white; font-weight: bold; font-size: 16px;'>{icon_text}</span>")
        
        self.setStyleSheet(f"""
            NotificationBanner {{
                background-color: {bg_color};
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)
        
        if self.parent():
            parent_w = self.parent().width()
            self.setFixedWidth(min(600, parent_w - 40))
            self.move((parent_w - self.width()) // 2, 0)
        
        self.opacity_effect.setOpacity(1.0)
        self.show()
        self.raise_()
        self.timer.start(6000)
        
    def hide_banner(self):
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self.hide)
        self.fade_anim.start()
