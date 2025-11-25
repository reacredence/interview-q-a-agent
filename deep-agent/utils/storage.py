import os
import boto3
from botocore.exceptions import NoCredentialsError

def upload_file(file_name, object_name=None):
    """
    Upload a file to an S3 bucket (or DigitalOcean Space).
    
    :param file_name: File to upload
    :param object_name: S3 object name. If not specified then file_name is used
    :return: Public URL if successful, else None
    """
    
    # Retrieve configuration from environment variables
    endpoint_url = os.getenv('S3_ENDPOINT_URL') # e.g., https://nyc3.digitaloceanspaces.com
    access_key = os.getenv('S3_ACCESS_KEY_ID')
    secret_key = os.getenv('S3_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('S3_BUCKET_NAME')
    region_name = os.getenv('S3_REGION_NAME', 'nyc3')
    
    if not all([endpoint_url, access_key, secret_key, bucket_name]):
        print("Skipping upload: S3 configuration missing.")
        return None

    if object_name is None:
        object_name = os.path.basename(file_name)

    # Initialize S3 client
    s3_client = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region_name
    )

    try:
        # Upload the file
        # We set ACL to public-read so the link is accessible. 
        # Note: Ensure your bucket/space allows this or configure presigned URLs instead.
        s3_client.upload_file(
            file_name, 
            bucket_name, 
            object_name, 
            ExtraArgs={'ACL': 'public-read', 'ContentType': 'application/pdf' if file_name.endswith('.pdf') else 'text/plain'}
        )
        
        # Construct public URL
        # For DigitalOcean Spaces: https://bucket-name.region.digitaloceanspaces.com/object-name
        # Or generic S3 style
        if "digitaloceanspaces" in endpoint_url:
            url = f"https://{bucket_name}.{region_name}.digitaloceanspaces.com/{object_name}"
        else:
            url = f"{endpoint_url}/{bucket_name}/{object_name}"
            
        print(f"File uploaded successfully: {url}")
        return url
        
    except FileNotFoundError:
        print(f"The file was not found: {file_name}")
        return None
    except NoCredentialsError:
        print("Credentials not available")
        return None
    except Exception as e:
        print(f"Upload failed: {e}")
        return None
