#!/usr/bin/env python3
"""
Test Ollama chat functionality
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatmode.config import load_settings
from chatmode.providers import build_chat_provider

print("Testing Ollama chat functionality...")

try:
    # Load settings
    settings = load_settings()
    print(f"Base URL: {settings.openai_base_url}")
    print(f"Model: {settings.default_chat_model}")
    print(
        f"API Key: {settings.openai_api_key[:10]}..."
        if settings.openai_api_key
        else "API Key: (none)"
    )

    # Build provider
    provider = build_chat_provider(
        provider="ollama",
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )
    print(f"Provider created: {type(provider).__name__}")

    # Test chat
    print("\nTesting chat completion...")
    response = provider.chat(
        model=settings.default_chat_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Please respond with a short greeting."},
        ],
        temperature=0.7,
        max_tokens=50,
    )

    print(f"✅ Success! Response received.")
    print(f"Response content: {response.content}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

    # Provide troubleshooting tips
    print("\nTroubleshooting tips:")
    print("1. Make sure Ollama is running: `ollama serve`")
    print("2. Check if the model is available: `ollama list`")
    print(
        "3. Pull the model if needed: `ollama pull hf.co/mradermacher/Qwen3-4B-Instruct-2507-heretic-av2-i1-GGUF:Q6_K`"
    )
    print("4. Check Ollama base URL in .env file")
