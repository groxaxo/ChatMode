import sys

sys.path.insert(0, ".")
from chatmode.config import load_settings
from chatmode.session import load_agents

settings = load_settings()
print(f"Settings loaded")
try:
    agents = load_agents(settings)
    print(f"Loaded {len(agents)} agents")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
