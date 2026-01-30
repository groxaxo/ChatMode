@echo off
REM ChatMode Auto-Installer for Windows v3.0
REM This script automatically installs ChatMode with conda environment
REM Features: Multi-provider support, auto model discovery from environment

setlocal EnableDelayedExpansion

echo ============================================
echo     ChatMode Auto-Installer v3.0
echo     AI Agent Orchestration System
echo     with Auto Provider Discovery
echo ============================================
echo.

REM Check if conda is installed
where conda >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Conda is not installed!
    echo Please install Miniconda or Anaconda first:
    echo   - Miniconda: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo [INFO] Conda found
echo.

REM Set variables
set "CONDA_ENV_NAME=chatmode"
set "PROJECT_DIR=%CD%"
set "DEFAULT_PORT=8002"
set "SCAN_SHELL_CONFIGS=false"

echo [INFO] Setting up conda environment: %CONDA_ENV_NAME%

REM Check if environment exists
conda env list | findstr /C:"%CONDA_ENV_NAME% " >nul
if %errorlevel% equ 0 (
    echo [WARNING] Conda environment '%CONDA_ENV_NAME%' already exists
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /I "!RECREATE!"=="y" (
        echo [INFO] Removing existing environment...
        call conda env remove -n %CONDA_ENV_NAME% -y
    ) else (
        echo [INFO] Using existing environment
        goto :SETUP_DIRS
    )
)

echo [INFO] Creating conda environment from environment.yml...
call conda env create -f environment.yml
if %errorlevel% neq 0 (
    echo [ERROR] Failed to create conda environment
    pause
    exit /b 1
)

echo [SUCCESS] Conda environment created

:SETUP_DIRS
echo.
echo [INFO] Creating required directories...
if not exist "data\chroma" mkdir "data\chroma"
if not exist "tts_out" mkdir "tts_out"
if not exist "logs" mkdir "logs"
echo [SUCCESS] Directories created

echo.
echo [INFO] Installing additional dependencies...
call conda activate %CONDA_ENV_NAME%
pip install "bcrypt>=4.0.0,<4.1.0" passlib==1.7.4
echo [SUCCESS] Dependencies installed

echo.
echo ============================================
echo     Provider Auto-Discovery Feature
echo ============================================
echo.
echo The new provider system can automatically detect API keys
echo from environment variables and system settings.
echo.
echo Supported providers: OpenAI, Fireworks AI, DeepSeek, xAI (Grok),
echo                      Anthropic, Ollama, LM Studio, vLLM
echo.

set /p SCAN_ENV="Would you like to scan system environment for API keys? (y/N): "
if /I "%SCAN_ENV%"=="y" (
    set "SCAN_SHELL_CONFIGS=true"
    echo [INFO] Will scan environment on startup...
    
    REM Check for common API keys in environment
    echo [INFO] Checking for API keys in system environment...
    set FOUND_KEYS=
    
    if defined OPENAI_API_KEY (
        echo    [OK] Found OPENAI_API_KEY
        set FOUND_KEYS=!FOUND_KEYS! OpenAI
    )
    if defined FIREWORKS_API_KEY (
        echo    [OK] Found FIREWORKS_API_KEY
        set FOUND_KEYS=!FOUND_KEYS! Fireworks
    )
    if defined DEEPSEEK_API_KEY (
        echo    [OK] Found DEEPSEEK_API_KEY
        set FOUND_KEYS=!FOUND_KEYS! DeepSeek
    )
    if defined XAI_API_KEY (
        echo    [OK] Found XAI_API_KEY
        set FOUND_KEYS=!FOUND_KEYS! xAI
    )
    if defined ANTHROPIC_API_KEY (
        echo    [OK] Found ANTHROPIC_API_KEY
        set FOUND_KEYS=!FOUND_KEYS! Anthropic
    )
    
    if defined FOUND_KEYS (
        echo [SUCCESS] Detected API keys for:!FOUND_KEYS!
    ) else (
        echo [WARNING] No API keys found in system environment
        echo    You can add them later in System Properties -
        echo    Advanced -
        echo    Environment Variables
    )
) else (
    set "SCAN_SHELL_CONFIGS=false"
    echo [INFO] Skipping environment scan (you can enable later in .env)
)

echo.
echo [INFO] Setting up environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo [SUCCESS] Created .env from .env.example
    ) else (
        echo [WARNING] No .env.example found, creating comprehensive .env
        (
            echo # ChatMode Configuration v3.0
            echo # Multi-Provider AI System with Auto-Discovery
            echo.
            echo # ============================================================================
            echo # Provider Auto-Discovery Settings
            echo # ============================================================================
            echo # Set to 'true' to scan system environment for API keys on startup
            echo SCAN_SHELL_CONFIGS=false
            echo.
            echo # ============================================================================
            echo # LLM Provider Configuration
            echo # ============================================================================
            echo # The system automatically detects and syncs models from all configured providers!
            echo # Just set the API keys below and the system will:
            echo # 1. Auto-detect the provider type from the URL
            echo # 2. Fetch available models from the provider
            echo # 3. Keep models in sync automatically
            echo.
            echo # === OpenAI (GPT-4, GPT-3.5, etc.) ===
            echo # Get your API key from https://platform.openai.com/api-keys
            echo OPENAI_API_KEY=
            echo OPENAI_BASE_URL=https://api.openai.com/v1
            echo OPENAI_MODEL=gpt-4o-mini
            echo.
            echo # === Ollama (Local LLM - FREE!) ===
            echo # Install: https://ollama.com
            echo # The system will auto-sync ALL your installed Ollama models!
            echo OLLAMA_BASE_URL=http://localhost:11434
            echo.
            echo # === Fireworks AI (DeepSeek, Llama, etc.) ===
            echo # Get your API key from https://fireworks.ai/account/api-keys
            echo FIREWORKS_API_KEY=
            echo.
            echo # === DeepSeek (DeepSeek-V3, DeepSeek-Coder) ===
            echo # Get your API key from https://platform.deepseek.com/api_keys
            echo DEEPSEEK_API_KEY=
            echo.
            echo # === xAI (Grok-2, Grok-Beta) ===
            echo # Get your API key from https://console.x.ai
            echo XAI_API_KEY=
            echo.
            echo # === Anthropic (Claude models) ===
            echo # Get your API key from https://console.anthropic.com/settings/keys
            echo ANTHROPIC_API_KEY=
            echo.
            echo # === LM Studio (Local GUI for models) ===
            echo # Download from https://lmstudio.ai
            echo LMSTUDIO_BASE_URL=http://localhost:1234/v1
            echo.
            echo # === vLLM (Self-hosted model serving) ===
            echo # Deploy your own models with vLLM
            echo VLLM_BASE_URL=http://localhost:8000/v1
            echo.
            echo # === Custom Providers ===
            echo # Add any OpenAI-compatible provider:
            echo # PROVIDER_<NAME>_URL=https://api.example.com/v1
            echo # PROVIDER_<NAME>_KEY=your-api-key
            echo.
            echo # ============================================================================
            echo # Embedding Configuration (for semantic memory)
            echo # ============================================================================
            echo EMBEDDING_PROVIDER=ollama
            echo EMBEDDING_MODEL=nomic-embed-text
            echo EMBEDDING_BASE_URL=http://localhost:11434
            echo EMBEDDING_API_KEY=
            echo.
            echo # ============================================================================
            echo # Text-to-Speech (TTS) Configuration
            echo # ============================================================================
            echo TTS_ENABLED=false
            echo TTS_BASE_URL=https://api.openai.com/v1
            echo TTS_API_KEY=
            echo TTS_MODEL=tts-1
            echo TTS_VOICE=alloy
            echo TTS_OUTPUT_DIR=./tts_out
            echo.
            echo # ============================================================================
            echo # Storage Configuration
            echo # ============================================================================
            echo CHROMA_DIR=./data/chroma
            echo DATABASE_URL=sqlite:///./data/chatmode.db
            echo.
            echo # ============================================================================
            echo # Conversation Settings
            echo # ============================================================================
            echo MAX_CONTEXT_TOKENS=32000
            echo MAX_OUTPUT_TOKENS=512
            echo MEMORY_TOP_K=5
            echo HISTORY_MAX_MESSAGES=20
            echo TEMPERATURE=0.9
            echo SLEEP_SECONDS=2
            echo.
            echo # ============================================================================
            echo # Admin & Security Settings
            echo # ============================================================================
            echo ADMIN_USE_LLM=true
            echo SECRET_KEY=change-this-in-production
            echo ALLOWED_ORIGINS=*
            echo VERBOSE=false
        ) > .env
        echo [SUCCESS] Created comprehensive .env file
    )
    
    REM Update SCAN_SHELL_CONFIGS if user chose to scan
    if "%SCAN_SHELL_CONFIGS%"=="true" (
        powershell -Command "(Get-Content .env) -replace 'SCAN_SHELL_CONFIGS=false', 'SCAN_SHELL_CONFIGS=true' | Set-Content .env"
        echo [SUCCESS] Enabled environment scanning in .env
    )
    
    echo [WARNING] Please edit .env with your API keys before starting
) else (
    echo [INFO] .env file already exists, skipping
    REM Still update SCAN_SHELL_CONFIGS if user chose to scan
    if "%SCAN_SHELL_CONFIGS%"=="true" (
        findstr /C:"SCAN_SHELL_CONFIGS=true" .env >nul
        if %errorlevel% neq 0 (
            echo. >> .env
            echo # Scan system environment for API keys >> .env
            echo SCAN_SHELL_CONFIGS=true >> .env
            echo [SUCCESS] Updated .env to enable environment scanning
        )
    )
)

echo.
echo [INFO] Initializing database...
call conda activate %CONDA_ENV_NAME%
python bootstrap_admin.py
if %errorlevel% neq 0 (
    echo [ERROR] Database initialization failed
    pause
    exit /b 1
)
echo [SUCCESS] Database initialized

echo.
echo [INFO] Verifying agent configuration...
if not exist "agent_config.json" (
    echo [WARNING] agent_config.json not found, creating default...
    (
        echo {
        echo   "agents": [
        echo     {
        echo       "name": "lawyer",
        echo       "file": "profiles/lawyer.json"
        echo     },
        echo     {
        echo       "name": "crook",
        echo       "file": "profiles/crook.json"
        echo     }
        echo   ]
        echo }
    ) > agent_config.json
    echo [SUCCESS] Created default agent_config.json
) else (
    echo [SUCCESS] agent_config.json found
)

echo.
echo [INFO] Creating launcher script...
(
    echo @echo off
    echo REM ChatMode Launcher Script v3.0
    echo REM Auto-generated by autoinstall.bat
    echo REM Features: Multi-provider support, auto model discovery
    echo.
    echo cd /d "%PROJECT_DIR%"
    echo call conda activate %CONDA_ENV_NAME%
    echo.
    echo echo ============================================
    echo echo     ChatMode Server v3.0
echo echo     Multi-Provider AI System
echo echo ============================================
    echo echo.
    echo echo [INFO] Starting server on http://localhost:%DEFAULT_PORT%
    echo echo [INFO] Default login: admin / admin
    echo echo.
    echo echo [FEATURE] Provider System:
    echo echo   - Auto-discovers models from configured providers
    echo echo   - Supports: OpenAI, Fireworks, DeepSeek, xAI, Ollama, etc.
    echo echo   - API docs: http://localhost:%DEFAULT_PORT%/docs
    echo echo.
    echo echo [HELP] To add providers:
    echo echo   1. Edit .env file with your API keys
    echo echo   2. Or set Windows environment variables
    echo echo   3. Restart the server
    echo echo.
    echo echo Press Ctrl+C to stop
    echo echo.
    echo.
    echo python -m uvicorn web_admin:app --host 0.0.0.0 --port %DEFAULT_PORT% --reload
    echo.
    echo pause
) > start.bat
echo [SUCCESS] Created start.bat launcher

echo.
echo ============================================
echo     Installation Complete! 
echo ============================================
echo.
echo Provider Setup Guide:
echo ---------------------
echo The new provider system supports automatic model discovery!
echo.
echo Quick Setup Options:
echo.
echo 1. .env file (recommended):
echo    Edit .env and add your API keys:
echo    OPENAI_API_KEY=sk-your-key-here
echo    FIREWORKS_API_KEY=fw-your-key-here
echo.
echo 2. Windows Environment Variables:
echo    Set via System Properties -^> Advanced -^> Environment Variables
echo    Then enable SCAN_SHELL_CONFIGS=true in .env
echo.
echo 3. Via API (after server starts):
echo    POST http://localhost:%DEFAULT_PORT%/providers
echo    {"name": "my-openai", "base_url": "...", "api_key": "..."}
echo.
echo Supported Providers:
echo    * OpenAI (GPT-4, GPT-3.5)
echo    * Fireworks AI (DeepSeek, Llama)
echo    * DeepSeek (DeepSeek-V3)
echo    * xAI/Grok (Grok-2)
echo    * Anthropic (Claude)
echo    * Ollama (Local - FREE!)
echo    * LM Studio (Local GUI)
echo    * vLLM (Self-hosted)
echo    * Any OpenAI-compatible API
echo.
echo Quick Start:
echo   1. Edit .env file with your API keys
if "%SCAN_SHELL_CONFIGS%"=="true" (
echo      [NOTE] Environment scanning is ENABLED - system variables will be detected
)
echo   2. Start the server: start.bat
echo   3. Open browser: http://localhost:%DEFAULT_PORT%
echo   4. Login with: admin / admin
echo.
echo Provider Management:
echo   * View providers: GET http://localhost:%DEFAULT_PORT%/providers
echo   * Sync models: POST http://localhost:%DEFAULT_PORT%/providers/sync-all
echo   * API documentation: http://localhost:%DEFAULT_PORT%/docs
echo.
echo Note: Make sure Ollama is running if using local models
echo.

set /p START_NOW="Would you like to start ChatMode now? (y/N): "
if /I "%START_NOW%"=="y" (
    echo.
    call start.bat
) else (
    echo.
    echo You can start ChatMode anytime by running: start.bat
    pause
)
