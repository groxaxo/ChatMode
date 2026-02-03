#!/usr/bin/env python3
"""
Test DeepSeek API connection
"""

import os
import sys
from openai import OpenAI

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Get API key and base URL from environment
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
model = os.getenv("OPENAI_MODEL", "deepseek-chat")

print(f"Testing DeepSeek API connection...")
print(f"Base URL: {base_url}")
print(f"Model: {model}")
print(f"API Key (first 10 chars): {api_key[:10]}...")

try:
    # Initialize client
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Test with a simple completion
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Please respond with a short greeting."},
        ],
        max_tokens=50,
        temperature=0.7,
    )

    print("\n✅ Success! DeepSeek API is working.")
    print(f"Response: {response.choices[0].message.content}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

    # Check for specific error types
    if "401" in str(e):
        print("Authentication error - check your API key")
    elif "404" in str(e):
        print("Endpoint not found - check base URL")
    elif "429" in str(e):
        print("Rate limit exceeded")
    else:
        print("Unknown error - check your configuration")
