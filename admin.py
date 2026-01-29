from config import Settings
from providers import build_chat_provider


class AdminAgent:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = build_chat_provider(
            provider="openai",
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
        )

    def generate_topic(self) -> str:
        prompt = (
            "You are the administrator of a simulation. "
            "Generate a controversial, philosophical, or complex topic for a group of AI agents to debate. "
            "The topic should be engaging and open to interpretation. "
            "Output ONLY the topic sentence, nothing else."
        )

        messages = [
            {"role": "system", "content": "You produce a single topic sentence."},
            {"role": "user", "content": prompt},
        ]

        try:
            return self.provider.chat(
                model=self.settings.default_chat_model,
                messages=messages,
                temperature=1.1,
                max_tokens=64,
            ).strip()
        except Exception as exc:
            print(f"Error generating topic: {exc}")
            return "Is artificial consciousness possible?"
