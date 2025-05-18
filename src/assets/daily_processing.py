from dagster import asset, AssetExecutionContext, DailyPartitionsDefinition, Output, MetadataValue
import time
from src.utils.geo import bbox_to_polygon, calculate_field_metrics
from src.common.processing_type import ProcessingType
from src.alerting.alert import Alerting


# Define daily partitions
daily_partitions = DailyPartitionsDefinition(
    start_date="2025-01-01",
)


@asset(
    partitions_def=daily_partitions,
    compute_kind="python",
    group_name="processing",
    deps=["bounding_boxes"],
    required_resource_keys={"database", "storage", "satellite_data"}

)
def daily_field_processing(
    context: AssetExecutionContext,
    bounding_boxes,
):
    """
    Process all fields for each bounding box on a daily basis.
    
    This asset:
    1. Gets all bounding boxes to process from the previous asset
    2. For each bbox, gets all fields that intersect with it
    3. Processes each field using satellite data
    4. Saves the results and records processing status
    """
    database = context.resources.database
    satellite_data = context.resources.satellite_data
    storage = context.resources.storage
    start_time = time.time()
    partition_date = context.partition_key
    db_ops = database.get_operations()
    
    # Initialize metrics
    fields_processed = 0
    fields_skipped = 0
    fields_failed = 0
    
    context.log.info(f"Processing {len(bounding_boxes)} bounding boxes for date {partition_date}")
    
    # Process each bounding box received from the previous asset
    for bbox in bounding_boxes:
        bbox_id = bbox["bbox_id"]
        bbox_name = bbox["name"]
        
        context.log.info(f"Processing bbox {bbox_id}: {bbox_name} for date {partition_date}")
        
        # Get all fields that intersect with this bbox
        fields = db_ops.get_fields()
        
        if not fields:
            context.log.info(f"No fields found for bbox {bbox_id} on date {partition_date}")
            continue
        
        context.log.info(f"Found {len(fields)} fields to process for bbox {bbox_id}")
        
        # Get satellite data for this bbox and date
        try:
            sat_data = satellite_data.get_data(bbox, partition_date)
            if not sat_data:
                context.log.error(f"No satellite data available for bbox {bbox_id} on {partition_date}")
                Alerting.send_alert(level="warning", msg=f"No satellite data available for bbox {bbox_id} on {partition_date}", client_id=context.run.run_id)
                continue
        except Exception as e:
            context.log.error(f"Error retrieving satellite data: {str(e)}")
            Alerting.send_alert(level="error", msg=f"Error retrieving satellite data for bbox {bbox_id} on {partition_date}: {str(e)}", client_id=context.run.run_id)
            fields_skipped += len(fields)
            continue
        
        # Process each field
        for field in fields:
            field_id = field['field_id']
            field_name = field['field_name']
            
            try:
                # Calculate field metrics
                field_shape = bbox_to_polygon(field)
                
                if not field_shape:
                    context.log.warning(f"Invalid field geometry for field {field_id}")
                    Alerting.send_alert(level="warning", msg=f"Invalid field geometry for field {field_id}", client_id=context.run.run_id)
                    fields_skipped += 1
                    continue
                
                # Calculate metrics for this field using the satellite data
                field_metrics = calculate_field_metrics(field_shape, sat_data)
                
                # Save the results to storage
                _ = storage.save_output(
                    date=partition_date,
                    field_id=field_id,
                    data={
                        'field_id': field_id,
                        'field_name': field_name,
                        'processing_date': partition_date,
                        'metrics': field_metrics,
                        'metadata': sat_data['metadata'] if 'metadata' in sat_data else {}
                    },
                    ext="json"
                )
                
                
                # Update the processing attempt
                processing_time = time.time()
                db_ops.record_processing_attempt(
                    field_id=field_id,
                    bbox_id=bbox_id,
                    processing_time=str(processing_time),
                    error_code="0",
                    processing_type=ProcessingType.realtime.value
                )
                
                fields_processed += 1
                context.log.info(f"Successfully processed field {field_id} ({field_name}) for date {partition_date}")
                
            except Exception as e:
                error_msg = str(e)
                context.log.error(f"Error processing field {field_id}: {error_msg}")
                processing_time = time.time()
                db_ops.record_processing_attempt(
                    field_id=field_id,
                    bbox_id=bbox_id,
                    processing_time=str(processing_time),
                    error_code="999",
                    processing_type=ProcessingType.realtime.value
                ) 
                # Add to missed fields for later processing
                db_ops.record_missed_field(
                    field_id=field_id,
                    bbox_id=bbox_id,
                    processing_time=str(processing_time)
                )
                Alerting.send_alert(level="error", msg=f"Error processing field {field_id}: {error_msg}", client_id=context.run.run_id)
                
                fields_failed += 1
    
    # Generate metadata for Dagster UI
    elapsed_time = time.time() - start_time
    
    yield Output(
        value={
            "date": partition_date,
            "fields_processed": fields_processed,
            "fields_skipped": fields_skipped,
            "fields_failed": fields_failed,
            "runtime_seconds": elapsed_time
        },
        metadata={
            "fields_processed": MetadataValue.int(fields_processed),
            "fields_skipped": MetadataValue.int(fields_skipped),
            "fields_failed": MetadataValue.int(fields_failed),
            "runtime_seconds": MetadataValue.float(elapsed_time),
            "partition_date": MetadataValue.text(partition_date)
        }
    )