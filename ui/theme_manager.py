from PySide6.QtWidgets import QApplication
from db.database import db

class ThemeManager:
    LIGHT_THEME = """
        QWidget { background-color: #FFFFFF; color: #333333; }
        QPushButton { background-color: #0078D4; color: white; border: none; padding: 5px 15px; border-radius: 4px; }
        QPushButton:hover { background-color: #106EBE; }
        QSplitter::handle { background-color: #E0E0E0; }
        QTableView { alternate-background-color: #F3F2F1; }
    """
    
    DARK_THEME = """
        QWidget { background-color: #1C1C1C; color: #FFFFFF; }
        QPushButton { background-color: #0078D4; color: white; border: none; padding: 5px 15px; border-radius: 4px; }
        QPushButton:hover { background-color: #106EBE; }
        QSplitter::handle { background-color: #333333; }
        QTableView { alternate-background-color: #2D2D2D; background-color: #1C1C1C; gridline-color: #333333; }
        QHeaderView::section { background-color: #333333; color: white; }
    """

    @classmethod
    def apply_theme(cls, theme_name: str = None):
        if not theme_name:
            theme_name = cls.get_saved_theme()
            
        app = QApplication.instance()
        if not app: return
        
        if theme_name == "dark":
            app.setStyleSheet(cls.DARK_THEME)
        else:
            app.setStyleSheet(cls.LIGHT_THEME)
            
        cls.save_theme(theme_name)
        
    @classmethod
    def get_saved_theme(cls) -> str:
        with db.connection() as conn:
            cur = conn.execute("SELECT value FROM app_settings WHERE key = 'theme'")
            row = cur.fetchone()
            return row['value'] if row else "light"
            
    @classmethod
    def save_theme(cls, theme: str):
        with db.connection() as conn:
            conn.execute("INSERT OR REPLACE INTO app_settings (key, value, updated_at) VALUES ('theme', ?, datetime('now'))", (theme,))
            conn.commit()
