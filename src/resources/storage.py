import json
import os
from pathlib import Path
from typing import Any, Union

from dagster import InitResourceContext, resource


class StorageResource:
    """Resource for storing and retrieving processed data."""

    def __init__(self, base_path: str) -> None:
        """
        Initialize storage resource.

        Args:
            base_path: Base path for data storage
        """
        self.base_path: Path = Path(base_path)
        os.makedirs(self.base_path, exist_ok=True)

    def save_output(
        self, date: str, field_id: Union[int, str], data: Any, ext: str = "json"
    ) -> str:
        output_dir: Path = Path(self.base_path, date, str(field_id))
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file: Path = Path(output_dir, f"data.{ext}")
        with open(output_file, "w") as f:
            if ext == "json":
                json.dump(data, f, indent=2)
            else:
                f.write(str(data))

        return str(output_file)


@resource
def local_storage(context: InitResourceContext) -> StorageResource:
    base_path: str = context.resource_config.get("base_path", "data/output")
    return StorageResource(base_path)
