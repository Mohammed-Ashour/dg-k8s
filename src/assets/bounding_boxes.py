# hydrosat_processing/assets/daily_processing.py
from dagster import asset, AssetExecutionContext, MultiPartitionsDefinition, Output, MetadataValue

# Helper to get all bbox_ids (for partition definition)
def get_all_bbox_ids():
    from src.resources.database import sqlite_database
    db_ops = sqlite_database(None).get_operations()
    return [str(bbox['bbox_id']) for bbox in db_ops.get_active_bounding_boxes()]

bbox_date_partitions = MultiPartitionsDefinition(
    {
        "bbox_id": get_all_bbox_ids(),
        "date": {"start": "2025-01-01", "freq": "daily"},
    }
)

@asset(
    partitions_def=bbox_date_partitions,
    compute_kind="python",
    group_name="processing",
    io_manager_key="io_manager",
    required_resource_keys={"database", "storage", "satellite_data"}
)
def bounding_boxes(context: AssetExecutionContext):
    """Asset that retrieves the bounding box for the current partition (bbox_id, date)."""
    partition = context.partition_key
    if isinstance(partition, str) and "|" in partition:
        bbox_id, date = partition.split("|")
    elif isinstance(partition, dict):
        bbox_id = partition["bbox_id"]
        date = partition["date"]
    else:
        raise Exception(f"Unexpected partition key: {partition}")
    db_ops = context.resources.database.get_operations()
    bbox = db_ops.get_bounding_box_by_id(int(bbox_id))
    if not bbox:
        raise Exception(f"No bounding box found for bbox_id {bbox_id}")
    context.log.info(f"Retrieved bbox {bbox_id} for date {date}")
    return Output(
        value=bbox,
        metadata={
            "bbox_id": MetadataValue.text(str(bbox_id)),
            "bbox_name": MetadataValue.text(bbox["name"]),
            "date": MetadataValue.text(date),
        }
    )

# Export bbox_date_partitions for use in other modules
__all__ = ["bbox_date_partitions", "bounding_boxes"]

