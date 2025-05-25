from dagster import resource, InitResourceContext
import numpy as np
from datetime import datetime
import json
import random
from typing import Dict, Any, Union, List
from src.resources.s3 import fetch_file_from_s3

class SatelliteDataResource:
    """Resource for retrieving satellite data."""
    
    def __init__(self, simulate: bool = True) -> None:
        
        self.simulate: bool = simulate

    def get_data(self, bbox: Dict[str, Any], date: Union[str, datetime], s3_client=None, s3_bucket=None, s3_prefix=None) -> Dict[str, Any]:
        
        if self.simulate:
            return self._simulate_satellite_data(bbox, date)
        else:
            if not s3_client or not s3_bucket or not s3_prefix:
                raise ValueError("S3 client, bucket, and prefix must be provided for real data fetching.")
            # Compose S3 key based on bbox and date
            if isinstance(date, str):
                date_str = date
            else:
                date_str = date.strftime('%Y-%m-%d')
            bbox_id = bbox['bbox_id'] if 'bbox_id' in bbox else bbox.get('id')
            s3_key = f"{s3_prefix}/bbox_{bbox_id}_{date_str}.json"
            file_bytes = fetch_file_from_s3(s3_client, s3_bucket, s3_key)
            return json.loads(file_bytes)
    
    def _simulate_satellite_data(self, bbox: Dict[str, Any], date: Union[str, datetime]) -> Dict[str, Any]:
        
        # Convert date string to datetime if needed
        if isinstance(date, str):
            date_obj: datetime = datetime.strptime(date, '%Y-%m-%d')
        else:
            date_obj = date
        
        # Create some deterministic randomness based on the date
        day_of_year: int = date_obj.timetuple().tm_yday
        seed: int = day_of_year + date_obj.year
        np.random.seed(seed)
        
        # Generate grid dimensions based on bbox size
        if isinstance(bbox, dict) and 'geometry' in bbox:
            # For simplicity, we'll use a fixed grid size
            grid_width: int = 100
            grid_height: int = 100
        else:
            # Use bbox dimensions to determine grid size
            width_meters: float = (bbox.get('east', 0) - bbox.get('west', 0)) * 111000
            height_meters: float = (bbox.get('north', 0) - bbox.get('south', 0)) * 111000
            grid_width = max(10, int(width_meters / 30))  # 30m resolution
            grid_height = max(10, int(height_meters / 30))  # 30m resolution
            
        # Generate simulated satellite bands
        bands: Dict[str, List[List[float]]] = {
            'red': np.random.rand(grid_height, grid_width).tolist(),
            'nir': np.random.rand(grid_height, grid_width).tolist(), # near infrared
            'blue': np.random.rand(grid_height, grid_width).tolist(), 
            'green': np.random.rand(grid_height, grid_width).tolist(),
            'swir': np.random.rand(grid_height, grid_width).tolist(), # shortwave infrared
            'temperature': (np.random.rand(grid_height, grid_width) * 15 + 15).tolist()  # 15-30 degrees C
        }
        
        # Calculate NDVI from red and nir bands
        red_array: np.ndarray = np.array(bands['red'])
        nir_array: np.ndarray = np.array(bands['nir'])
        ndvi: np.ndarray = (nir_array - red_array) / (nir_array + red_array + 1e-8)
        bands['ndvi'] = ndvi.tolist()
        
        # Calculate soil moisture (simplified model)
        swir_array: np.ndarray = np.array(bands['swir'])
        soil_moisture: np.ndarray = np.clip(
            0.5 - 0.3 * swir_array + 0.2 * ndvi + 0.1 * np.random.rand(grid_height, grid_width), 
            0, 1
        )
        bands['soil_moisture'] = soil_moisture.tolist()
        
        # Add metadata
        metadata: Dict[str, Union[str, float]] = {
            'date': date if isinstance(date, str) else date.strftime('%Y-%m-%d'),
            'resolution': '30m',
            'sensor': 'Simulated',
            'cloud_cover': random.uniform(0, 0.3),
            'quality': 'Good'
        }
        
        return {
            'bands': bands,
            'metadata': metadata
        }


@resource
def satellite_data(context: InitResourceContext) -> SatelliteDataResource:
    """
    Resource factory for satellite data.
    
    Args:
        context: Dagster resource initialization context
        
    Returns:
        SatelliteDataResource instance
    """
    simulate: bool = context.resource_config.get("simulate", True)
    return SatelliteDataResource(simulate=simulate)
