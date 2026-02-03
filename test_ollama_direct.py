#!/usr/bin/env python3
"""
Test Ollama API directly
"""

import requests
import json

url = "http://localhost:11434/api/chat"
model = "llama3.2:3b"

payload = {
    "model": model,
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one word."},
    ],
    "stream": False,
    "options": {"temperature": 0.7, "num_predict": 50},
}

print(f"Testing Ollama API with model: {model}")
print(f"URL: {url}")

try:
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    print(f"\n✅ Success! Status code: {response.status_code}")
    print(f"Full response: {json.dumps(data, indent=2)}")

    if "message" in data and "content" in data["message"]:
        print(f"\nResponse content: {data['message']['content']}")
    else:
        print(f"\nNo content in response. Response structure: {data.keys()}")

except requests.exceptions.RequestException as e:
    print(f"\n❌ Request error: {e}")
    if hasattr(e, "response") and e.response is not None:
        print(f"Response status: {e.response.status_code}")
        print(f"Response text: {e.response.text}")
except Exception as e:
    print(f"\n❌ Error: {e}")
