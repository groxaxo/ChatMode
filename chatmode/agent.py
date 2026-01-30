import json
import asyncio
from typing import List, Dict, Optional, Tuple

from .config import Settings
from .memory import MemoryStore
from .providers import (
    ChatProvider,
    EmbeddingProvider,
    build_chat_provider,
    build_embedding_provider,
)
from .tts import TTSClient
from .utils import clean_placeholders, trim_messages_to_context, approximate_tokens


class ChatAgent:
    def __init__(self, name: str, config_file: str, settings: Settings):
        self.name = name
        self.settings = settings
        self.load_profile(config_file)
        self.history: List[Dict[str, str]] = []
        self.mcp_client = None  # MCP client for tool calling
        self.allowed_tools: List[str] = []  # Allowed MCP tools

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
        
        # Initialize MCP client if configured
        self._init_mcp_client()

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
        top_k = self.memory_top_k if self.memory_top_k is not None else self.settings.memory_top_k
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

        # Use per-agent max_context_tokens if set, otherwise use global setting
        max_tokens = self.max_context_tokens if self.max_context_tokens is not None else self.settings.max_context_tokens
        return trim_messages_to_context(
            messages,
            max_tokens=max_tokens,
            token_counter=approximate_tokens,
        )

    def generate_response(
        self, topic: str, conversation_history: List[Dict[str, str]]
    ) -> Tuple[str, Optional[str]]:
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
        
        response = self.chat_provider.chat(
            model=self.model or self.settings.default_chat_model,
            messages=messages,
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_output_tokens,
            options=self.params,
            tools=tools,
            tool_choice="auto" if tools else None,
        )
        
        # Handle tool calls
        if response.startswith("__TOOL_CALLS__:"):
            tool_calls_json = response[len("__TOOL_CALLS__:"):]
            tool_calls = json.loads(tool_calls_json)
            
            # Execute each tool call
            tool_results = []
            for call in tool_calls:
                func_name = call["function"]["name"]
                
                # Security: Verify tool is in allowed_tools list
                if func_name not in self.allowed_tools:
                    tool_results.append(f"Tool {func_name} is not allowed for this agent")
                    continue
                
                func_args = json.loads(call["function"]["arguments"]) if isinstance(
                    call["function"]["arguments"], str
                ) else call["function"]["arguments"]
                
                # Call the tool
                try:
                    result = asyncio.run(
                        self.mcp_client.call_tool(func_name, func_args)
                    )
                    tool_results.append(f"Tool {func_name} returned: {result}")
                except Exception as e:
                    tool_results.append(f"Tool {func_name} failed: {e}")
            
            # Send tool results back to LLM for natural language response
            tool_result_text = "\n".join(tool_results)
            
            # Append tool results to messages and ask LLM to respond
            messages_with_tools = messages + [
                {"role": "assistant", "content": f"[Tool execution results]\n{tool_result_text}"},
                {"role": "user", "content": "Based on the tool results above, provide a natural language response."}
            ]
            
            # Get final response from LLM
            response = self.chat_provider.chat(
                model=self.model or self.settings.default_chat_model,
                messages=messages_with_tools,
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

    def remember_message(
        self, sender: str, content: str, session_id: Optional[str] = None, topic: Optional[str] = None
    ) -> None:
        """Store a message in long-term memory with session context."""
        self.memory.add(
            text=content,
            metadata={"sender": sender},
            session_id=session_id,
            agent_id=self.name,
            topic=topic,
        )
