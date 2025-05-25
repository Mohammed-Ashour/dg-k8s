import json
from datetime import datetime
from typing import Any, List, Mapping


class DatabaseOperations:
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = self.conn.cursor()

    def register_bbox(self, name: str, geometry: Mapping[str, Any]) -> int:
        """Add a new bounding box to the database."""
        self.cursor.execute(
            "INSERT INTO bounding_boxes (name, geometry) VALUES (?, ?)",
            (name, json.dumps(geometry)),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def register_field(
        self, name: str, geometry: Mapping[str, Any], planting_date: str
    ) -> int:
        """Add a new field to the database."""
        self.cursor.execute(
            "INSERT INTO fields (name, geometry, planting_date) VALUES (?, ?, ?)",
            (name, json.dumps(geometry), planting_date),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def record_processing_attempt(
        self,
        field_id: int,
        bbox_id: int,
        processing_type: str,
        processing_time=None,
        error_code=None,
    ):
        """Record a processing attempt."""
        self.cursor.execute(
            """INSERT INTO processing_attempts 
               (field_id, bbox_id, processing_type, processing_time, error_code)
               VALUES (?, ?, ?, ?, ?)""",
            (field_id, bbox_id, processing_type, processing_time, error_code),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def record_missed_field(
        self, field_id: int, bbox_id: Mapping[str, Any], processing_time: str
    ):
        """Record a missed field that couldn't be processed."""
        today = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            """INSERT INTO missed_fields 
               (field_id, bbox_id, processing_time, date_missed)
               VALUES (?, ?, ?, ?)""",
            (field_id, bbox_id, processing_time, today),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def mark_missed_field_as_processed(self, field_id: int, date_missed: str):
        """Mark a previously missed field as processed."""
        self.cursor.execute(
            """UPDATE missed_fields 
               SET processed = 1, resolved_time = CURRENT_TIMESTAMP 
               WHERE field_id = ? AND date_missed = ?""",
            (field_id, date_missed),
        )
        self.conn.commit()
        return self.cursor.rowcount

    def get_pending_missed_fields(self):
        """Retrieve all pending missed fields that need processing."""
        self.cursor.execute(
            """SELECT m.field_id, m.bbox_id, m.date_missed, f.name, f.geometry
               FROM missed_fields m
               JOIN fields f ON m.field_id = f.field_id
               WHERE processed = 0 and resolved_time IS NULL"""
        )
        return [
            {
                "field_id": row[0],
                "bbox_id": row[1],
                "date_missed": row[2],
                "field_name": row[3],
                "geometry": json.loads(row[4]),
            }
            for row in self.cursor.fetchall()
        ]

    def get_fields(self) -> List[Mapping[str, Any]]:
        """Get all fields that intersect with a bounding box for a specific date."""
        self.cursor.execute(
            """SELECT f.field_id, f.name, f.geometry
               FROM fields f
               WHERE f.active = 1"""
        )
        return [
            {
                "field_id": row[0],
                "field_name": row[1],
                "geometry": json.loads(row[2]),
            }
            for row in self.cursor.fetchall()
        ]

    def get_active_bounding_boxes(self):
        """Retrieve all active bounding boxes from the database."""
        self.cursor.execute(
            "SELECT bbox_id, name, geometry FROM bounding_boxes WHERE active = 1"
        )
        return [
            {
                "bbox_id": row[0],
                "name": row[1],
                "geometry": json.loads(row[2]) if isinstance(row[2], str) else row[2],
            }
            for row in self.cursor.fetchall()
        ]

    def get_bounding_box_by_id(self, bbox_id):
        """Retrieve a specific bounding box by ID."""
        self.cursor.execute(
            "SELECT bbox_id, name, geometry FROM bounding_boxes WHERE bbox_id = ?",
            (bbox_id,),
        )
        row = self.cursor.fetchone()
        if row:
            return {
                "bbox_id": row[0],
                "name": row[1],
                "geometry": json.loads(row[2]) if isinstance(row[2], str) else row[2],
            }
        return None
