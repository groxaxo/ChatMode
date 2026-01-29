import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from config import load_settings
from session import ChatSession
from database import init_db


app = FastAPI(
    title="ChatMode Admin",
    description="AI Multi-Agent Conversation Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
settings = load_settings()
chat_session = ChatSession(settings)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

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
    from routes import all_routers
    for router in all_routers:
        app.include_router(router)
except ImportError as e:
    print(f"Warning: Could not load API routes: {e}")

templates = Jinja2Templates(directory="templates")

base_dir = os.path.dirname(__file__)
default_frontend_dir = os.path.join(base_dir, "frontend")
reun10n_frontend_dir = os.path.join(base_dir, "Reun10n", "frontend")
frontend_dir = os.getenv("FRONTEND_DIR") or (
    reun10n_frontend_dir if os.path.isdir(reun10n_frontend_dir) else default_frontend_dir
)

app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")
# Mount audio directory
os.makedirs(settings.tts_output_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=settings.tts_output_dir), name="audio")


@app.get("/", response_class=HTMLResponse)
def admin_page(request: Request):
    # Serve new unified app frontend
    app_path = os.path.join(frontend_dir, "app.html")
    if os.path.exists(app_path):
        with open(app_path, "r") as f:
            return HTMLResponse(content=f.read())
    
    # Fallback to old unified
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
    topic = topic.strip()
    if not topic:
        return RedirectResponse(url="/", status_code=303)
    if chat_session.start(topic):
        return RedirectResponse(url="/", status_code=303)
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
def stop_session():
    chat_session.stop()
    return RedirectResponse(url="/", status_code=303)


@app.post("/memory/clear")
def clear_memory():
    chat_session.clear_memory()
    return {"status": "memory_cleared"}


@app.post("/resume")
def resume_session():
    if chat_session.resume():
        return {"status": "resumed"}
    return JSONResponse(
        {"status": "failed", "reason": "Already running or no topic"}, status_code=400
    )


@app.post("/messages")
def send_message(content: str = Form(...), sender: str = Form("Admin")):
    chat_session.inject_message(sender, content)
    return {"status": "sent"}


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


@app.get("/agents")
def list_agents():
    """List all available agents."""
    import json
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "agent_config.json")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        agents_info = []
        for agent_conf in config.get("agents", []):
            agent_file = agent_conf["file"]
            
            # Security: Validate file path is within profiles directory
            abs_file_path = os.path.abspath(agent_file)
            profiles_dir = os.path.abspath(os.path.join(base_dir, "profiles"))
            if not abs_file_path.startswith(profiles_dir):
                print(f"Warning: Skipping agent file outside profiles directory: {agent_file}")
                continue
            
            if not os.path.exists(abs_file_path):
                continue
                
            with open(abs_file_path, "r") as f:
                profile = json.load(f)

            agents_info.append(
                {
                    "name": profile.get("name", agent_conf.get("name")),
                    "model": profile.get("model", "default"),
                    "api": profile.get("api", "openai"),
                    "file": agent_conf["file"],
                }
            )

        return {"agents": agents_info}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/agents/{agent_name}")
def get_agent_profile(agent_name: str):
    """Get full agent profile."""
    import json
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "agent_config.json")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)

        for agent_conf in config.get("agents", []):
            if agent_conf.get("name") == agent_name:
                agent_file = agent_conf["file"]
                
                # Security: Validate file path is within profiles directory
                abs_file_path = os.path.abspath(agent_file)
                profiles_dir = os.path.abspath(os.path.join(base_dir, "profiles"))
                if not abs_file_path.startswith(profiles_dir):
                    return JSONResponse({"error": "Invalid agent file path"}, status_code=400)
                
                if not os.path.exists(abs_file_path):
                    return JSONResponse({"error": "Agent file not found"}, status_code=404)
                    
                with open(abs_file_path, "r") as f:
                    profile = json.load(f)
                return profile

        return JSONResponse({"error": "Agent not found"}, status_code=404)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/agents/{agent_name}")
async def update_agent_profile(agent_name: str, request: Request):
    """Update agent profile."""
    import json
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, "agent_config.json")

    try:
        # Load config
        with open(config_path, "r") as f:
            config = json.load(f)

        # Find agent file
        agent_file = None
        for agent_conf in config.get("agents", []):
            if agent_conf.get("name") == agent_name:
                agent_file = agent_conf["file"]
                break

        if not agent_file:
            return JSONResponse({"error": "Agent not found"}, status_code=404)

        # Security: Validate file path is within profiles directory
        abs_file_path = os.path.abspath(agent_file)
        profiles_dir = os.path.abspath(os.path.join(base_dir, "profiles"))
        if not abs_file_path.startswith(profiles_dir):
            return JSONResponse({"error": "Invalid agent file path"}, status_code=400)

        # Load current profile
        if not os.path.exists(abs_file_path):
            return JSONResponse({"error": "Agent file not found"}, status_code=404)
            
        with open(abs_file_path, "r") as f:
            profile = json.load(f)

        # Get update data
        update_data = await request.json()

        # Validate and update fields
        if "conversing" in update_data:
            if not isinstance(update_data["conversing"], str):
                return JSONResponse({"error": "conversing must be a string"}, status_code=400)
            profile["conversing"] = update_data["conversing"]
            
        if "max_tokens" in update_data:
            max_tokens = update_data["max_tokens"]
            if not isinstance(max_tokens, int) or max_tokens < 1 or max_tokens > 10000:
                return JSONResponse({"error": "max_tokens must be between 1 and 10000"}, status_code=400)
            if "params" not in profile:
                profile["params"] = {}
            profile["params"]["max_tokens"] = max_tokens
            
        if "temperature" in update_data:
            temperature = update_data["temperature"]
            if not isinstance(temperature, (int, float)) or temperature < 0 or temperature > 2:
                return JSONResponse({"error": "temperature must be between 0 and 2"}, status_code=400)
            if "params" not in profile:
                profile["params"] = {}
            profile["params"]["temperature"] = float(temperature)

        # Save profile
        with open(abs_file_path, "w") as f:
            json.dump(profile, f, indent=2)

        return {"status": "success", "agent": agent_name}

    except json.JSONDecodeError:
        return JSONResponse({"error": "Invalid JSON in request body"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
