# lambda/process_lambda.py
import json
import boto3
import time
from datetime import datetime
import hashlib

s3 = boto3.client("s3", endpoint_url="http://localstack:4566",
                  region_name="us-east-1")
dynamodb = boto3.resource(
    "dynamodb", endpoint_url="http://localstack:4566", region_name="us-east-1")

BUCKET_NAME = "ai-results-bucket"
TABLE_NAME = "ai_results"


def fake_ai_process(action, text):
    if action == "summarize":
        return text[:75] + "..." if len(text) > 75 else text
    elif action == "translate":
        return f"[translated] {text}"
    elif action == "describe":
        return f"This text has {len(text.split())} words."
    return "Unknown action."


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        user_id = message["user_id"]
        action = message["user_action"]
        text = message["user_text"]

        # Process
        result = fake_ai_process(action, text)

        # Store to S3
        file_name = f"{user_id}_{int(time.time())}_{action}.txt"
        s3.put_object(Bucket=BUCKET_NAME, Key=file_name, Body=result)

        # Store to DynamoDB
        table = dynamodb.Table(TABLE_NAME)
        table.put_item(Item={
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "original_text": text,
            "s3_file": file_name
        })

    return {"statusCode": 200}
