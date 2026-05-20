from db.database import db

def run_migrations():
    queries = [
        """
        CREATE TABLE IF NOT EXISTS processing_queue (
            queue_id TEXT PRIMARY KEY,
            ias_no TEXT NOT NULL,
            name TEXT NOT NULL,
            excel_row INTEGER NOT NULL,
            status TEXT NOT NULL,
            retry_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            output_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            excel_path TEXT,
            images_folder TEXT,
            output_folder TEXT,
            template_path TEXT,
            total_rows INTEGER,
            processed_count INTEGER,
            failed_count INTEGER,
            started_at TEXT,
            last_checkpoint_at TEXT,
            status TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            module TEXT NOT NULL,
            queue_id TEXT,
            message TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS template_registry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            json_content TEXT NOT NULL,
            is_default INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    ]
    with db.connection() as conn:
        for q in queries:
            conn.execute(q)
        conn.commit()
