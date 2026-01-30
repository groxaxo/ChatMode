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

    return HTMLResponse(
        content="<h1>ChatMode</h1><p>Please configure frontend directory</p>"
    )


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
    return {"status": "healthy", "version": "2.0.0", "framework": "chatmode"}
