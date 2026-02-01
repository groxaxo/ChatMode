import json
import os
import time

from agent import ChatAgent
from admin import AdminAgent
from chatmode.config import load_settings


def load_config(path):
    with open(path, "r") as f:
        return json.load(f)


def main():
    settings = load_settings()
    print("Initializing Chat Mode...")

    # 1. Admin interface for topic
    topic = os.getenv("ADMIN_TOPIC", "").strip()
    if not topic:
        topic = input("Admin topic (leave blank to auto-generate): ").strip()

    if not topic and settings.admin_use_llm:
        admin = AdminAgent(settings)
        print("Admin generating topic...")
        topic = admin.generate_topic()

    if not topic:
        topic = "Is artificial consciousness possible?"

    print("\n==================================================")
    print(f"TOPIC: {topic}")
    print("==================================================\n")

    # 2. Initialize Agents
    config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")
    config = load_config(config_path)
    agents = []

    for agent_conf in config.get("agents", []):
        try:
            agent = ChatAgent(
                name=agent_conf.get("name", "agent"),
                config_file=agent_conf["file"],
                settings=settings,
            )
            agents.append(agent)
            print(f"Loaded agent: {agent.full_name}")
        except Exception as e:
            print(f"Failed to load agent {agent_conf.get('name', 'agent')}: {e}")

    if len(agents) < 2:
        print("Need at least two agents to start. Exiting.")
        return

    # 3. Conversation Loop
    conversation_history = []
    round_num = 1

    while True:
        print(f"\n--- Round {round_num} ---")
        for agent in agents:
            print(f"{agent.full_name} is thinking...")

            response = agent.generate_response(topic, conversation_history)
            print(f"\n[{agent.full_name}]: {response}")

            conversation_history.append(
                {"sender": agent.full_name, "content": response}
            )

            # Store message in each agent's long-term memory
            for memory_agent in agents:
                memory_agent.remember_message(agent.full_name, response)

            if len(conversation_history) > settings.history_max_messages:
                conversation_history.pop(0)

            print(f"\n(Waiting {settings.sleep_seconds}s...)\n")
            time.sleep(settings.sleep_seconds)

        round_num += 1


if __name__ == "__main__":
    main()
