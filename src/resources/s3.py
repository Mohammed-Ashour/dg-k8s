import boto3
import os
from dagster import resource

@resource(
    config_schema={
        "bucket": str,
        "region_name": str,
        "endpoint_url": str,  # Add endpoint_url for MinIO
        "use_ssl": bool,
    }
)
def s3_resource(init_context):
    return boto3.client(
        "s3",
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin"),
        region_name=init_context.resource_config["region_name"],
        endpoint_url=init_context.resource_config["endpoint_url"],
        use_ssl=init_context.resource_config["use_ssl"],
    )

def fetch_file_from_s3(s3_client, bucket: str, key: str) -> bytes:
    """Fetch a file from S3 and return its contents as bytes."""
    response = s3_client.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()