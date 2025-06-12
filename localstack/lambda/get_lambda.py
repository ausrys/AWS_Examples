import json
import boto3
import jwt

SECRET = "your_jwt_secret"
VALID_ACTIONS = {"summarize", "translate", "describe"}

sqs = boto3.client(
    "sqs", region_name="us-east-1")
QUEUE_URL = sqs.get_queue_url(QueueName="ai_requests")["QueueUrl"]


def handler(event, context):
    if event["httpMethod"] != "GET":
        return {"statusCode": 405, "body": "Only GET supported"}

    try:
        auth = event["headers"].get("Authorization", "")
        token = auth.replace("Bearer ", "")
        decoded = jwt.decode(token, SECRET, algorithms=["HS256"])
        user_id = decoded.get("user_id")
    except Exception:
        return {"statusCode": 401, "body": "Unauthorized"}

    try:
        body = json.loads(event["body"])
        action = body.get("user_action")
        text = body.get("user_text")
        if action not in VALID_ACTIONS or not text:
            raise ValueError("Invalid body")
    except Exception:
        return {"statusCode": 400, "body": "Invalid request body"}

    message = {
        "user_id": user_id,
        "user_action": action,
        "user_text": text
    }

    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Validated and sent to SQS"})
    }
