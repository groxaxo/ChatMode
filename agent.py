import json
from typing import List, Dict, Optional, Tuple

from config import Settings
from memory import MemoryStore
from providers import (
    ChatProvider,
    EmbeddingProvider,
    build_chat_provider,
    build_embedding_provider,
)
from tts import TTSClient
from utils import clean_placeholders, trim_messages_to_context, approximate_tokens


class ChatAgent:
    def __init__(self, name: str, config_file: str, settings: Settings):
        self.name = name
        self.settings = settings
        self.load_profile(config_file)
        self.history: List[Dict[str, str]] = []

        if not self.api_url:
            self.api_url = (
                settings.ollama_base_url
                if self.api == "ollama"
                else settings.openai_base_url
            )

        self.chat_provider: ChatProvider = build_chat_provider(
            provider=self.api,
            base_url=self.api_url,
            api_key=self.api_key or settings.openai_api_key,
        )
        self.embedding_provider: EmbeddingProvider = build_embedding_provider(
            provider=settings.embedding_provider,
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key or settings.openai_api_key,
            model=settings.embedding_model,
        )
        self.memory = MemoryStore(
            collection_name=f"{self.name}_memory",
            persist_dir=settings.chroma_dir,
            embedding_provider=self.embedding_provider,
        )

        self.tts_client = None
        if settings.tts_enabled:
            self.tts_client = TTSClient(
                base_url=settings.tts_base_url,
                api_key=settings.tts_api_key or settings.openai_api_key,
                model=settings.tts_model,
                voice=settings.tts_voice,
                output_dir=settings.tts_output_dir,
            )

    def load_profile(self, config_file: str) -> None:
        with open(config_file, "r") as f:
            data = json.load(f)
        self.full_name = data.get("name", self.name)
        self.model = data.get("model")
        self.api = data.get("api", "ollama")
        self.api_url = data.get("url")
        self.api_key = data.get("api_key")
        self.params = data.get("params", {})

        self.system_prompt = clean_placeholders(data.get("conversing", ""))
        self.system_prompt += (
            "\nMODE: PURE CHAT. Do not mention Minecraft, inventory, or health. "
            "You are in a meeting room debating a topic."
        )

        speak_model = data.get("speak_model", {})
        if speak_model:
            self.tts_model_override = speak_model.get("model")
            self.tts_voice_override = speak_model.get("voice")
        else:
            self.tts_model_override = None
            self.tts_voice_override = None

    def _build_messages(
        self, topic: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        memory_query = topic
        if conversation_history:
            memory_query += "\n" + "\n".join(
                msg["content"] for msg in conversation_history[-5:]
            )

        memory_snippets = self.memory.query(memory_query, self.settings.memory_top_k)
        memory_text = "\n".join(
            f"- {item['text']} (speaker: {item.get('sender', 'unknown')})"
            for item in memory_snippets
        )

        history_lines = [
            f"{msg['sender']}: {msg['content']}" for msg in conversation_history
        ]
        history_text = "\n".join(history_lines)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "system",
                "content": f"Long-term memory snippets:\n{memory_text}"
                if memory_text
                else "Long-term memory snippets: (none)",
            },
            {"role": "user", "content": f"Topic:\n{topic}"},
            {"role": "user", "content": f"Conversation so far:\n{history_text}"},
            {
                "role": "user",
                "content": f"Respond as {self.full_name} with a clear, direct reply.",
            },
        ]

        return trim_messages_to_context(
            messages,
            max_tokens=self.settings.max_context_tokens,
            token_counter=approximate_tokens,
        )

    def generate_response(
        self, topic: str, conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, Optional[str]]:
        messages = self._build_messages(topic, conversation_history)
        response = self.chat_provider.chat(
            model=self.model or self.settings.default_chat_model,
            messages=messages,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_output_tokens,
            options=self.params,
        )

        output_path = None
        if self.settings.tts_enabled and self.tts_client:
            output_path = self.tts_client.speak(
                text=response,
                model=self.tts_model_override or self.settings.tts_model,
                voice=self.tts_voice_override or self.settings.tts_voice,
                filename_prefix=self.name,
            )

        return (response.strip() if response else "...", output_path)

    def remember_message(self, sender: str, content: str) -> None:
        self.memory.add(text=content, metadata={"sender": sender})
