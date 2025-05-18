import sqlite3

class DatabaseSetup:
    def __init__(self, db_path="processing_database.db"):
        self.db_path = db_path
        self._setup_database()
    
    def _setup_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create bounding_boxes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bounding_boxes (
            bbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            geometry TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
        ''')
        
        # Create fields table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fields (
            field_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            geometry TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            planting_date TEXT NOT NULL,
            active INTEGER DEFAULT 1
        )
        ''')
        
 
        # Create missed_fields table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS missed_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER NOT NULL,
            bbox_id INTEGER NOT NULL,
            processing_time TEXT NOT NULL,
            date_missed TEXT NOT NULL,
            processed INTEGER DEFAULT 0,
            resolved_time TEXT DEFAULT NULL,
            FOREIGN KEY (field_id) REFERENCES fields (field_id),
            FOREIGN KEY (bbox_id) REFERENCES bounding_boxes (bbox_id)
        )
        ''')

        # Create processing_attempts table to track all processing attempts
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_attempts (
            attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
            field_id INTEGER,
            bbox_id INTEGER,
            processing_time REAL DEFAULT CURRENT_TIMESTAMP,
            processing_type TEXT NOT NULL CHECK(processing_type IN ('realtime', 'reprocessing')) DEFAULT 'realtime',
            error_code TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (field_id) REFERENCES fields (field_id),
            FOREIGN KEY (bbox_id) REFERENCES bounding_boxes (bbox_id)
        )
        ''')
        
        conn.commit()
        conn.close()

    def get_connection(self):
        """Get a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)
