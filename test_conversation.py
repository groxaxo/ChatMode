#!/usr/bin/env python3
"""
Demonstrate initiating a conversation with Argentinian slang topic.
"""

import asyncio
import sys
from unittest.mock import Mock, patch, AsyncMock

# Add current directory to path
sys.path.insert(0, ".")

from chatmode.config import Settings
from chatmode.session import ChatSession


async def main():
    # Create mock settings
    settings = Settings(
        openai_api_key="test",
        openai_base_url="http://localhost",
        default_chat_model="gpt-4o-mini",
        ollama_base_url="http://localhost:11434",
        embedding_provider="ollama",
        embedding_model="nomic-embed-text",
        embedding_base_url="http://localhost:11434",
        embedding_api_key="",
        tts_enabled=False,
        tts_base_url="http://localhost",
        tts_api_key="",
        tts_model="tts-1",
        tts_voice="alloy",
        tts_output_dir="/tmp",
        tts_format="mp3",
        tts_speed=1.0,
        tts_instructions="",
        tts_timeout=30.0,
        tts_max_retries=3,
        tts_headers="",
        chroma_dir="/tmp",
        max_context_tokens=32000,
        max_output_tokens=512,
        memory_top_k=5,
        history_max_messages=20,
        temperature=0.9,
        sleep_seconds=0.1,
        admin_use_llm=False,
        verbose=False,
        log_level="INFO",
        log_dir="/tmp",
    )
    session = ChatSession(settings)
    # Mock load_agents to return a single mock agent
    with patch("chatmode.session.load_agents") as load_mock:
        mock_agent = Mock()
        mock_agent.name = "test"
        mock_agent.full_name = "Test Agent"
        mock_agent.sleep_seconds = 0.1
        mock_agent.get_sleep_seconds = Mock(return_value=0.1)
        mock_agent.generate_response = AsyncMock(return_value="Mock response")
        load_mock.return_value = [mock_agent]

        # Mock AdminAgent's provider
        with patch("chatmode.admin.build_chat_provider") as mock_build:
            mock_provider = Mock()
            mock_provider.chat = Mock(return_value="Mock admin response")
            mock_build.return_value = mock_provider

            # Mock the session's _run_loop to prevent background task errors
            with patch.object(session, "_run_loop", AsyncMock()):
                # Start session with Argentinian slang topic
                topic = "¡Qué quilombo! (Argentinian slang for 'What a mess!')"
                success = await session.start(topic)
                if success:
                    print(f"✅ Session started with topic: {topic}")
                    print(f"Session ID: {session.session_id}")
                    print(f"Admin agent created: {session.admin_agent is not None}")

                    # Simulate a brief conversation with Argentinian slang
                    slang_phrases = [
                        "¡Qué quilombo!",
                        "¡Che, boludo!",
                        "¡Es un bajón!",
                        "¡Estoy en bolas!",
                        "¡Hacerse la rata!",
                    ]

                    print("\n📝 Simulating conversation:")
                    for i, phrase in enumerate(slang_phrases):
                        # Inject user message
                        session.inject_message("User", phrase)
                        print(f"  User: {phrase}")

                        # Simulate agent response (using mocked agent)
                        agent_response = f"Entiendo tu slang argentino: '{phrase}'"
                        mock_agent.generate_response.return_value = agent_response
                        # In real session, agent would generate response automatically
                        # For demo, we just print simulated response
                        print(f"  Agent: {agent_response}")

                        # Small delay for realism
                        await asyncio.sleep(0.1)

                    print(
                        f"\n📊 Conversation stats: {len(slang_phrases)} messages exchanged"
                    )

                    # Stop session immediately to avoid background tasks
                    await session.stop()
                    print("Session stopped gracefully.")
                else:
                    print("❌ Failed to start session")


if __name__ == "__main__":
    asyncio.run(main())
