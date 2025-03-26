import os
import boto3
from botocore.exceptions import ClientError

def handler(event, context):
    bucket_name = os.environ.get('BUCKET_NAME')
    if not bucket_name:
        raise Exception("BUCKET_NAME environment variable is missing.")
    
    s3 = boto3.client('s3')
    try:
        # Use a paginator to count all objects in the bucket.
        paginator = s3.get_paginator('list_objects_v2')
        count = 0
        for page in paginator.paginate(Bucket=bucket_name):
            count += len(page.get('Contents', []))
    except ClientError as e:
        raise Exception(f"Failed to access bucket {bucket_name}: {e}")
    
    return {
        'statusCode': 200,
        'body': f'Lambda executed successfully. Using bucket: {bucket_name} which contains {count} items.'
    }
