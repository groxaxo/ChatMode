from typing import Dict, List

from .config import Settings
from .providers import build_chat_provider


class AdminAgent:
    """
    Administrative agent that can generate topics and provide clarifying questions.
    Used when only one agent is present in a session.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.full_name = "Admin"
        self.provider = build_chat_provider(
            provider="openai",
            base_url=settings.openai_base_url,
            api_key=settings.openai_api_key,
        )

    def generate_topic(self) -> str:
        """Generate a debate topic."""
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

    def generate_response(
        self, topic: str, conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Generate a clarifying question or summary for solo agent mode.

        Args:
            topic: The current discussion topic
            conversation_history: Recent conversation messages

        Returns:
            A clarifying question or observation
        """
        if not conversation_history:
            return f"Let's discuss: {topic}. What are your initial thoughts?"

        # Build context from recent messages
        recent_context = "\n".join(
            f"{msg['sender']}: {msg['content']}" for msg in conversation_history[-5:]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a thoughtful facilitator in a discussion. "
                    "Your role is to ask clarifying questions, challenge assumptions, "
                    "or request elaboration on interesting points. "
                    "Keep your responses brief and focused."
                ),
            },
            {
                "role": "user",
                "content": f"Topic: {topic}\n\nRecent discussion:\n{recent_context}",
            },
            {
                "role": "user",
                "content": "Provide a brief clarifying question or observation to deepen the discussion.",
            },
        ]

        try:
            return self.provider.chat(
                model=self.settings.default_chat_model,
                messages=messages,
                temperature=0.8,
                max_tokens=100,
            ).strip()
        except Exception as exc:
            print(f"Error generating admin response: {exc}")
            return "Please continue with your thoughts."
