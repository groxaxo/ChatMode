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
from .logger_config import setup_logging, get_logger

# Setup logging
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ChatMode - AI Multi-Agent Platform",
    description="Manage and orchestrate AI agent conversations with multiple LLM providers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Load settings
settings = load_settings()
chat_session = ChatSession(settings)


# Initialize database and providers on startup
@app.on_event("startup")
async def startup_event():
    # Setup logging with settings from config
    setup_logging(
        log_level=settings.log_level,
        log_dir=settings.log_dir,
        log_to_file=True,
        log_to_console=True,
    )

    logger.info("🚀 Starting ChatMode application")
    init_db()
    logger.info("✅ Database initialized")

    # Initialize providers from environment variables
    try:
        from .database import SessionLocal
        from .services import initialize_providers, load_providers_from_db
        from .providers import load_providers_from_db as load_provider_registry

        db = SessionLocal()
        try:
            # Check if user wants to scan shell configs (.bashrc, .zshrc)
            scan_shell = os.getenv("SCAN_SHELL_CONFIGS", "false").lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

            if scan_shell:
                logger.info(
                    "🔍 Scanning shell config files (.bashrc, .zshrc) for API keys..."
                )

            # Discover and create providers from environment
            result = await initialize_providers(
                db, auto_sync=True, scan_shell_configs=scan_shell
            )

            if result["total_discovered"] > 0:
                logger.info(f"✅ Initialized {result['total_discovered']} providers")

                if result.get("scanned_files"):
                    logger.info(f"📁 Scanned: {', '.join(result['scanned_files'])}")

                for provider_result in result["providers"]:
                    action = provider_result.get("action", "unknown")
                    name = provider_result.get("name", "unknown")
                    source = provider_result.get("source", "environment")

                    if action == "error":
                        logger.error(f"⚠️  {name}: {provider_result.get('error')}")
                    else:
                        sync_info = provider_result.get("sync", {})
                        source_indicator = "📄" if source == "shell_config" else "🔧"
                        if sync_info.get("success"):
                            logger.info(
                                f"{source_indicator} {name}: {sync_info.get('total_models', 0)} models"
                            )
                        else:
                            logger.warning(
                                f"⚠️  {name}: sync failed - {sync_info.get('error', 'unknown error')}"
                            )
            else:
                logger.warning(
                    "ℹ️  No providers configured. Set API keys in .env or .bashrc"
                )
                logger.info(
                    "Supported: OPENAI_API_KEY, FIREWORKS_API_KEY, DEEPSEEK_API_KEY, etc."
                )

            # Load providers into runtime registry
            load_provider_registry(db)
            logger.info("✅ Providers loaded into runtime registry")

        finally:
            db.close()
    except Exception as e:
        logger.error(f"⚠️  Provider initialization failed: {e}", exc_info=True)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    from .logger_config import (
        get_correlation_id,
        set_correlation_id,
        clear_correlation_id,
    )
    import time

    # Set correlation ID for this request
    correlation_id = request.headers.get("X-Correlation-ID") or set_correlation_id()

    start_time = time.time()
    method = request.method
    url = str(request.url)

    # Log request start
    logger.debug(
        f"➡️  Request started: {method} {url}",
        extra={
            "correlation_id": correlation_id,
            "method": method,
            "url": url,
            "client_host": request.client.host if request.client else None,
        },
    )

    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000

        # Log response
        status_code = response.status_code
        log_level = (
            logging.DEBUG
            if status_code < 400
            else logging.WARNING
            if status_code < 500
            else logging.ERROR
        )

        logger.log(
            log_level,
            f"⬅️  Response: {method} {url} - {status_code} ({duration:.1f}ms)",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "url": url,
                "status_code": status_code,
                "duration_ms": duration,
            },
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(
            f"💥 Request failed: {method} {url} - {e} ({duration:.1f}ms)",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "url": url,
                "error": str(e),
                "duration_ms": duration,
            },
            exc_info=True,
        )
        raise
    finally:
        clear_correlation_id()


# Register API routes
try:
    from .routes import all_routers
    from .routes.advanced import set_global_chat_session

    # Set global session for advanced routes
    set_global_chat_session(chat_session)

    for router in all_routers:
        app.include_router(router)
    logger.info(f"✅ Loaded {len(all_routers)} API route modules")
except ImportError as e:
    logger.warning(f"Could not load API routes: {e}")

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
    reun10n_frontend_dir
    if os.path.isdir(reun10n_frontend_dir)
    else default_frontend_dir
)

if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

# Mount audio directories
os.makedirs(settings.tts_output_dir, exist_ok=True)
os.makedirs("./data/audio", exist_ok=True)

# Legacy TTS output directory
app.mount(
    "/audio/legacy", StaticFiles(directory=settings.tts_output_dir), name="audio_legacy"
)
# New audio storage with session-based organization
app.mount("/audio", StaticFiles(directory="./data/audio"), name="audio")


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

    return HTMLResponse(
        content="<h1>ChatMode</h1><p>Please configure frontend directory</p>"
    )


@app.post("/start")
async def start_session(topic: str = Form("")):
    """Start a new chat session."""
    topic = topic.strip()
    if not topic:
        return RedirectResponse(url="/", status_code=303)
    if await chat_session.start(topic):
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
async def stop_session():
    """Stop the current chat session."""
    await chat_session.stop()
    return RedirectResponse(url="/", status_code=303)


@app.post("/memory/clear")
def clear_memory():
    """Clear session memory."""
    chat_session.clear_memory()
    return {"status": "memory_cleared"}


@app.post("/resume")
async def resume_session():
    """Resume a paused session."""
    if await chat_session.resume():
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
async def status(request: Request):
    """Get session status and recent messages."""
    # Sanitize audio paths to URLs
    messages = []
    base_url = str(request.base_url).rstrip("/")

    for msg in chat_session.last_messages:
        new_msg = msg.copy()

        # Handle legacy audio paths
        if new_msg.get("audio") and isinstance(new_msg["audio"], str):
            if not new_msg["audio"].startswith("http"):
                # Convert absolute path to relative URL
                filename = os.path.basename(new_msg["audio"])
                new_msg["audio"] = f"{base_url}/audio/{filename}"

        # Handle new audio_url field
        if new_msg.get("audio_url") and isinstance(new_msg["audio_url"], str):
            if not new_msg["audio_url"].startswith("http"):
                new_msg["audio_url"] = f"{base_url}{new_msg['audio_url']}"

        messages.append(new_msg)

    # Get agent states
    agent_states = await chat_session.get_agent_states()

    return JSONResponse(
        {
            "running": chat_session.is_running(),
            "topic": chat_session.topic,
            "session_id": chat_session.session_id,
            "last_messages": messages,
            "agent_states": agent_states,
        }
    )


# ============================================================================
# Agent Control Endpoints
# ============================================================================


@app.post("/agents/{agent_name}/pause")
async def pause_agent(agent_name: str, reason: str = Form(None)):
    """Pause a specific agent."""
    success = await chat_session.pause_agent(agent_name, reason)
    if success:
        return {"status": "paused", "agent": agent_name, "reason": reason}
    return JSONResponse(
        {
            "status": "failed",
            "agent": agent_name,
            "reason": "Agent not found or already paused",
        },
        status_code=400,
    )


@app.post("/agents/{agent_name}/resume")
async def resume_agent(agent_name: str):
    """Resume a paused agent."""
    success = await chat_session.resume_agent(agent_name)
    if success:
        return {"status": "resumed", "agent": agent_name}
    return JSONResponse(
        {
            "status": "failed",
            "agent": agent_name,
            "reason": "Agent not found or not paused",
        },
        status_code=400,
    )


@app.post("/agents/{agent_name}/stop")
async def stop_agent(agent_name: str, reason: str = Form(None)):
    """Stop a specific agent."""
    success = await chat_session.stop_agent(agent_name, reason)
    if success:
        return {"status": "stopped", "agent": agent_name, "reason": reason}
    return JSONResponse(
        {
            "status": "failed",
            "agent": agent_name,
            "reason": "Agent not found or already stopped",
        },
        status_code=400,
    )


@app.post("/agents/{agent_name}/finish")
async def finish_agent(agent_name: str, reason: str = Form(None)):
    """Mark an agent as finished."""
    success = await chat_session.finish_agent(agent_name, reason)
    if success:
        return {"status": "finished", "agent": agent_name, "reason": reason}
    return JSONResponse(
        {
            "status": "failed",
            "agent": agent_name,
            "reason": "Agent not found or already finished",
        },
        status_code=400,
    )


@app.post("/agents/{agent_name}/restart")
async def restart_agent(agent_name: str):
    """Restart a stopped or finished agent."""
    success = await chat_session.restart_agent(agent_name)
    if success:
        return {"status": "restarted", "agent": agent_name}
    return JSONResponse(
        {
            "status": "failed",
            "agent": agent_name,
            "reason": "Agent not found or not stopped/finished",
        },
        status_code=400,
    )


@app.get("/agents/states")
async def get_agent_states():
    """Get the current state of all agents."""
    states = await chat_session.get_agent_states()
    return {"agent_states": states}


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0", "framework": "chatmode"}
