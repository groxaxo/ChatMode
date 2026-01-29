#!/usr/bin/env python3
"""
Golden Path Demo Setup Script

This script sets up a demonstration environment with two fully configured agents
to showcase the ChatMode Agent Manager capabilities:

1. **Sage** - A knowledgeable assistant with long-term memory enabled
2. **Echo** - A voice-enabled conversational agent with TTS

Run this script after starting the ChatMode server to populate the database
with demo data.
"""

import os
import sys
import requests
import json
from datetime import datetime

# Configuration
BASE_URL = os.environ.get("CHATMODE_URL", "http://localhost:8000")
ADMIN_USER = os.environ.get("DEMO_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("DEMO_ADMIN_PASS", "admin123")


def log(msg: str, level: str = "INFO"):
    """Print a log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")


def api_request(method: str, endpoint: str, token: str = None, **kwargs) -> dict:
    """Make an API request."""
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    url = f"{BASE_URL}{endpoint}"
    response = requests.request(method, url, headers=headers, **kwargs)
    
    if response.status_code >= 400:
        log(f"API Error: {response.status_code} - {response.text}", "ERROR")
        return None
    
    return response.json() if response.text else {}


def setup_demo():
    """Set up the golden path demo environment."""
    log("=" * 60)
    log("ChatMode Golden Path Demo Setup")
    log("=" * 60)
    
    # Step 1: Create admin user (first run only)
    log("Step 1: Creating admin user...")
    
    # Try to login first
    login_response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASS}
    )
    
    if login_response.status_code == 200:
        token = login_response.json()["access_token"]
        log(f"Logged in as existing admin user '{ADMIN_USER}'")
    else:
        log("Admin user doesn't exist, will be created on first DB init")
        log("Please create an admin user manually or via the bootstrap script")
        return False
    
    # Step 2: Create Agent 1 - Sage (Memory-enabled assistant)
    log("Step 2: Creating Agent 'Sage' - Memory-enabled assistant...")
    
    sage_data = {
        "name": "sage",
        "display_name": "Sage",
        "model": "gpt-4o",
        "provider": "openai",
        "api_url": "https://api.openai.com/v1",
        "system_prompt": """You are Sage, a wise and knowledgeable AI assistant with excellent memory.

You remember past conversations and use that context to provide more personalized responses.
When relevant memories are available, incorporate them naturally into your responses.

Your personality traits:
- Thoughtful and analytical
- Patient and thorough in explanations
- Draws connections between topics
- References previous discussions when relevant

Always strive to be helpful while demonstrating your memory capabilities.""",
        "developer_prompt": "Use retrieved memories to enhance responses. Reference past conversations naturally.",
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 1.0,
        "enabled": True
    }
    
    result = api_request("POST", "/api/v1/agents/", token, json=sage_data)
    if result:
        sage_id = result["id"]
        log(f"Created agent 'Sage' with ID: {sage_id}")
        
        # Enable memory for Sage
        memory_settings = {
            "memory_enabled": True,
            "embedding_provider": "openai",
            "embedding_model": "text-embedding-3-small",
            "retention_days": 90,
            "top_k": 5
        }
        api_request("PUT", f"/api/v1/agents/{sage_id}/memory", token, json=memory_settings)
        log("Enabled long-term memory for Sage")
    else:
        log("Agent 'Sage' may already exist, continuing...")
    
    # Step 3: Create Agent 2 - Echo (Voice-enabled agent)
    log("Step 3: Creating Agent 'Echo' - Voice-enabled conversational agent...")
    
    echo_data = {
        "name": "echo",
        "display_name": "Echo",
        "model": "gpt-4o-mini",
        "provider": "openai",
        "api_url": "https://api.openai.com/v1",
        "system_prompt": """You are Echo, a friendly and expressive AI assistant optimized for voice conversations.

Your responses are designed to sound natural when spoken aloud. You:
- Use conversational language and contractions
- Keep responses concise but warm
- Avoid overly technical jargon
- Add natural transitions and verbal cues
- Express personality through word choice

Remember: Your responses will be converted to speech, so write how you'd naturally speak.""",
        "developer_prompt": "Optimize responses for TTS output. Keep under 100 words when possible.",
        "temperature": 0.8,
        "max_tokens": 512,
        "top_p": 0.9,
        "enabled": True
    }
    
    result = api_request("POST", "/api/v1/agents/", token, json=echo_data)
    if result:
        echo_id = result["id"]
        log(f"Created agent 'Echo' with ID: {echo_id}")
        
        # Enable TTS for Echo
        voice_settings = {
            "tts_enabled": True,
            "tts_provider": "openai",
            "tts_model": "tts-1",
            "tts_voice": "nova",
            "speaking_rate": 1.1,
            "pitch": 0.0,
            "stt_enabled": True,
            "stt_provider": "openai",
            "stt_model": "whisper-1"
        }
        api_request("PUT", f"/api/v1/agents/{echo_id}/voice", token, json=voice_settings)
        log("Enabled TTS/STT for Echo")
    else:
        log("Agent 'Echo' may already exist, continuing...")
    
    # Step 4: Create a moderator user
    log("Step 4: Creating moderator user...")
    
    moderator_data = {
        "username": "moderator",
        "email": "mod@example.com",
        "password": "mod123",
        "role": "moderator"
    }
    
    result = api_request("POST", "/api/v1/users/", token, json=moderator_data)
    if result:
        log(f"Created moderator user: {moderator_data['username']}")
    else:
        log("Moderator user may already exist, continuing...")
    
    # Step 5: Create a viewer user
    log("Step 5: Creating viewer user...")
    
    viewer_data = {
        "username": "viewer",
        "email": "viewer@example.com",
        "password": "view123",
        "role": "viewer"
    }
    
    result = api_request("POST", "/api/v1/users/", token, json=viewer_data)
    if result:
        log(f"Created viewer user: {viewer_data['username']}")
    else:
        log("Viewer user may already exist, continuing...")
    
    # Summary
    log("=" * 60)
    log("Golden Path Demo Setup Complete!")
    log("=" * 60)
    log("")
    log("Created Resources:")
    log("  Agents:")
    log("    - Sage: Memory-enabled knowledge assistant (gpt-4o)")
    log("    - Echo: Voice-enabled conversational agent (gpt-4o-mini)")
    log("")
    log("  Users:")
    log(f"    - {ADMIN_USER} (admin) - Full system access")
    log("    - moderator (moderator) - Can manage agents and content")
    log("    - viewer (viewer) - Read-only access")
    log("")
    log("Demo Features to Try:")
    log("  1. Login to Agent Manager at: " + BASE_URL + "/frontend/agent_manager.html")
    log("  2. Edit Sage's system prompt and observe audit logging")
    log("  3. Toggle Echo's TTS settings on/off")
    log("  4. Start a conversation with each agent")
    log("  5. Upload voice messages and play them back")
    log("  6. Export a conversation to Markdown")
    log("  7. View audit logs of all actions")
    log("")
    log("API Documentation: " + BASE_URL + "/docs")
    
    return True


if __name__ == "__main__":
    try:
        success = setup_demo()
        sys.exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        log(f"Could not connect to {BASE_URL}. Is the server running?", "ERROR")
        sys.exit(1)
    except Exception as e:
        log(f"Setup failed: {e}", "ERROR")
        sys.exit(1)
