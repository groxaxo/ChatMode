"""
ChatMode Main Application

Single entrypoint for the ChatMode API and admin interface.
Combines all routes and serves the unified frontend.
"""

import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from .config import load_settings
from .session import ChatSession
from .database import init_db

# Create FastAPI app
app = FastAPI(
    title="ChatMode - AI Multi-Agent Platform",
    description="Manage and orchestrate AI agent conversations with multiple LLM providers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Load settings
settings = load_settings()
chat_session = ChatSession(settings)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
try:
    from .routes import all_routers
    for router in all_routers:
        app.include_router(router)
except ImportError as e:
    print(f"Warning: Could not load API routes: {e}")

# Setup templates and static files
base_dir = os.path.dirname(os.path.dirname(__file__))
templates_dir = os.path.join(base_dir, "templates")
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
else:
    templates = None

# Frontend directory
default_frontend_dir = os.path.join(base_dir, "frontend")
reun10n_frontend_dir = os.path.join(base_dir, "Reun10n", "frontend")
frontend_dir = os.getenv("FRONTEND_DIR") or (
    reun10n_frontend_dir if os.path.isdir(reun10n_frontend_dir) else default_frontend_dir
)

if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

# Mount audio directory
os.makedirs(settings.tts_output_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=settings.tts_output_dir), name="audio")


@app.get("/", response_class=HTMLResponse)
def admin_page(request: Request):
    """Serve the unified admin interface."""
    unified_path = os.path.join(frontend_dir, "unified.html")
    if os.path.exists(unified_path):
        with open(unified_path, "r") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to template if unified.html is missing
    if templates:
        return templates.TemplateResponse(
            "admin.html",
            {
                "request": request,
                "running": chat_session.is_running(),
                "topic": chat_session.topic,
            },
        )
    
    return HTMLResponse(content="<h1>ChatMode</h1><p>Please configure frontend directory</p>")


@app.post("/start")
def start_session(topic: str = Form("")):
    """Start a new chat session."""
    topic = topic.strip()
    if not topic:
        return RedirectResponse(url="/", status_code=303)
    if chat_session.start(topic):
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
def stop_session():
    """Stop the current chat session."""
    chat_session.stop()
    return RedirectResponse(url="/", status_code=303)


@app.post("/memory/clear")
def clear_memory():
    """Clear session memory."""
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
    """Inject a message into the conversation."""
    chat_session.inject_message(sender, content)
    return {"status": "sent"}


@app.get("/status")
def status(request: Request):
    """Get session status and recent messages."""
    # Sanitize audio paths to URLs
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
            "last_messages": messages,
        }
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "framework": "chatmode"
    }
