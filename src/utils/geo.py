import json
from typing import Any, Dict, Optional

import shapely.geometry
from shapely.geometry import shape


def bbox_to_polygon(bbox: Dict[str, Any]) -> shapely.geometry.Polygon:
    if isinstance(bbox, dict) and "geometry" in bbox:
        geometry = bbox["geometry"]
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        return shape(geometry)
    else:
        raise ValueError("Invalid bbox format")


def calculate_field_metrics(
    field_geometry: shapely.geometry.base.BaseGeometry, data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Calculate metrics for a field based on the satellite data.
    Currently, this is a placeholder function that simulates the calculation.
    """
    # This is a simplified example - in reality, you'd compute NDVI, temperature, etc.
    metrics: Dict[str, Any] = {
        "area": field_geometry.area,
        "perimeter": field_geometry.length,
        "centroid": [field_geometry.centroid.x, field_geometry.centroid.y],
    }

    if data is not None:
        metrics.update(
            {
                "ndvi_mean": 0.65,  # Simulated value
                "ndvi_min": 0.45,  # Simulated value
                "ndvi_max": 0.85,  # Simulated value
                "temperature_mean": 22.5,  # Simulated value in Celsius
                "moisture": 0.35,  # Simulated value
            }
        )

    return metrics


def filter_fields_in_bbox(fields, bbox):
    bbox_geom = shape(bbox["geometry"])
    filtered = []
    for field in fields:
        field_geom = shape(field["geometry"])
        if bbox_geom.intersects(field_geom):
            filtered.append(field)
    return filtered
