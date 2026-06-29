"""
ChatMode Main Application

Single entrypoint for the ChatMode API and admin interface.
Combines all routes and serves the unified frontend.
"""

import contextlib
import logging
import os
import time
from typing import Optional

from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .config import load_settings
from .database import init_db, get_db
from .logger_config import get_logger, setup_logging
from .session import ChatSession
from . import crud

# Setup logging
logger = get_logger(__name__)

# Load settings
settings = load_settings()


# Create FastAPI app with lifespan
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup logging with settings from config
    setup_logging(
        log_level=settings.log_level,
        log_dir=settings.log_dir,
        log_to_file=True,
        log_to_console=True,
    )

    # Warn about insecure defaults in use
    if os.getenv("SECRET_KEY", "dev-secret-key-change-in-production") == "dev-secret-key-change-in-production":
        logger.warning(
            "⚠️  SECRET_KEY is using the default value — set a strong SECRET_KEY in production!"
        )

    logger.info("🚀 Starting ChatMode application")
    init_db()
    logger.info("✅ Database initialized")

    # Initialize providers from environment variables
    try:
        from .database import SessionLocal
        from .providers import load_providers_from_db
        from .services import initialize_providers

        db = SessionLocal()
        try:
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

            load_providers_from_db(db)
            logger.info("✅ Providers loaded into runtime registry")

        finally:
            db.close()
    except Exception as e:
        logger.error(f"⚠️  Provider initialization failed: {e}", exc_info=True)
    yield


app = FastAPI(
    title="ChatMode - AI Multi-Agent Platform",
    description="Manage and orchestrate AI agent conversations with multiple LLM providers",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

chat_session = ChatSession(settings)


# CORS — read allowed origins from environment; default to wildcard for development
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    from .logger_config import (
        clear_correlation_id,
        get_correlation_id,
        set_correlation_id,
    )

    correlation_id = request.headers.get("X-Correlation-ID") or set_correlation_id()

    start_time = time.time()
    method = request.method
    url = str(request.url)

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
    from .routes.filter import set_filter_session

    set_global_chat_session(chat_session)
    set_filter_session(chat_session)

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

# React frontend directory (built version)
react_dist_dir = os.path.join(base_dir, "frontend", "dist")
react_static_path = "/react-static"

if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

if os.path.exists(react_dist_dir):
    app.mount(
        react_static_path, StaticFiles(directory=react_dist_dir), name="react_static"
    )

# Mount audio directories
os.makedirs(settings.tts_output_dir, exist_ok=True)
os.makedirs("./data/audio", exist_ok=True)

app.mount(
    "/audio/legacy", StaticFiles(directory=settings.tts_output_dir), name="audio_legacy"
)
app.mount("/audio", StaticFiles(directory="./data/audio"), name="audio")


@app.get("/", response_class=HTMLResponse)
def admin_page(request: Request):
    """
    Serve the default admin interface (React frontend).

    DEFAULT FRONTEND: React Application
    Location: frontend/react-app/dist/
    Build command: cd frontend/react-app && npm run build
    """
    react_index = os.path.join(react_dist_dir, "index.html")
    if os.path.exists(react_index):
        with open(react_index, "r") as f:
            content = f.read()
            content = content.replace('"/assets/', f'"{react_static_path}/assets/')
            content = content.replace('"/vite.svg"', f'"{react_static_path}/vite.svg"')
            return HTMLResponse(content=content)

    return HTMLResponse(
        content="""<h1>ChatMode - Frontend Not Built</h1>
        <p>The React frontend needs to be built. Run:</p>
        <pre>cd frontend/react-app && npm run build</pre>
        <p>Then restart the server.</p>""",
        status_code=503,
    )


@app.get("/status")
async def status(request: Request):
    """Get session status and recent messages."""
    messages = []
    base_url = str(request.base_url).rstrip("/")

    for msg in chat_session.last_messages:
        new_msg = msg.copy()

        if new_msg.get("audio") and isinstance(new_msg["audio"], str):
            if not new_msg["audio"].startswith("http"):
                filename = os.path.basename(new_msg["audio"])
                new_msg["audio"] = f"{base_url}/audio/{filename}"

        if new_msg.get("audio_url") and isinstance(new_msg["audio_url"], str):
            if not new_msg["audio_url"].startswith("http"):
                new_msg["audio_url"] = f"{base_url}{new_msg['audio_url']}"

        messages.append(new_msg)

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


class AgentActionRequest(BaseModel):
    reason: Optional[str] = None


async def _agent_action_response(
    success: bool,
    status_name: str,
    agent_name: str,
    reason: Optional[str],
    fail_msg: str,
) -> JSONResponse:
    """Build a consistent response for agent control actions."""
    if success:
        agent_states = await chat_session.get_agent_states()
        return JSONResponse(
            {
                "status": status_name,
                "agent": agent_name,
                "reason": reason,
                "agent_state": agent_states.get(agent_name, {}),
            }
        )
    return JSONResponse(
        {"status": "failed", "agent": agent_name, "reason": fail_msg},
        status_code=400,
    )


@app.post("/agents/{agent_name}/pause")
async def pause_agent(agent_name: str, body: AgentActionRequest = AgentActionRequest()):
    """Pause a specific agent."""
    success = await chat_session.pause_agent(agent_name, body.reason)
    return await _agent_action_response(
        success, "paused", agent_name, body.reason,
        "Agent not found or already paused",
    )


@app.post("/agents/{agent_name}/resume")
async def resume_agent(agent_name: str):
    """Resume a paused agent."""
    success = await chat_session.resume_agent(agent_name)
    return await _agent_action_response(
        success, "resumed", agent_name, None,
        "Agent not found or not paused",
    )


@app.post("/agents/{agent_name}/stop")
async def stop_agent(agent_name: str, body: AgentActionRequest = AgentActionRequest()):
    """Stop a specific agent."""
    success = await chat_session.stop_agent(agent_name, body.reason)
    return await _agent_action_response(
        success, "stopped", agent_name, body.reason,
        "Agent not found or already stopped",
    )


@app.post("/agents/{agent_name}/finish")
async def finish_agent(agent_name: str, body: AgentActionRequest = AgentActionRequest()):
    """Mark an agent as finished."""
    success = await chat_session.finish_agent(agent_name, body.reason)
    return await _agent_action_response(
        success, "finished", agent_name, body.reason,
        "Agent not found or already finished",
    )


@app.post("/agents/{agent_name}/restart")
async def restart_agent(agent_name: str):
    """Restart a stopped or finished agent."""
    success = await chat_session.restart_agent(agent_name)
    return await _agent_action_response(
        success, "restarted", agent_name, None,
        "Agent not found or not stopped/finished",
    )


@app.get("/agents/states")
async def get_agent_states():
    """Get the current state of all agents."""
    states = await chat_session.get_agent_states()
    return JSONResponse({"agent_states": states})


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


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0", "framework": "chatmode"}
