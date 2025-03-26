# lambda/index.py
import os

def handler(event, context):
    bucket_name = os.environ.get('BUCKET_NAME')
    if not bucket_name:
        raise Exception("BUCKET_NAME environment variable is missing.")
    
    return {
        'statusCode': 200,
        'body': f'Lambda executed successfully. Using bucket: {bucket_name}'
    }

