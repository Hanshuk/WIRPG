import json
from datetime import datetime
from typing import Any
from db.database import db

class AppSettings:
    """
    Manages application settings persisted in SQLite app_settings table.
    """

    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        with db.connection() as conn:
            cursor = conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except Exception:
                    return row["value"]
        return default

    @staticmethod
    def set(key: str, value: Any) -> None:
        val_str = json.dumps(value) if not isinstance(value, str) else value
        now = datetime.now().isoformat()
        with db.connection() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (key, value, updated_at) 
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET 
                value=excluded.value, updated_at=excluded.updated_at
                """,
                (key, val_str, now)
            )
            conn.commit()

settings = AppSettings()
