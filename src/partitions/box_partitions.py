from dagster import MultiPartitionKey, MultiPartitionsDefinition, StaticPartitionsDefinition
from datetime import datetime
from typing import List, Sequence

class BoundingBoxPartitionsDefinition(MultiPartitionsDefinition):
    def __init__(self, start_date: str, database_resource):
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.database = database_resource
        
        # Initialize the dimension definitions with names
        
        bbox_partition = StaticPartitionsDefinition(
            self._get_bbox_keys(),
 
        )
        
        self._partitions_defs = [ bbox_partition]

    def _get_bbox_keys(self) -> List[str]:
        """Get all active bounding box IDs"""
        try:
            db_ops = self.database.get_operations()
            bboxes = db_ops.get_active_bounding_boxes()
            if not bboxes:
                raise ValueError("No active bounding boxes found")
            return [str(bbox["bbox_id"]) for bbox in bboxes]
        except Exception as e:
            raise ValueError(f"Failed to get bounding box keys: {str(e)}")

    def get_multipartition_keys(self) -> Sequence[MultiPartitionKey]:
        """Generate partition keys for each date-bbox combination"""
        partitions = []
        bboxes = self._get_bbox_keys()
        
        for bbox_id in bboxes:
            partition_key = MultiPartitionKey({
                "bbox_id": f'{self.start_date.strftime("%Y-%m-%d")}_bbox_id'
            })
            partitions.append(partition_key)
        
        return partitions

    @property
    def partition_dimension_names(self) -> Sequence[str]:
        """Return the names of the partition dimensions"""
        return ["bbox_id"]