import boto3
import os
from botocore.exceptions import NoCredentialsError
from uuid import uuid4

# AWS Configuration
AWS_ACCESS_KEY = "your-access-key"
AWS_SECRET_KEY = "your-secret-key"
AWS_BUCKET_NAME = "your-bucket-name"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

def upload_image_to_s3(image_bytes: bytes, filename: str) -> str:
    """
    Uploads an image to AWS S3 and returns its public URL.
    """
    unique_filename = f"{uuid4()}_{filename}"
    try:
        s3_client.put_object(Bucket=AWS_BUCKET_NAME, Key=unique_filename, Body=image_bytes, ACL="public-read")
        return f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{unique_filename}"
    except NoCredentialsError:
        raise Exception("AWS Credentials not found")
