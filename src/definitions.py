from dagster import (
    Definitions, 
    define_asset_job, 
    ScheduleDefinition,
    AssetSelection,
    FilesystemIOManager
)

# Import assets
from src.assets.daily_processing import  daily_field_processing
from src.assets.bounding_boxes import bounding_boxes
from src.assets.missed_fields_backfill import missed_fields_processing

# Import resources
from src.resources.database import sqlite_database
from src.resources.storage import local_storage
from src.resources.satellite import satellite_data
from src.resources.s3 import s3_resource

# Define jobs
daily_processing_job = define_asset_job(
    name="daily_processing_job",
    selection=AssetSelection.assets(bounding_boxes, daily_field_processing)
)

missed_fields_job = define_asset_job(
    name="missed_fields_job",
    selection=AssetSelection.assets(missed_fields_processing),
)

# Define schedules
daily_schedule = ScheduleDefinition(
    job=daily_processing_job,
    cron_schedule="0 1 * * *",  # Run at 1:00 AM every day
)

recovery_schedule = ScheduleDefinition(
    job=missed_fields_job,
    cron_schedule="0 */6 * * *",  # Run every 6 hours
)

# Define Dagster definitions
defs = Definitions(
    assets=[
        bounding_boxes,
        daily_field_processing,
        missed_fields_processing,
    ],
    schedules=[daily_schedule, recovery_schedule],
    resources={
        "database": sqlite_database.configured({"path": "data/processing_database.db"}),
        "storage": local_storage.configured({"base_path": "data/output"}),
        "satellite_data": satellite_data.configured({"simulate": True}),
        "io_manager": FilesystemIOManager(base_dir="data/dagster_io"),
        "s3": s3_resource.configured({
            "bucket": "test-bucket",
            "region_name": "us-east-1",
            "endpoint_url": "http://minio.dagster.svc.cluster.local:9000",
            "use_ssl": False,
        }),
    },
)
