import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple

from .config import Settings
from .logger_config import get_logger, log_execution_time
from .memory import MemoryStore
from .providers import (
    ChatProvider,
    EmbeddingProvider,
    build_chat_provider,
    build_embedding_provider,
)
from .tts import TTSClient
from .utils import approximate_tokens, clean_placeholders, trim_messages_to_context

logger = get_logger(__name__)


class ChatAgent:
    def __init__(self, name: str, config_file: str, settings: Settings):
        self.name = name
        self.settings = settings
        self.config_file = config_file
        logger.debug(f"🤖 Initializing ChatAgent: {name}")

        self.load_profile(config_file)
        self.history: List[Dict[str, str]] = []
        self.mcp_client = None  # MCP client for tool calling

        if not self.api_url:
            self.api_url = (
                settings.ollama_base_url
                if self.api == "ollama"
                else settings.openai_base_url
            )

        logger.debug(f"🔌 Building chat provider: {self.api} @ {self.api_url}")
        self.chat_provider: ChatProvider = build_chat_provider(
            provider=self.api,
            base_url=self.api_url,
            api_key=self.api_key or settings.openai_api_key,
        )

        logger.debug(f"🔌 Building embedding provider: {settings.embedding_provider}")
        self.embedding_provider: EmbeddingProvider = build_embedding_provider(
            provider=settings.embedding_provider,
            base_url=settings.embedding_base_url,
            api_key=settings.embedding_api_key or settings.openai_api_key,
            model=settings.embedding_model,
        )

        logger.debug(f"🧠 Initializing memory store: {self.name}_memory")
        self.memory = MemoryStore(
            collection_name=f"{self.name}_memory",
            persist_dir=settings.chroma_dir,
            embedding_provider=self.embedding_provider,
        )

        self.tts_client = None
        if settings.tts_enabled:
            logger.debug(f"🔊 Initializing TTS client")
            self.tts_client = TTSClient(
                base_url=settings.tts_base_url,
                api_key=settings.tts_api_key or settings.openai_api_key,
                model=settings.tts_model,
                voice=settings.tts_voice,
                output_dir=settings.tts_output_dir,
            )

        # Initialize MCP client if configured
        self._init_mcp_client()
        logger.info(f"✅ ChatAgent '{name}' initialized successfully")

    def load_profile(self, config_file: str) -> None:
        import os

        with open(config_file, "r") as f:
            data = json.load(f)
        self.full_name = data.get("name", self.name)
        self.model = data.get("model")
        self.api = data.get("api", "ollama")
        self.api_url = data.get("url")

        # Support api_key directly or from environment variable via api_key_env
        self.api_key = data.get("api_key")
        if not self.api_key and data.get("api_key_env"):
            self.api_key = os.getenv(data.get("api_key_env"))

        self.params = data.get("params", {})

        # Per-agent overrides
        self.sleep_seconds = data.get("sleep_seconds")
        self.temperature_override = data.get("temperature")
        self.max_output_tokens_override = data.get(
            "max_output_tokens", data.get("max_tokens")
        )

        self.system_prompt = clean_placeholders(data.get("conversing", ""))

        # Add extra_prompt if provided in profile
        extra_prompt = data.get("extra_prompt", "")
        if extra_prompt:
            self.system_prompt += "\n" + extra_prompt

        # Per-agent memory and context settings
        self.memory_top_k = data.get("memory_top_k")  # Optional override
        self.max_context_tokens = data.get("max_context_tokens")  # Optional override

        # MCP configuration
        self.mcp_command = data.get("mcp_command")
        self.mcp_args = data.get("mcp_args", [])
        self.allowed_tools = data.get("allowed_tools", [])

        speak_model = data.get("speak_model", {})
        if speak_model:
            self.tts_model_override = speak_model.get("model")
            self.tts_voice_override = speak_model.get("voice")
        else:
            self.tts_model_override = None
            self.tts_voice_override = None

    def get_sleep_seconds(self, default: float) -> float:
        """Get per-agent sleep seconds with fallback to global default."""
        if isinstance(self.sleep_seconds, (int, float)):
            return float(self.sleep_seconds)
        return float(default)

    def sync_from_profile(self) -> None:
        """Reload profile and reinitialize providers if configuration changed."""
        prev_api = self.api
        prev_api_url = self.api_url
        prev_api_key = self.api_key
        prev_mcp_command = self.mcp_command
        prev_mcp_args = list(self.mcp_args or [])

        self.load_profile(self.config_file)
        if not self.api_url:
            self.api_url = (
                self.settings.ollama_base_url
                if self.api == "ollama"
                else self.settings.openai_base_url
            )

        api_changed = (
            self.api != prev_api
            or self.api_url != prev_api_url
            or self.api_key != prev_api_key
        )
        if api_changed:
            logger.debug(
                f"🔄 Rebuilding chat provider for {self.name} due to API changes"
            )
            self.chat_provider = build_chat_provider(
                provider=self.api,
                base_url=self.api_url,
                api_key=self.api_key or self.settings.openai_api_key,
            )

        if self.mcp_command != prev_mcp_command or self.mcp_args != prev_mcp_args:
            self.mcp_client = None
            self._init_mcp_client()

    def _init_mcp_client(self) -> None:
        """Initialize MCP client if configured."""
        if not self.mcp_command:
            return

        try:
            from .mcp_client import MCPClient

            self.mcp_client = MCPClient(
                command=self.mcp_command,
                args=self.mcp_args,
            )
        except Exception as e:
            print(f"Warning: Failed to initialize MCP client for {self.name}: {e}")

    def _build_messages(
        self, topic: str, conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        memory_query = topic
        if conversation_history:
            memory_query += "\n" + "\n".join(
                msg["content"] for msg in conversation_history[-5:]
            )

        # Use per-agent memory_top_k if set, otherwise use global setting
        top_k = (
            self.memory_top_k
            if self.memory_top_k is not None
            else self.settings.memory_top_k
        )
        memory_snippets = self.memory.query(memory_query, top_k)
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
                "content": (
                    f"Long-term memory snippets:\n{memory_text}"
                    if memory_text
                    else "Long-term memory snippets: (none)"
                ),
            },
            {"role": "user", "content": f"Topic:\n{topic}"},
            {"role": "user", "content": f"Conversation so far:\n{history_text}"},
            {
                "role": "user",
                "content": f"Respond as {self.full_name} with a clear, direct reply.",
            },
        ]

        # Use per-agent max_context_tokens if set, otherwise use global setting
        max_tokens = (
            self.max_context_tokens
            if self.max_context_tokens is not None
            else self.settings.max_context_tokens
        )
        return trim_messages_to_context(
            messages,
            max_tokens=max_tokens,
            token_counter=approximate_tokens,
        )

    def _safe_json_loads(self, raw_args: str) -> Dict:
        """
        Safely parse JSON, returning empty dict on failure.

        Args:
            raw_args: JSON string that may be invalid

        Returns:
            Parsed dict or empty dict if invalid
        """
        try:
            if isinstance(raw_args, str):
                return json.loads(raw_args)
            elif isinstance(raw_args, dict):
                return raw_args
            else:
                return {}
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Failed to parse tool arguments: {e}")
            return {}

    @log_execution_time(logger, logging.DEBUG)
    def generate_response(
        self, topic: str, conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, Optional[str]]:
        logger.debug(f"📝 Generating response for topic: {topic[:50]}...")
        messages = self._build_messages(topic, conversation_history)

        # Prepare tools if MCP client is configured
        tools = None
        if self.mcp_client and self.allowed_tools:
            try:
                tools = asyncio.run(
                    self.mcp_client.get_openai_tools(allowed_tools=self.allowed_tools)
                )
            except Exception as e:
                print(f"Warning: Failed to get MCP tools: {e}")

        temperature = (
            self.temperature_override
            if isinstance(self.temperature_override, (int, float))
            else self.settings.temperature
        )
        max_tokens = (
            int(self.max_output_tokens_override)
            if isinstance(self.max_output_tokens_override, (int, float))
            else self.settings.max_output_tokens
        )

        completion = self.chat_provider.chat(
            model=self.model or self.settings.default_chat_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            options=self.params,
            tools=tools,
            tool_choice="auto" if tools else None,
        )

        # Check for tool calls using the robust pattern from problem statement
        # msg = completion.choices[0].message
        # tool_calls = getattr(msg, "tool_calls", None) or msg.get("tool_calls")
        tool_calls = None
        if completion:
            tool_calls = getattr(completion, "tool_calls", None)
            if not tool_calls and hasattr(completion, "get"):
                tool_calls = completion.get("tool_calls")

        # Handle tool calls with proper message format
        if tool_calls:
            # Add the assistant's message with tool calls to conversation
            assistant_msg = {
                "role": "assistant",
                "content": getattr(completion, "content", None) or "",
            }
            # OpenAI API expects tool_calls in the assistant message
            if hasattr(completion, "tool_calls"):
                # Convert to dict format for messages
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in completion.tool_calls
                ]
            messages.append(assistant_msg)

            # Execute each tool call
            for tc in tool_calls:
                tool_call_id = tc.id
                tool_name = tc.function.name
                raw_args = tc.function.arguments  # string; may be invalid JSON

                # Safe JSON parsing with fallback
                args = self._safe_json_loads(raw_args)

                # Security: Verify tool is in allowed_tools list
                if tool_name not in self.allowed_tools:
                    result = {
                        "error": f"Tool {tool_name} is not allowed for this agent"
                    }
                else:
                    # Call the tool
                    try:
                        result = asyncio.run(self.mcp_client.call_tool(tool_name, args))
                    except Exception as e:
                        result = {"error": str(e)}

                # Add tool result in proper format with role="tool"
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,  # required
                        "content": json.dumps(result),  # or plain text
                    }
                )

            # Second call: model integrates tool output into natural language
            # Don't pass tools again to avoid infinite loops
            completion = self.chat_provider.chat(
                model=self.model or self.settings.default_chat_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                options=self.params,
                # Explicitly no tools on second call
            )

        # Extract final response content
        response = ""
        if completion:
            if hasattr(completion, "content"):
                response = completion.content or ""
            elif isinstance(completion, str):
                response = completion

        output_path = None
        if self.settings.tts_enabled and self.tts_client:
            output_path = self.tts_client.speak(
                text=response,
                model=self.tts_model_override or self.settings.tts_model,
                voice=self.tts_voice_override or self.settings.tts_voice,
                filename_prefix=self.name,
            )

        return (response.strip() if response else "...", output_path)

    def remember_message(
        self,
        sender: str,
        content: str,
        session_id: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> None:
        """Store a message in long-term memory with session context."""
        self.memory.add(
            text=content,
            metadata={"sender": sender},
            session_id=session_id,
            agent_id=self.name,
            topic=topic,
        )
