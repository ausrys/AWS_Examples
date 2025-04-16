import json


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"]) if event.get("body") else {}
        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
