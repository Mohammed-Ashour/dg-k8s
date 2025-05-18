# hydrosat_processing/assets/daily_processing.py
from dagster import asset, AssetExecutionContext, DailyPartitionsDefinition, Output, MetadataValue

# Define daily partitions
daily_partitions = DailyPartitionsDefinition(
    start_date="2025-01-01",
)

@asset(
    partitions_def=daily_partitions,
    compute_kind="python",
    group_name="processing",
    io_manager_key="io_manager",
    required_resource_keys={"database", "storage", "satellite_data"}
)
def bounding_boxes(context: AssetExecutionContext):
    """Asset that retrieves active bounding boxes from the database."""
    db_ops = context.resources.database.get_operations()
    
    # Retrieve all active bounding boxes
    boxes = db_ops.get_active_bounding_boxes()
    
    context.log.info(f"Retrieved {len(boxes)} active bounding boxes from database")
    
    # Add metadata for Dagster UI
    return Output(
        value=boxes,
        metadata={
            "num_boxes": MetadataValue.int(len(boxes)),
            "box_names": MetadataValue.text(", ".join(box["name"] for box in boxes))
        }
    )

