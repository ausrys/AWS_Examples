import json
import os
import requests


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        user_input = body.get("input")

        if not user_input:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'input' in request."})
            }

        # Prepare Gemini request
        api_key = os.environ["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_input}
                    ]
                }
            ]
        }

        headers = {
            "Content-Type": "application/json"
        }

        gemini_response = requests.post(url, headers=headers, json=payload)

        if gemini_response.status_code != 200:
            raise Exception("Failed to process the request.")

        result = gemini_response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']

        return {
            "statusCode": 200,
            "body": json.dumps({
                "question": user_input,
                "answer": answer
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Sorry, something went wrong while processing your request."
            })
        }
