#!/usr/bin/env python3
"""
ChatMode Agent Manager CLI

A command-line tool for managing multi-agent chat sessions.
Supports starting, stopping, resuming sessions, injecting messages, and listing agents.
"""

import argparse
import sys
import time
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from rich.columns import Columns

from config import load_settings
from session_crewai import ChatSession


console = Console()


def main():
    parser = argparse.ArgumentParser(description="ChatMode Agent Manager CLI", add_help=False)
    parser.add_argument('--help', action='store_true', help='Show help message')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a new session')
    start_parser.add_argument('topic', help='The debate topic')

    # Stop command
    subparsers.add_parser('stop', help='Stop the current session')

    # Resume command
    subparsers.add_parser('resume', help='Resume a paused session')

    # Status command
    subparsers.add_parser('status', help='Show current session status')

    # List agents command
    subparsers.add_parser('list-agents', help='List available agents')

    # Inject message command
    inject_parser = subparsers.add_parser('inject', help='Inject a message into the session')
    inject_parser.add_argument('sender', help='Sender name')
    inject_parser.add_argument('message', help='Message content')

    # Clear memory command
    subparsers.add_parser('clear-memory', help='Clear conversation memory')

    args = parser.parse_args()

    if args.help or not args.command:
        show_help()
        return

    settings = load_settings()
    session = ChatSession(settings)

    if args.command == 'start':
        handle_start(session, args.topic)
    elif args.command == 'stop':
        handle_stop(session)
    elif args.command == 'resume':
        handle_resume(session)
    elif args.command == 'status':
        handle_status(session)
    elif args.command == 'list-agents':
        handle_list_agents()
    elif args.command == 'inject':
        handle_inject(session, args.sender, args.message)
    elif args.command == 'clear-memory':
        handle_clear_memory(session)


def show_help():
    help_text = """
[bold blue]ChatMode Agent Manager CLI[/bold blue]

A beautiful CLI tool for managing multi-agent chat sessions.

[bold]Usage:[/bold]
  python agent_manager.py <command> [options]

[bold]Commands:[/bold]
  [green]start <topic>[/green]       Start a new session with the given topic
  [green]stop[/green]                Stop the current session
  [green]resume[/green]              Resume a paused session
  [green]status[/green]              Show current session status and recent messages
  [green]list-agents[/green]         List all available agents
  [green]inject <sender> <msg>[/green] Inject a message into the ongoing session
  [green]clear-memory[/green]        Clear the conversation memory

[bold]Examples:[/bold]
  python agent_manager.py start "The future of AI"
  python agent_manager.py status
  python agent_manager.py inject Admin "What do you think?"
  python agent_manager.py stop

[dim]Use --help for more details.[/dim]
"""
    console.print(Panel(help_text, title="[bold magenta]ChatMode CLI[/bold magenta]", border_style="blue"))


def handle_start(session, topic):
    with console.status(f"[bold green]Starting session with topic: {topic}[/bold green]", spinner="dots"):
        if session.start(topic):
            console.print(f"[green]✓ Session started successfully![/green]")
            console.print(f"[dim]Topic: {topic}[/dim]")
            console.print("[yellow]Agents are now discussing... Press Ctrl+C to stop.[/yellow]")
            try:
                with Live(console=console, refresh_per_second=1) as live:
                    while session.is_running():
                        status_table = create_status_table(session)
                        live.update(status_table)
                        time.sleep(1)
            except KeyboardInterrupt:
                session.stop()
                console.print("[red]Session stopped by user.[/red]")
        else:
            console.print("[red]✗ Failed to start session. It might already be running.[/red]")


def handle_stop(session):
    session.stop()
    console.print("[green]✓ Session stopped.[/green]")


def handle_resume(session):
    with console.status("[bold green]Resuming session...[/bold green]", spinner="dots"):
        if session.resume():
            console.print("[green]✓ Session resumed successfully![/green]")
            console.print("[yellow]Agents are now discussing... Press Ctrl+C to stop.[/yellow]")
            try:
                with Live(console=console, refresh_per_second=1) as live:
                    while session.is_running():
                        status_table = create_status_table(session)
                        live.update(status_table)
                        time.sleep(1)
            except KeyboardInterrupt:
                session.stop()
                console.print("[red]Session stopped by user.[/red]")
        else:
            console.print("[red]✗ Failed to resume session. No topic set or already running.[/red]")


def handle_status(session):
    table = create_status_table(session)
    console.print(table)


def create_status_table(session):
    table = Table(title="[bold blue]Session Status[/bold blue]")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    running = session.is_running()
    status_icon = "[green]●[/green]" if running else "[red]●[/red]"
    table.add_row("Status", f"{status_icon} {'Running' if running else 'Stopped'}")
    table.add_row("Topic", session.topic or "[dim]Not set[/dim]")

    # Recent messages
    messages_table = Table(show_header=False, box=None)
    messages_table.add_column("Sender", style="bold yellow", width=15)
    messages_table.add_column("Message", style="white")

    for msg in session.last_messages[-5:]:
        messages_table.add_row(msg['sender'], msg['content'][:80] + "..." if len(msg['content']) > 80 else msg['content'])

    table.add_row("Recent Messages", messages_table if session.last_messages else "[dim]None[/dim]")

    return table


def handle_list_agents():
    import json
    config_path = "agent_config.json"
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        agents = config.get("agents", [])

        table = Table(title="[bold blue]Available Agents[/bold blue]")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Model", style="green")
        table.add_column("API", style="yellow")

        for agent in agents:
            with open(agent["file"], "r") as f:
                profile = json.load(f)
            table.add_row(
                profile.get("name", agent.get("name")),
                profile.get("model", "default"),
                profile.get("api", "openai")
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error loading agents: {e}[/red]")


def handle_inject(session, sender, message):
    session.inject_message(sender, message)
    console.print(f"[green]✓ Message injected:[/green] [bold]{sender}[/bold]: {message}")


def handle_clear_memory(session):
    session.clear_memory()
    console.print("[green]✓ Memory cleared.[/green]")


if __name__ == "__main__":
    main()