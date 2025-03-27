import boto3
import os
from io import BytesIO


aws_access_key = os.environ.get("AWS_ACCESS_KEY")
aws_secret_key = os.environ.get("AWS_SECRET_KEY")
bucket_name = os.environ.get("AWS_BUCKET_NAME")
region = os.environ.get("AWS_REGION")

def upload_to_s3(file_obj, object_name):
    """
    Uploads a file to an AWS S3 bucket.

    Args:
        file_obj (Union[str, BytesIO]): Either a file path or a BytesIO object.
        object_name (str): Name of the object in S3.

    Returns:
        str: S3 URL of the uploaded file if successful, else error message.
    """
    try:
        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

        # Upload file
        if isinstance(file_obj, str):
            # If file_obj is a path, use upload_file
            s3_client.upload_file(file_obj, bucket_name, object_name)
        else:
            # If file_obj is BytesIO, use upload_fileobj
            s3_client.upload_fileobj(file_obj, bucket_name, object_name)

        # Generate file URL
        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{object_name}"
        
        print("File uploaded successfully!")
        return s3_url

    except Exception as e:
        return f"Error uploading file: {str(e)}"

bucket_name = "drishtikon"
file_path = "hello5.jpg"  # Replace with the actual file path
object_name = "hello5.jpg"  # Name in S3

s3_url = upload_to_s3(file_path, object_name)
print(s3_url)
