#!/usr/bin/env python3
"""
Agent Profile Manager - Gradio interface for managing ChatMode agent profiles
Complementary to the existing agent_manager.py CLI tool
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple

import gradio as gr


CONFIG_FILE = "agent_config.json"
PROFILES_DIR = "profiles"


def load_config() -> Dict:
    """Load agent configuration."""
    if not os.path.exists(CONFIG_FILE):
        return {"agents": []}
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(config: Dict) -> None:
    """Save agent configuration."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def load_profile(filepath: str) -> Dict:
    """Load a single agent profile."""
    with open(filepath, "r") as f:
        return json.load(f)


def save_profile(filepath: str, profile: Dict) -> None:
    """Save a single agent profile."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(profile, f, indent=4)


def list_agents() -> str:
    """List all configured agents."""
    config = load_config()
    
    if not config.get("agents"):
        return "No agents configured."
    
    output = []
    for idx, agent_conf in enumerate(config["agents"], 1):
        try:
            profile = load_profile(agent_conf["file"])
            output.append(f"{idx}. {profile.get('name', 'Unknown')} ({agent_conf['name']})")
            output.append(f"   File: {agent_conf['file']}")
            output.append(f"   Model: {profile.get('model', 'N/A')}")
            output.append(f"   API: {profile.get('api', 'N/A')}")
            output.append("")
        except Exception as e:
            output.append(f"{idx}. ERROR loading {agent_conf['name']}: {e}")
            output.append("")
    
    return "\n".join(output)


def get_agent_names() -> List[str]:
    """Get list of agent names for dropdown."""
    config = load_config()
    return [agent["name"] for agent in config.get("agents", [])]


def get_agent_details(agent_name: str) -> Tuple[str, str, str, str, str, str]:
    """Get agent profile details."""
    if not agent_name:
        return "", "", "", "", "", ""
    
    config = load_config()
    agent_conf = next((a for a in config["agents"] if a["name"] == agent_name), None)
    
    if not agent_conf:
        return "", "", "", "", "", "Agent not found"
    
    try:
        profile = load_profile(agent_conf["file"])
        return (
            profile.get("name", ""),
            profile.get("model", ""),
            profile.get("api", ""),
            profile.get("url", ""),
            profile.get("conversing", ""),
            agent_conf["file"]
        )
    except Exception as e:
        return "", "", "", "", "", f"Error loading profile: {e}"


def update_agent(agent_name: str, display_name: str, model: str, api: str, 
                url: str, system_prompt: str) -> str:
    """Update an existing agent profile."""
    if not agent_name:
        return "Please select an agent to update."
    
    config = load_config()
    agent_conf = next((a for a in config["agents"] if a["name"] == agent_name), None)
    
    if not agent_conf:
        return f"Agent '{agent_name}' not found in config."
    
    try:
        profile = load_profile(agent_conf["file"])
        
        # Update fields
        if display_name:
            profile["name"] = display_name
        if model:
            profile["model"] = model
        if api:
            profile["api"] = api
        if url:
            profile["url"] = url
        if system_prompt:
            profile["conversing"] = system_prompt
        
        save_profile(agent_conf["file"], profile)
        return f"✓ Successfully updated agent '{agent_name}'"
    except Exception as e:
        return f"✗ Error updating agent: {e}"


def create_agent(agent_id: str, display_name: str, model: str, api: str, 
                url: str, system_prompt: str) -> str:
    """Create a new agent profile."""
    if not agent_id or not display_name:
        return "Agent ID and Display Name are required."
    
    config = load_config()
    
    # Check if agent already exists
    if any(a["name"] == agent_id for a in config.get("agents", [])):
        return f"✗ Agent '{agent_id}' already exists. Use update instead."
    
    # Create profile file path
    filepath = os.path.join(PROFILES_DIR, f"{agent_id}.json")
    
    # Create profile
    profile = {
        "name": display_name,
        "model": model or "gpt-4",
        "api": api or "openai",
    }
    
    if url:
        profile["url"] = url
    
    if system_prompt:
        profile["conversing"] = system_prompt
    else:
        profile["conversing"] = f"You are {display_name}. You engage in thoughtful conversation."
    
    try:
        save_profile(filepath, profile)
        
        # Add to config
        if "agents" not in config:
            config["agents"] = []
        
        config["agents"].append({
            "name": agent_id,
            "file": filepath
        })
        
        save_config(config)
        return f"✓ Successfully created agent '{agent_id}' at {filepath}"
    except Exception as e:
        return f"✗ Error creating agent: {e}"


def delete_agent(agent_name: str) -> str:
    """Delete an agent from configuration."""
    if not agent_name:
        return "Please select an agent to delete."
    
    config = load_config()
    agent_conf = next((a for a in config["agents"] if a["name"] == agent_name), None)
    
    if not agent_conf:
        return f"✗ Agent '{agent_name}' not found."
    
    try:
        # Remove from config
        config["agents"] = [a for a in config["agents"] if a["name"] != agent_name]
        save_config(config)
        
        return f"✓ Removed '{agent_name}' from config. Profile file still exists at {agent_conf['file']}"
    except Exception as e:
        return f"✗ Error deleting agent: {e}"


def view_raw_profile(agent_name: str) -> str:
    """View raw JSON of agent profile."""
    if not agent_name:
        return "Select an agent to view"
    
    config = load_config()
    agent_conf = next((a for a in config["agents"] if a["name"] == agent_name), None)
    
    if not agent_conf:
        return "Agent not found"
    
    try:
        with open(agent_conf["file"], "r") as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"


# Gradio Interface
def build_interface():
    """Build the Gradio interface."""
    with gr.Blocks(title="ChatMode Agent Profile Manager", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 ChatMode Agent Profile Manager")
        gr.Markdown("Manage agent profiles for your ChatMode sessions")
        
        with gr.Tabs():
            # List Tab
            with gr.Tab("📋 List Agents"):
                list_btn = gr.Button("Refresh List", variant="primary")
                list_output = gr.Textbox(label="Configured Agents", lines=15, interactive=False)
                list_btn.click(fn=list_agents, outputs=list_output)
                
                # Auto-load on startup
                demo.load(fn=list_agents, outputs=list_output)
            
            # Edit Tab
            with gr.Tab("✏️ Edit Agent"):
                agent_dropdown = gr.Dropdown(
                    label="Select Agent",
                    choices=get_agent_names(),
                    interactive=True
                )
                refresh_dropdown = gr.Button("↻ Refresh List", size="sm")
                
                with gr.Row():
                    edit_display_name = gr.Textbox(label="Display Name")
                    edit_model = gr.Textbox(label="Model")
                
                with gr.Row():
                    edit_api = gr.Textbox(label="API Type (openai, ollama, etc.)")
                    edit_url = gr.Textbox(label="API URL (optional)")
                
                edit_prompt = gr.Textbox(label="System Prompt", lines=8)
                edit_filepath = gr.Textbox(label="Profile File Path", interactive=False)
                
                with gr.Row():
                    load_btn = gr.Button("Load Selected", variant="secondary")
                    update_btn = gr.Button("💾 Save Changes", variant="primary")
                
                edit_output = gr.Textbox(label="Status", interactive=False)
                
                # Wire up events
                refresh_dropdown.click(
                    fn=lambda: gr.Dropdown(choices=get_agent_names()),
                    outputs=agent_dropdown
                )
                
                load_btn.click(
                    fn=get_agent_details,
                    inputs=agent_dropdown,
                    outputs=[edit_display_name, edit_model, edit_api, edit_url, 
                            edit_prompt, edit_filepath]
                )
                
                agent_dropdown.change(
                    fn=get_agent_details,
                    inputs=agent_dropdown,
                    outputs=[edit_display_name, edit_model, edit_api, edit_url, 
                            edit_prompt, edit_filepath]
                )
                
                update_btn.click(
                    fn=update_agent,
                    inputs=[agent_dropdown, edit_display_name, edit_model, edit_api, 
                           edit_url, edit_prompt],
                    outputs=edit_output
                )
            
            # Create Tab
            with gr.Tab("➕ Create Agent"):
                gr.Markdown("Create a new agent profile")
                
                with gr.Row():
                    create_id = gr.Textbox(label="Agent ID (e.g., 'scientist')", placeholder="scientist")
                    create_display_name = gr.Textbox(label="Display Name", placeholder="Dr. Sarah Chen")
                
                with gr.Row():
                    create_model = gr.Textbox(label="Model", placeholder="gpt-4")
                    create_api = gr.Textbox(label="API Type", placeholder="openai")
                
                create_url = gr.Textbox(label="API URL (optional)", placeholder="http://localhost:11434")
                create_prompt = gr.Textbox(
                    label="System Prompt",
                    lines=6,
                    placeholder="You are Dr. Sarah Chen, a brilliant scientist..."
                )
                
                create_btn = gr.Button("✨ Create Agent", variant="primary")
                create_output = gr.Textbox(label="Status", interactive=False)
                
                create_btn.click(
                    fn=create_agent,
                    inputs=[create_id, create_display_name, create_model, create_api, 
                           create_url, create_prompt],
                    outputs=create_output
                )
            
            # Delete Tab
            with gr.Tab("🗑️ Delete Agent"):
                delete_dropdown = gr.Dropdown(
                    label="Select Agent to Delete",
                    choices=get_agent_names(),
                    interactive=True
                )
                delete_refresh = gr.Button("↻ Refresh List", size="sm")
                
                gr.Markdown("⚠️ **Warning**: This removes the agent from config but keeps the profile file.")
                
                delete_btn = gr.Button("Delete from Config", variant="stop")
                delete_output = gr.Textbox(label="Status", interactive=False)
                
                delete_refresh.click(
                    fn=lambda: gr.Dropdown(choices=get_agent_names()),
                    outputs=delete_dropdown
                )
                
                delete_btn.click(
                    fn=delete_agent,
                    inputs=delete_dropdown,
                    outputs=delete_output
                )
            
            # View Raw Tab
            with gr.Tab("📄 View Raw JSON"):
                raw_dropdown = gr.Dropdown(
                    label="Select Agent",
                    choices=get_agent_names(),
                    interactive=True
                )
                raw_refresh = gr.Button("↻ Refresh List", size="sm")
                raw_output = gr.Code(label="Raw Profile JSON", language="json", lines=20)
                
                raw_refresh.click(
                    fn=lambda: gr.Dropdown(choices=get_agent_names()),
                    outputs=raw_dropdown
                )
                
                raw_dropdown.change(
                    fn=view_raw_profile,
                    inputs=raw_dropdown,
                    outputs=raw_output
                )
    
    return demo


if __name__ == "__main__":
    print("🚀 Starting ChatMode Agent Profile Manager...")
    print(f"📂 Config: {CONFIG_FILE}")
    print(f"📁 Profiles: {PROFILES_DIR}/")
    print("-" * 50)
    
    demo = build_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
