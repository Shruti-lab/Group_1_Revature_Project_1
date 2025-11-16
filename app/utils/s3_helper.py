import boto3
import os
from botocore.exceptions import NoCredentialsError
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
 
def upload_to_s3(file, folder="uploads"):
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_S3_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_S3_REGION"),
        )
 
        bucket_name = os.getenv("AWS_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("AWS_BUCKET_NAME not set in environment variables")
 
        filename = f"{folder}/{datetime.utcnow().timestamp()}_{file.filename}"
 
        logger.info(f"Uploading {file.filename} to bucket {bucket_name}.")
 
        s3.upload_fileobj(
            Fileobj=file,
            Bucket=bucket_name,
            Key=filename,
            ExtraArgs={"ContentType": file.content_type},
        )
 
        url = f"https://{bucket_name}.s3.{os.getenv('AWS_S3_REGION')}.amazonaws.com/{filename}"
        logger.info(f"Uploaded {file.filename} successfully: {url}")
        return url
 
    except NoCredentialsError:
        logger.error("AWS credentials not found.")
        return None
    except Exception as e:
        logger.error(f"Error uploading to S3: {e}")
        return None
 
 
from urllib.parse import urlparse
 
def delete_from_s3(file_urls):
    """
    Deletes one or more files from S3 given their full URLs.
    """
    if not file_urls:
        return
 
    if isinstance(file_urls, str):
        file_urls = [file_urls]  # ensure it's a list
 
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.getenv("AWS_S3_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_S3_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_S3_REGION"),
        )
 
        bucket_name = os.getenv("AWS_BUCKET_NAME")
 
        for url in file_urls:
            try:
                # Parse the key from the URL
                parsed = urlparse(url)
                key = parsed.path.lstrip('/')  # remove leading slash
 
                # Delete the file
                s3.delete_object(Bucket=bucket_name, Key=key)
                print(f"Deleted S3 file: {key}")
            except Exception as inner_e:
                print(f"Failed to delete {url}: {inner_e}")
 
    except Exception as e:
        print(f"Error connecting to S3: {e}")