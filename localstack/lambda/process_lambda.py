import time
from datetime import datetime
import json
import boto3
import requests
from huggingface_hub import InferenceClient

s3 = boto3.client("s3",
                  region_name="us-east-1")
dynamodb = boto3.resource(
    "dynamodb", region_name="us-east-1")

BUCKET_NAME = "ai-results-bucket"
TABLE_NAME = "ai_results"
GEMINI_API_KEY = "somekey
client = InferenceClient(
    api_key="somekey",
)
URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
)


def ai_process(action, text):
    try:
        if action == "summarize":
            result = client.summarization(
                text=text,
                model="facebook/bart-large-cnn",
            )
            print("[SUMMARY RESULT]:", result.summary_text)
            return result.summary_text

        elif action == "translate":
            result = client.translation(
                text=text,
                model="Helsinki-NLP/opus-mt-zh-en",
            )
            print("[TRANSLATION RESULT]:", result.translation_text)
            return result.translation_text

        elif action == "describe":
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": text}
                        ]
                    }
                ]
            }
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(
                URL, json=payload, headers=headers, timeout=8)
            if response.status_code == 200:
                result = response.json()
                try:
                    reply = result['candidates'][0]['content']['parts'][0]['text']
                    print("Gemini says:", reply)
                    return reply
                except (KeyError, IndexError):
                    print("Response format error:", result)
            else:
                print(
                    f"Request failed with status code {response.status_code}")
                print(response.text)

        else:
            print("[ERROR] Unknown action:", action)
            return "Unknown action."

    except Exception as e:
        print(f"[AI_PROCESS ERROR] Action: {action} | Error: {str(e)}")
        return f"Error during {action}: {str(e)}"


def handler(event, context):
    for record in event["Records"]:
        message = json.loads(record["body"])
        user_id = message["user_id"]
        action = message["user_action"]
        text = message["user_text"]

        # Process
        result = ai_process(action, text)

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
            "ai_answer": result,
            "s3_file": file_name
        })

    return {"statusCode": 200}
