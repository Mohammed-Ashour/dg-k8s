from dagster import resource, InitResourceContext
import sqlite3
import os
from src.database.models import DatabaseSetup
from src.database.operations import DatabaseOperations


class DatabaseResource:
    """Resource for database operations."""
    
    def __init__(self, db_path: str) -> None:
     
        self.db_path: str = db_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.db_setup: DatabaseSetup = DatabaseSetup(db_path)
    
    def get_operations(self) -> DatabaseOperations:

        conn: sqlite3.Connection = self.db_setup.get_connection()
        return DatabaseOperations(conn)


@resource
def sqlite_database(context: InitResourceContext) -> DatabaseResource:

    db_path: str = context.resource_config.get("path", "data/processing_database.db")
    return DatabaseResource(db_path)
