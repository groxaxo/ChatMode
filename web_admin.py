import os
import contextlib
from fastapi import FastAPI, Form, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from chatmode.config import load_settings
from chatmode.session import ChatSession
from chatmode.database import init_db, get_db
from chatmode.content_filter import ContentFilter, create_filter_from_permissions
from chatmode import crud
from chatmode.logger_config import setup_logging, get_logger

# Load settings and setup logging
settings = load_settings()
setup_logging(
    log_level=settings.log_level,
    log_dir=settings.log_dir,
    log_to_file=True,
    log_to_console=True,
)
logger = get_logger(__name__)

chat_session = ChatSession(settings)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Load content filter settings from first enabled agent
    setup_content_filter()
    yield


app = FastAPI(
    title="ChatMode Admin",
    description="AI Multi-Agent Conversation Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def setup_content_filter():
    """Load content filter settings from database and apply to session."""
    try:
        db = next(get_db())
        # Get first enabled agent with permissions
        agents, _ = crud.get_agents(db, page=1, per_page=1, enabled=True)
        if agents and agents[0].permissions:
            filter_instance = create_filter_from_permissions(
                {
                    "filter_enabled": agents[0].permissions.filter_enabled,
                    "blocked_words": agents[0].permissions.blocked_words,
                    "filter_action": agents[0].permissions.filter_action,
                    "filter_message": agents[0].permissions.filter_message,
                }
            )
            chat_session.set_content_filter(filter_instance)
            logger.info(f"Content filter loaded from agent '{agents[0].name}'")
            logger.info(f"  Enabled: {filter_instance.enabled}")
            logger.info(f"  Blocked words: {len(filter_instance.blocked_words)} words")
            logger.info(f"  Action: {filter_instance.action}")
        else:
            # No filter configured - create disabled filter
            default_filter = ContentFilter(
                enabled=False,
                blocked_words=[],
                action="block",
                filter_message="This message contains inappropriate content and has been blocked.",
            )
            chat_session.set_content_filter(default_filter)
            logger.info("Content filter is disabled by default")
    except Exception as e:
        logger.warning(f"Could not load content filter: {e}")
        # Set a disabled filter
        default_filter = ContentFilter(enabled=False)
        chat_session.set_content_filter(default_filter)


# Add CORS for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
try:
    from chatmode.routes import all_routers

    for router in all_routers:
        app.include_router(router)
except ImportError as e:
    print(f"Warning: Could not load API routes: {e}")

templates = Jinja2Templates(directory="templates")

base_dir = os.path.dirname(__file__)

# React frontend directory (built version)
# Build output from frontend/react-app/vite.config.js: outDir: '../dist'
react_dist_dir = os.path.join(base_dir, "frontend", "dist")
react_static_path = "/react-static"

# Serve React build assets if available
if os.path.exists(react_dist_dir):
    app.mount(
        react_static_path, StaticFiles(directory=react_dist_dir), name="react_static"
    )

# Mount audio directory
os.makedirs(settings.tts_output_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=settings.tts_output_dir), name="audio")


@app.get("/", response_class=HTMLResponse)
def admin_page(request: Request):
    """
    Serve the default admin interface (React frontend).

    DEFAULT FRONTEND: React Application
    Location: frontend/react-app/dist/
    Build command: cd frontend/react-app && npm run build

    The React frontend provides:
    - Agent Management with tickbox enable/disable
    - Agent sorting (enabled agents appear at top)
    - Real-time session monitoring
    - User authentication and role-based access
    """
    react_index = os.path.join(react_dist_dir, "index.html")
    if os.path.exists(react_index):
        with open(react_index, "r") as f:
            content = f.read()
            # Rewrite asset paths to use /react-static/
            content = content.replace('"/assets/', f'"{react_static_path}/assets/')
            content = content.replace('"/vite.svg"', f'"{react_static_path}/vite.svg"')
            return HTMLResponse(content=content)

    # Error if React frontend is not built
    return HTMLResponse(
        content="""<h1>ChatMode - Frontend Not Built</h1>
        <p>The React frontend needs to be built. Run:</p>
        <pre>cd frontend/react-app && npm run build</pre>
        <p>Then restart the server.</p>""",
        status_code=503,
    )


@app.post("/start")
async def start_session(topic: str = Form("")):
    topic = topic.strip()
    if not topic:
        return RedirectResponse(url="/", status_code=303)
    if await chat_session.start(topic):
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
async def stop_session():
    await chat_session.stop()
    return RedirectResponse(url="/", status_code=303)


@app.post("/memory/clear")
def clear_memory():
    chat_session.clear_memory()
    return {"status": "memory_cleared"}


@app.post("/resume")
async def resume_session():
    if await chat_session.resume():
        return {"status": "resumed"}
    return JSONResponse(
        {"status": "failed", "reason": "Already running or no topic"}, status_code=400
    )


@app.post("/pause")
async def pause_session():
    """
    Pause the current session without clearing history or topic.

    Note: This endpoint is duplicated in both web_admin.py and chatmode/main.py
    because they are separate entry points that may be used independently.
    """
    # Simply call chat_session.stop(), which sets _running=False but retains topic/history
    await chat_session.stop()
    return JSONResponse({"status": "paused"})


@app.post("/messages")
def send_message(content: str = Form(...), sender: str = Form("Admin")):
    # Apply content filter if configured
    if chat_session.content_filter:
        allowed, filtered_content, message = chat_session.content_filter.filter_content(
            content
        )
        if not allowed:
            return JSONResponse(
                {
                    "status": "blocked",
                    "message": message
                    or "Message blocked due to inappropriate content",
                },
                status_code=400,
            )
        content = filtered_content
    chat_session.inject_message(sender, content)
    return {"status": "sent"}


@app.post("/filter/reload")
def reload_filter():
    """Reload content filter settings from database."""
    try:
        setup_content_filter()
        return {"status": "filter_reloaded"}
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/filter/toggle")
async def toggle_filter(request: Request):
    """Toggle content filter on/off globally."""
    try:
        import json

        body = json.loads(await request.body())
        enabled = body.get("enabled", True)

        if chat_session.content_filter:
            chat_session.content_filter.enabled = enabled
            return {
                "status": "filter_toggled",
                "enabled": enabled,
                "message": f"Content filter {'enabled' if enabled else 'disabled'}",
            }
        else:
            return JSONResponse(
                {"status": "error", "message": "No content filter configured"},
                status_code=400,
            )
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/filter/status")
def get_filter_status():
    """Get current content filter status."""
    if chat_session.content_filter:
        return {
            "enabled": chat_session.content_filter.enabled,
            "action": chat_session.content_filter.action,
            "blocked_words_count": len(chat_session.content_filter.blocked_words),
        }
    else:
        return {"enabled": False, "message": "No filter configured"}


@app.get("/agents")
def list_agents(include_disabled: bool = False, db: Session = Depends(get_db)):
    """
    Return minimal info about agents for the Agent Overview tab.

    Note: This endpoint is duplicated in both web_admin.py and chatmode/main.py
    because they are separate entry points that may be used independently.
    """
    agents, _ = crud.get_agents(
        db, page=1, per_page=100, enabled=(not include_disabled)
    )
    return {
        "agents": [
            {
                "name": agent.name,
                "model": agent.model,
                "api": agent.provider or "openai",
            }
            for agent in agents
        ]
    }


@app.get("/status")
def status(request: Request):
    # Sanitize audio paths to URLs
    messages = []
    base_url = str(request.base_url).rstrip("/")

    for msg in chat_session.last_messages:
        new_msg = msg.copy()
        if new_msg.get("audio"):
            # Convert absolute path to relative URL
            # stored path: /home/op/ChatMode/tts_out/abc.mp3
            # desired url: http://host:port/audio/abc.mp3
            filename = os.path.basename(new_msg["audio"])
            new_msg["audio"] = f"{base_url}/audio/{filename}"
        messages.append(new_msg)

    return JSONResponse(
        {
            "running": chat_session.is_running(),
            "topic": chat_session.topic,
            "last_messages": messages,
        }
    )


@app.get("/profiles")
def list_profiles():
    """List available agent profiles from the profiles directory."""
    import glob
    import json

    profiles = []
    profiles_dir = "profiles"

    if os.path.exists(profiles_dir):
        files = glob.glob(os.path.join(profiles_dir, "*.json"))
        # Sort files to make list stable/alphabetical
        files.sort()

        for f_path in files:
            try:
                with open(f_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Add filename to help identify source
                    data["_filename"] = os.path.basename(f_path)
                    profiles.append(data)
            except Exception as e:
                print(f"Error reading profile {f_path}: {e}")

    return {"profiles": profiles}
