import os
from dotenv import load_dotenv
import boto3

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_S3_REGION")
)
bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
# List buckets
# response = s3.list_buckets()
# for bucket in response['Buckets']:
#     print(bucket['Name'])

with open("FILE_NAME", "rb") as f:
    s3.upload_fileobj(f, bucket_name, "OBJECT_NAME")

