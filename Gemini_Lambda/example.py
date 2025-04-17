import os
import requests
from dotenv import load_dotenv
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("API key not found. Make sure it's set in the .env file.")

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"
payload = {
    "contents": [
        {
            "parts": [
                {"text": "Tell me a fun fact about space."}
            ]
        }
    ]
}
headers = {
    "Content-Type": "application/json"
}
response = requests.post(url, json=payload, headers=headers, timeout=8)
if response.status_code == 200:
    result = response.json()
    try:
        reply = result['candidates'][0]['content']['parts'][0]['text']
        print("Gemini says:", reply)
    except (KeyError, IndexError):
        print("Response format error:", result)
else:
    print(f"Request failed with status code {response.status_code}")
    print(response.text)
