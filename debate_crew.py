"""
Debate Crew Module for ChatMode.

Orchestrates multi-agent debates using CrewAI's Crew and Task system.
"""

import os
from typing import List, Dict, Any, Optional, Callable
from crewai import Agent, Crew, Task, Process

from chatmode.config import Settings
from chatmode.llm_config import create_embedder_config


class DebateCrew:
    """
    Orchestrates multi-agent debates using CrewAI.

    Replaces the custom conversation loop with CrewAI's
    structured task execution and memory management.
    """

    def __init__(
        self,
        agents: List[Agent],
        settings: Settings,
        on_response: Optional[Callable[[str, str], None]] = None,
    ):
        """
        Initialize the debate crew.

        Args:
            agents: List of CrewAI agents to participate in debate
            settings: Global application settings
            on_response: Optional callback(agent_name, response) for each response
        """
        self.agents = agents
        self.settings = settings
        self.on_response = on_response
        self.topic: str = ""
        self.conversation_history: List[Dict[str, str]] = []

        # Configure embedder for memory
        self.embedder_config = create_embedder_config(settings)

    def create_debate_task(
        self,
        agent: Agent,
        topic: str,
        conversation_history: List[Dict[str, str]],
        round_num: int,
    ) -> Task:
        """
        Create a debate response task for an agent.

        Args:
            agent: The agent to create the task for
            topic: The debate topic
            conversation_history: Previous messages in the conversation
            round_num: Current round number

        Returns:
            CrewAI Task for the agent's response
        """
        # Format conversation history for context
        history_text = self._format_history(conversation_history)

        description = f"""
You are participating in Round {round_num} of a moderated debate on the following topic:

=== TOPIC (MANDATORY) ===
{topic}
=========================

CONVERSATION SO FAR:
{history_text if history_text else "(This is the opening of the debate)"}

As {agent.role}, provide your perspective on this topic. Consider what others have said 
and either build upon, challenge, or introduce new angles to the discussion.

=== TOPIC ENFORCEMENT RULES ===
1. EVERY response MUST directly address the debate topic above
2. If someone goes off-topic, politely redirect to the topic
3. Do NOT discuss unrelated subjects, games, or personal matters
4. Stay focused on the debate - this is a professional meeting
===============================

Guidelines:
- Stay in character as {agent.role}
- Be direct and engaging
- Reference or respond to other participants when relevant
- Keep your response focused and conversational (2-4 paragraphs)
- ALWAYS connect your response back to the main topic
"""

        return Task(
            description=description,
            expected_output=f"A thoughtful debate response from {agent.role}'s perspective",
            agent=agent,
        )

    def run_round(
        self, topic: str, conversation_history: List[Dict[str, str]], round_num: int = 1
    ) -> List[Dict[str, str]]:
        """
        Execute one round of debate where each agent responds.

        Args:
            topic: The debate topic
            conversation_history: Previous messages
            round_num: Current round number

        Returns:
            List of new messages generated in this round
        """
        self.topic = topic
        self.conversation_history = conversation_history.copy()
        new_messages = []

        for agent in self.agents:
            # Create task for this agent
            task = self.create_debate_task(
                agent=agent,
                topic=topic,
                conversation_history=self.conversation_history,
                round_num=round_num,
            )

            # Create a single-agent crew for this response
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                memory=True,
                embedder=self.embedder_config,
                verbose=False,  # Reduce noise
            )

            # Execute and get response
            try:
                result = crew.kickoff()
                response = str(result.raw) if hasattr(result, "raw") else str(result)

                # Clean up response
                response = response.strip()

                # Create message entry
                message = {"sender": agent.role, "content": response}

                new_messages.append(message)
                self.conversation_history.append(message)

                # Callback for real-time updates
                if self.on_response:
                    self.on_response(agent.role, response)

            except Exception as e:
                error_msg = f"[Error generating response: {e}]"
                message = {"sender": agent.role, "content": error_msg}
                new_messages.append(message)
                print(f"Error from {agent.role}: {e}")

        return new_messages

    def run_continuous(
        self,
        topic: str,
        max_rounds: int = 0,
        delay_callback: Optional[Callable[[], bool]] = None,
    ) -> List[Dict[str, str]]:
        """
        Run continuous debate rounds.

        Args:
            topic: The debate topic
            max_rounds: Maximum rounds (0 for unlimited)
            delay_callback: Optional callback between rounds, return False to stop

        Returns:
            Complete conversation history
        """
        self.topic = topic
        self.conversation_history = []
        round_num = 1

        while True:
            print(f"\n--- Round {round_num} ---")

            new_messages = self.run_round(
                topic=topic,
                conversation_history=self.conversation_history,
                round_num=round_num,
            )

            # Check termination conditions
            if max_rounds > 0 and round_num >= max_rounds:
                print(f"\nReached maximum rounds ({max_rounds})")
                break

            # Delay callback can signal to stop
            if delay_callback and not delay_callback():
                print("\nDebate stopped by callback")
                break

            round_num += 1

        return self.conversation_history

    def _format_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for prompt context."""
        if not history:
            return ""

        lines = []
        for msg in history[-10:]:  # Last 10 messages for context
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            lines.append(f"[{sender}]: {content}")

        return "\n\n".join(lines)

    def get_agent_by_name(self, name: str) -> Optional[Agent]:
        """Find an agent by their role name."""
        for agent in self.agents:
            if agent.role.lower() == name.lower():
                return agent
        return None


class TopicGenerator:
    """
    Generates debate topics using CrewAI.
    Replaces the AdminAgent functionality.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the topic generator.

        Args:
            settings: Global application settings
        """
        self.settings = settings

        # Create a topic generator agent
        from chatmode.llm_config import get_default_llm

        self.agent = Agent(
            role="Debate Moderator",
            goal="Generate engaging and thought-provoking debate topics",
            backstory=(
                "You are an experienced debate moderator known for selecting "
                "controversial, philosophical, and complex topics that spark "
                "meaningful discussion. You choose topics that are open to "
                "multiple valid perspectives."
            ),
            llm=get_default_llm(settings),
            verbose=False,
        )

    def generate_topic(self) -> str:
        """
        Generate a new debate topic.

        Returns:
            A debate topic string
        """
        task = Task(
            description=(
                "Generate a single controversial, philosophical, or complex topic "
                "for a group of AI agents to debate. The topic should be engaging "
                "and open to interpretation. Output ONLY the topic sentence, "
                "nothing else. No quotes, no explanation."
            ),
            expected_output="A single sentence debate topic",
            agent=self.agent,
        )

        crew = Crew(
            agents=[self.agent],
            tasks=[task],
            process=Process.sequential,
            verbose=False,
        )

        try:
            result = crew.kickoff()
            topic = str(result.raw) if hasattr(result, "raw") else str(result)
            return topic.strip().strip("\"'")
        except Exception as e:
            print(f"Error generating topic: {e}")
            return "Is artificial consciousness possible?"
