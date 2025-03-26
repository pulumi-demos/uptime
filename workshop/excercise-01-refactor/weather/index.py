import os
import json
import boto3
import requests
from datetime import datetime
from botocore.exceptions import ClientError

def handler(event, context):
    # Retrieve the S3 bucket name from the environment variable
    bucket_name = os.environ.get('BUCKET_NAME')
    if not bucket_name:
        raise Exception("BUCKET_NAME environment variable is missing.")
    
    # Use wttr.in, a public weather service that doesn't require an API key.
    weather_url = "http://wttr.in/Seattle?format=j1"
    
    # Fetch weather data for Seattle
    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json()
    except Exception as e:
        raise Exception(f"Failed to fetch weather data: {e}")
    
    # Prepare the file content as JSON
    file_content = json.dumps(weather_data, indent=2)
    
    # Create a unique filename using the current UTC timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    file_name = f"{timestamp}.txt"
    
    # Upload the file to the specified S3 bucket
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=file_content)
    except ClientError as e:
        raise Exception(f"Failed to write file to bucket {bucket_name}: {e}")
    
    return {
        'statusCode': 200,
        'body': f"Weather data for Seattle successfully written to {bucket_name}/{file_name}"
    }
