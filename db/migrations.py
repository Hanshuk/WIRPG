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
        """,
        """
        CREATE TABLE IF NOT EXISTS image_hash_registry (
            image_id TEXT PRIMARY KEY,
            sha256_hash TEXT NOT NULL,
            phash TEXT NOT NULL,
            dhash TEXT NOT NULL,
            file_path TEXT NOT NULL,
            ias_no TEXT NOT NULL,
            slot INTEGER NOT NULL,
            registered_at TEXT NOT NULL
        )
        """
    ]
    with db.connection() as conn:
        for q in queries:
            conn.execute(q)
        
        # Add metadata columns to processing_queue if not present
        cursor = conn.execute("PRAGMA table_info(processing_queue)")
        columns = [row['name'] for row in cursor.fetchall()]
        
        new_cols = {
            "error_type": "TEXT",
            "missing_fields": "TEXT",
            "missing_images": "TEXT",
            "suggested_fix": "TEXT",
            "timestamp": "TEXT"
        }
        for col_name, col_type in new_cols.items():
            if col_name not in columns:
                conn.execute(f"ALTER TABLE processing_queue ADD COLUMN {col_name} {col_type}")
                
        conn.commit()
