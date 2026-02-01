import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from chatmode.llm_config import create_llm_from_profile
import json

settings = load_settings()
print("Settings loaded")

# Load sunny profile
with open("profiles/sunny.json", "r") as f:
    profile = json.load(f)

print(f"Profile: {profile['name']}, model: {profile['model']}, api: {profile['api']}")

llm = create_llm_from_profile(profile, settings)
print(f"LLM created: {llm.model}, base_url: {llm.base_url}")

# Try a simple completion
try:
    print("Testing LLM completion...")
    response = llm.completion(prompt="Hello, how are you?", max_tokens=10)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
