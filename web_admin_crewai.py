"""
ChatMode Web Admin with CrewAI Integration.

FastAPI-based web interface for controlling multi-agent debates.
"""

import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from chatmode.config import load_settings
from session_crewai import ChatSession
from chatmode.logger_config import setup_logging, get_logger

# Load settings first to get log configuration
settings = load_settings()

# Configure logging using centralized configuration
setup_logging(
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    log_to_file=True,
    log_to_console=True,
)
logger = get_logger(__name__)


app = FastAPI(title="ChatMode Admin (CrewAI)")
chat_session = ChatSession(settings)

# Add CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

base_dir = os.path.dirname(__file__)
default_frontend_dir = os.path.join(base_dir, "frontend")
reun10n_frontend_dir = os.path.join(base_dir, "Reun10n", "frontend")
frontend_dir = os.getenv("FRONTEND_DIR") or (
    reun10n_frontend_dir
    if os.path.isdir(reun10n_frontend_dir)
    else default_frontend_dir
)

app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

# Mount audio directory for TTS output
os.makedirs(settings.tts_output_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=settings.tts_output_dir), name="audio")


@app.get("/", response_class=HTMLResponse)
def admin_page(request: Request):
    """Render the admin control panel."""
    # Serve unified frontend directly (like web_admin.py does)
    unified_path = os.path.join(frontend_dir, "unified.html")
    if os.path.exists(unified_path):
        with open(unified_path, "r") as f:
            return HTMLResponse(content=f.read())

    # Fallback to template
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "running": chat_session.is_running(),
            "topic": chat_session.topic,
        },
    )


@app.post("/start")
def start_session(topic: str = Form("")):
    """Start a new debate session with the given topic."""
    topic = topic.strip()
    if not topic:
        logger.warning("Start session requested without topic")
        return RedirectResponse(url="/", status_code=303)

    try:
        logger.info(f"Starting session with topic: {topic}")
        if chat_session.start(topic):
            logger.info(f"Session started: {chat_session.session_id}")
            return RedirectResponse(url="/", status_code=303)
    except RuntimeError as e:
        logger.error(f"Failed to start session: {e}")
        return JSONResponse({"status": "error", "reason": str(e)}, status_code=400)

    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
def stop_session():
    """Stop the current debate session."""
    logger.info(f"Stopping session: {chat_session.session_id}")
    chat_session.stop()
    return RedirectResponse(url="/", status_code=303)


@app.post("/memory/clear")
def clear_memory():
    """Clear conversation history."""
    chat_session.clear_memory()
    return {"status": "memory_cleared"}


@app.post("/resume")
def resume_session():
    """Resume a paused session."""
    if chat_session.resume():
        return {"status": "resumed"}
    return JSONResponse(
        {"status": "failed", "reason": "Already running or no topic"}, status_code=400
    )


@app.post("/messages")
def send_message(content: str = Form(...), sender: str = Form("Admin")):
    """Inject an admin message into the conversation."""
    logger.info(
        f"[{chat_session.session_id}] Admin injected message from '{sender}': {content[:50]}..."
    )
    chat_session.inject_message(sender, content)
    return {"status": "sent"}


@app.get("/status")
def status(request: Request):
    """Get current session status and recent messages."""
    messages = []
    base_url = str(request.base_url).rstrip("/")

    for msg in chat_session.last_messages:
        new_msg = msg.copy()
        if new_msg.get("audio"):
            # Convert absolute path to relative URL
            filename = os.path.basename(new_msg["audio"])
            new_msg["audio"] = f"{base_url}/audio/{filename}"
        messages.append(new_msg)

    return JSONResponse(
        {
            "running": chat_session.is_running(),
            "topic": chat_session.topic,
            "session_id": chat_session.session_id,
            "created_at": chat_session.created_at,
            "last_messages": messages,
        }
    )


@app.get("/agents")
def list_agents():
    """List all available agents."""
    import json

    config_path = os.path.join(os.path.dirname(__file__), "agent_config.json")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        agents_info = []
        for agent_conf in config.get("agents", []):
            with open(agent_conf["file"], "r") as f:
                profile = json.load(f)

            agents_info.append(
                {
                    "name": profile.get("name", agent_conf.get("name")),
                    "model": profile.get("model", "default"),
                    "api": profile.get("api", "openai"),
                }
            )

        return {"agents": agents_info}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "framework": "crewai",
        "session_running": chat_session.is_running(),
    }
