from dagster import asset, AssetExecutionContext, Output, MetadataValue
import time
from datetime import datetime
from src.utils.geo import bbox_to_polygon, calculate_field_metrics
from src.common.processing_type import ProcessingType
from src.alerting.alert import Alerting
@asset(
    compute_kind="python",
    group_name="recovery",
    io_manager_key="io_manager",
    required_resource_keys={"database", "storage", "satellite_data"}
)
def missed_fields_processing(
    context: AssetExecutionContext,
):
    """
    Process fields that were missed in earlier runs.
    
    This asset:
    1. Gets all fields with no resolved_time in missed_fields table
    2. Retrieves satellite data for each field
    3. Processes each field and updates its status
    """
    
    start_time = time.time()
    db_ops = context.resources.database.get_operations()
    
    # Get all pending missed fields
    pending_fields = db_ops.get_pending_missed_fields()
    
    if not pending_fields:
        context.log.info("No pending missed fields to process")
        return {
            "processed": 0,
            "still_pending": 0,
            "runtime_seconds": time.time() - start_time
        }
    
    context.log.info(f"Found {len(pending_fields)} pending missed fields to process")
    
    # Initialize metrics
    fields_processed = 0
    fields_still_pending = 0
    
    # Process each missed field
    for missed_field in pending_fields:
        field_id = missed_field['field_id']
        bbox_id = missed_field['bbox_id']
        date_missed = missed_field['date_missed']
        field_name = missed_field['field_name']
        
        context.log.info(f"Attempting to process missed field {field_id} ({field_name}) for date {date_missed}")
        
        try:
            # Get the bbox for this field
            bbox_data = db_ops.get_bounding_box_by_id(bbox_id)
            if not bbox_data:
                context.log.error(f"Could not find bounding box {bbox_id} for missed field {field_id}")
                Alerting.send_alert(
                    level="error",
                    msg=f"Could not find bounding box {bbox_id} for missed field {field_id}",
                    client_id=context.run.run_id
                )
                
                fields_still_pending += 1
                continue
            
            # Get satellite data for this field's date and bbox
            try:
                sat_data = context.resources.satellite_data.get_data(bbox_data, date_missed)
                
                if not sat_data:
                    context.log.info(f"Satellite data still not available for field {field_id} on {date_missed}")
                    fields_still_pending += 1
                    continue
                    
            except Exception as e:
                context.log.error(f"Error retrieving satellite data: {str(e)}")
                Alerting.send_alert(level="error", msg=f"Error retrieving satellite data for field {field_id} on {date_missed}: {str(e)}", client_id=context.run.run_id)
                fields_still_pending += 1
                continue
            
            # Process the field
            field_shape = bbox_to_polygon(missed_field)
            
            if not field_shape:
                context.log.warning(f"Invalid field geometry for field {field_id}")
                fields_still_pending += 1
                continue
                
            field_metrics = calculate_field_metrics(field_shape, sat_data)
            
            # Save the results to storage
            _ = context.resources.storage.save_output(
                date=date_missed,
                field_id=field_id,
                data={
                    'field_id': field_id,
                    'field_name': field_name,
                    'processing_date': date_missed,
                    'processing_type': ProcessingType.reprocessing.value,
                    'metrics': field_metrics,
                    'metadata': sat_data['metadata'] if 'metadata' in sat_data else {},
                    'recovered': True,
                    'recovery_date': datetime.now().strftime("%Y-%m-%d")
                },
                ext="json"
            )
            
            # Mark as processed in missed_fields table
            db_ops.mark_missed_field_as_processed(field_id, date_missed)

            # Record the processing attempt
            db_ops.record_processing_attempt(
                field_id=field_id,
                bbox_id=bbox_id,
                processing_type=ProcessingType.reprocessing.value,
                processing_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                error_code="0"
            )
            

            fields_processed += 1
            context.log.info(f"Successfully processed missed field {field_id} for date {date_missed}")
            
        except Exception as e:
            context.log.error(f"Error processing missed field {field_id}: {str(e)}")
            Alerting.send_alert(level="error", msg=f"Error processing missed field {field_id}: {str(e)}", client_id=context.run.run_id)
            fields_still_pending += 1
    
    # Generate metadata for Dagster UI
    elapsed_time = time.time() - start_time
    
    return Output(
        value={
            "processed": fields_processed,
            "still_pending": fields_still_pending,
            "runtime_seconds": elapsed_time
        },
        metadata={
            "fields_processed": MetadataValue.int(fields_processed),
            "fields_still_pending": MetadataValue.int(fields_still_pending),
            "runtime_seconds": MetadataValue.float(elapsed_time),
            "execution_date": MetadataValue.text(datetime.now().strftime("%Y-%m-%d"))
        }
    )
