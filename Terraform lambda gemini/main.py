import json
import os
import requests


def lambda_handler(event, _):
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
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={api_key}"
        )

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

        gemini_response = requests.post(
            url, headers=headers, json=payload, timeout=8)

        if gemini_response.status_code != 200:
            raise ValueError("Failed to process the request.")

        result = gemini_response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']

        return {
            "statusCode": 200,
            "body": json.dumps({
                "question": user_input,
                "answer": answer
            })
        }

    except RuntimeError:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Sorry, something went wrong..."
            })
        }
