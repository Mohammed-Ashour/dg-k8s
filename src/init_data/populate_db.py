import json
from sqlite3 import Connection

from src.database.models import DatabaseSetup
from src.database.operations import DatabaseOperations


def populate_sample_data(db_connection: Connection):
    """Populate the database with sample data for testing."""
    # Add sample bounding boxes if they don't exist
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM bounding_boxes")
    if cursor.fetchone()[0] == 0:
        sample_boxes = [
            {
                "name": "Region A",
                "geometry": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-95.0, 40.0],
                                [-95.0, 41.0],
                                [-94.0, 41.0],
                                [-94.0, 40.0],
                                [-95.0, 40.0],
                            ]
                        ],
                    }
                ),
            },
            {
                "name": "Region B",
                "geometry": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-93.0, 42.0],
                                [-93.0, 43.0],
                                [-92.0, 43.0],
                                [-92.0, 42.0],
                                [-93.0, 42.0],
                            ]
                        ],
                    }
                ),
            },
        ]

        for bbox in sample_boxes:
            cursor.execute(
                "INSERT INTO bounding_boxes (name, geometry) VALUES (?, ?)",
                (bbox["name"], bbox["geometry"]),
            )

    # Add sample fields if they don't exist
    cursor.execute("SELECT COUNT(*) FROM fields")
    if cursor.fetchone()[0] == 0:
        sample_fields = [
            {
                "name": "Farm 1",
                "geometry": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-94.8, 40.2],
                                [-94.8, 40.8],
                                [-94.2, 40.8],
                                [-94.2, 40.2],
                                [-94.8, 40.2],
                            ]
                        ],
                    }
                ),
                "planting_date": "2025-03-15",
            },
            {
                "name": "Farm 2",
                "geometry": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-92.8, 42.2],
                                [-92.8, 42.8],
                                [-92.2, 42.8],
                                [-92.2, 42.2],
                                [-92.8, 42.2],
                            ]
                        ],
                    }
                ),
                "planting_date": "2025-04-01",
            },
            {
                "name": "Farm 3",
                "geometry": json.dumps(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-94.6, 40.5],
                                [-94.6, 40.9],
                                [-94.3, 40.9],
                                [-94.3, 40.5],
                                [-94.6, 40.5],
                            ]
                        ],
                    }
                ),
                "planting_date": "2025-02-20",
            },
        ]

        for field in sample_fields:
            cursor.execute(
                "INSERT INTO fields (name, geometry, planting_date) VALUES (?, ?, ?)",
                (field["name"], field["geometry"], field["planting_date"]),
            )

    db_connection.commit()


if __name__ == "__main__":
    db_setup: DatabaseSetup = DatabaseSetup("data/processing_database.db")

    db_connection = db_setup.get_connection()
    db_operations = DatabaseOperations(db_connection)
    populate_sample_data(db_connection)
    db_connection.close()
