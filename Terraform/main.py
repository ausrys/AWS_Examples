import json


def lambda_handler(event, _):
    try:
        body = json.loads(event["body"]) if event.get("body") else {}
        return {
            "statusCode": 200,
            "body": json.dumps(body)
        }
    except RuntimeError as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
