#!/bin/bash
# ChatMode Auto-Installer Script v3.0
# This script automatically installs ChatMode with conda environment,
# initializes the database, sets up the provider system, and prepares for launch.
#
# NEW in v3.0:
# - Automatic provider discovery from .bashrc/.zshrc
# - Multi-provider support (OpenAI, Fireworks, DeepSeek, xAI, Ollama, etc.)
# - Auto-sync models from configured providers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
CONDA_ENV_NAME="chatmode"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PORT=8002

# Provider API key environment variables
PROVIDER_ENVS=(
    "OPENAI_API_KEY:OpenAI"
    "FIREWORKS_API_KEY:Fireworks AI"
    "DEEPSEEK_API_KEY:DeepSeek"
    "XAI_API_KEY:xAI (Grok)"
    "ANTHROPIC_API_KEY:Anthropic"
)

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        ChatMode Auto-Installer v3.0                           ║${NC}"
echo -e "${BLUE}║   AI Agent Orchestration System with Auto Provider Discovery  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_feature() {
    echo -e "${CYAN}[FEATURE]${NC} $1"
}

# Check if conda is installed
check_conda() {
    print_status "Checking for conda..."
    if command -v conda &> /dev/null; then
        print_success "Conda found at: $(which conda)"
        return 0
    else
        print_error "Conda is not installed!"
        echo "Please install Miniconda or Anaconda first:"
        echo "  - Miniconda: https://docs.conda.io/en/latest/miniconda.html"
        echo "  - Anaconda: https://www.anaconda.com/download"
        exit 1
    fi
}

# Create conda environment
setup_conda_env() {
    print_status "Setting up conda environment: $CONDA_ENV_NAME"
    
    # Check if environment already exists
    if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
        print_warning "Conda environment '$CONDA_ENV_NAME' already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Removing existing environment..."
            conda env remove -n $CONDA_ENV_NAME -y
        else
            print_status "Using existing environment"
            return 0
        fi
    fi
    
    print_status "Creating conda environment from environment.yml..."
    cd "$PROJECT_DIR"
    conda env create -f environment.yml
    print_success "Conda environment created successfully"
}

# Install additional dependencies
install_deps() {
    print_status "Installing additional dependencies..."
    
    # Activate environment
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $CONDA_ENV_NAME
    
    # Fix bcrypt compatibility
    print_status "Fixing bcrypt compatibility..."
    pip install 'bcrypt>=4.0.0,<4.1.0' passlib==1.7.4
    
    print_success "Dependencies installed"
}

# Setup directories
setup_directories() {
    print_status "Creating required directories..."
    
    cd "$PROJECT_DIR"
    mkdir -p data/chroma
    mkdir -p tts_out
    mkdir -p logs
    
    print_success "Directories created"
}

# Scan shell configs for API keys
scan_shell_configs() {
    print_feature "Provider Auto-Discovery Feature"
    echo ""
    echo "The new provider system can automatically detect API keys from:"
    echo "  - .env file (current session)"
    echo "  - .bashrc, .zshrc, .bash_profile (shell configs)"
    echo ""
    echo "Supported providers: OpenAI, Fireworks AI, DeepSeek, xAI (Grok),"
    echo "                     Anthropic, Ollama, LM Studio, vLLM"
    echo ""
    
    read -p "Would you like to scan your shell config files (.bashrc, .zshrc) for API keys? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        SCAN_SHELL_CONFIGS="true"
        print_status "Will scan shell configs on startup..."
        
        # Check what files exist
        FOUND_CONFIGS=""
        for config in ~/.bashrc ~/.zshrc ~/.bash_profile ~/.profile; do
            if [ -f "$config" ]; then
                FOUND_CONFIGS="$FOUND_CONFIGS $config"
            fi
        done
        
        if [ -n "$FOUND_CONFIGS" ]; then
            print_status "Found shell configs:$FOUND_CONFIGS"
            
            # Check for existing API keys
            FOUND_KEYS=""
            for env_pair in "${PROVIDER_ENVS[@]}"; do
                IFS=':' read -r env_var provider_name <<< "$env_pair"
                if grep -q "export $env_var" ~/.bashrc ~/.zshrc ~/.bash_profile 2>/dev/null; then
                    FOUND_KEYS="$FOUND_KEYS\n   ✓ $provider_name ($env_var)"
                fi
            done
            
            if [ -n "$FOUND_KEYS" ]; then
                print_success "Detected API keys in shell configs:$FOUND_KEYS"
            else
                print_warning "No API keys found in shell configs yet"
                echo "   You can add them later: echo 'export OPENAI_API_KEY=sk-...' >> ~/.bashrc"
            fi
        else
            print_warning "No shell config files found"
        fi
    else
        SCAN_SHELL_CONFIGS="false"
        print_status "Skipping shell config scan (you can enable later in .env)"
    fi
}

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
        else
            print_warning "No .env.example found, creating comprehensive .env"
            cat > .env << 'EOF'
# ChatMode Configuration v3.0
# Multi-Provider AI System with Auto-Discovery

# ============================================================================
# Provider Auto-Discovery Settings
# ============================================================================
# Set to 'true' to scan .bashrc, .zshrc, .bash_profile for API keys on startup
SCAN_SHELL_CONFIGS=false

# ============================================================================
# LLM Provider Configuration
# ============================================================================
# The system automatically detects and syncs models from all configured providers!
# Just set the API keys below and the system will:
# 1. Auto-detect the provider type from the URL
# 2. Fetch available models from the provider
# 3. Keep models in sync automatically

# === OpenAI (GPT-4, GPT-3.5, etc.) ===
# Get your API key from https://platform.openai.com/api-keys
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# === Ollama (Local LLM - FREE!) ===
# Install: https://ollama.com
# The system will auto-sync ALL your installed Ollama models!
OLLAMA_BASE_URL=http://localhost:11434

# === Fireworks AI (DeepSeek, Llama, etc.) ===
# Get your API key from https://fireworks.ai/account/api-keys
FIREWORKS_API_KEY=

# === DeepSeek (DeepSeek-V3, DeepSeek-Coder) ===
# Get your API key from https://platform.deepseek.com/api_keys
DEEPSEEK_API_KEY=

# === xAI (Grok-2, Grok-Beta) ===
# Get your API key from https://console.x.ai
XAI_API_KEY=

# === Anthropic (Claude models) ===
# Get your API key from https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=

# === LM Studio (Local GUI for models) ===
# Download from https://lmstudio.ai
LMSTUDIO_BASE_URL=http://localhost:1234/v1

# === vLLM (Self-hosted model serving) ===
# Deploy your own models with vLLM
VLLM_BASE_URL=http://localhost:8000/v1

# === Custom Providers ===
# Add any OpenAI-compatible provider:
# PROVIDER_<NAME>_URL=https://api.example.com/v1
# PROVIDER_<NAME>_KEY=your-api-key

# ============================================================================
# Embedding Configuration (for semantic memory)
# ============================================================================
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434
EMBEDDING_API_KEY=

# ============================================================================
# Text-to-Speech (TTS) Configuration
# ============================================================================
TTS_ENABLED=false
TTS_BASE_URL=https://api.openai.com/v1
TTS_API_KEY=
TTS_MODEL=tts-1
TTS_VOICE=alloy
TTS_OUTPUT_DIR=./tts_out

# ============================================================================
# Storage Configuration
# ============================================================================
CHROMA_DIR=./data/chroma
DATABASE_URL=sqlite:///./data/chatmode.db

# ============================================================================
# Conversation Settings
# ============================================================================
MAX_CONTEXT_TOKENS=32000
MAX_OUTPUT_TOKENS=512
MEMORY_TOP_K=5
HISTORY_MAX_MESSAGES=20
TEMPERATURE=0.9
SLEEP_SECONDS=2

# ============================================================================
# Admin & Security Settings
# ============================================================================
ADMIN_USE_LLM=true
SECRET_KEY=change-this-in-production
ALLOWED_ORIGINS=*
VERBOSE=false
EOF
            print_success "Created comprehensive .env file"
        fi
        
        # Update SCAN_SHELL_CONFIGS based on user choice
        if [ "$SCAN_SHELL_CONFIGS" = "true" ]; then
            sed -i 's/SCAN_SHELL_CONFIGS=false/SCAN_SHELL_CONFIGS=true/' .env
            print_success "Enabled shell config scanning in .env"
        fi
        
        print_warning "Please edit .env with your API keys before starting"
    else
        print_warning ".env file already exists, skipping"
        # Still ask about shell config scanning for existing installs
        if [ -z "$SCAN_SHELL_CONFIGS" ]; then
            scan_shell_configs
            if [ "$SCAN_SHELL_CONFIGS" = "true" ]; then
                # Update existing .env
                if grep -q "SCAN_SHELL_CONFIGS" .env; then
                    sed -i 's/SCAN_SHELL_CONFIGS=.*/SCAN_SHELL_CONFIGS=true/' .env
                else
                    echo "" >> .env
                    echo "# Scan shell configs for API keys" >> .env
                    echo "SCAN_SHELL_CONFIGS=true" >> .env
                fi
                print_success "Updated .env to enable shell config scanning"
            fi
        fi
    fi
}

# Initialize database
init_database() {
    print_status "Initializing database..."
    
    cd "$PROJECT_DIR"
    
    # Activate environment
    source $(conda info --base)/etc/profile.d/conda.sh
    conda activate $CONDA_ENV_NAME
    
    # Run bootstrap script
    python bootstrap_admin.py
    
    print_success "Database initialized"
}

# Verify agent_config.json
verify_agent_config() {
    print_status "Verifying agent configuration..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -f "agent_config.json" ]; then
        print_warning "agent_config.json not found, creating default..."
        cat > agent_config.json << 'EOF'
{
  "agents": [
    {
      "name": "lawyer",
      "file": "profiles/lawyer.json"
    },
    {
      "name": "crook",
      "file": "profiles/crook.json"
    }
  ]
}
EOF
        print_success "Created default agent_config.json"
    else
        print_success "agent_config.json found"
    fi
}

# Create launcher script
create_launcher() {
    print_status "Creating launcher script..."
    
    cat > "$PROJECT_DIR/start.sh" << EOF
#!/bin/bash
# ChatMode Launcher Script v3.0
# Auto-generated by autoinstall.sh
# Features: Multi-provider support, auto model discovery

cd "$PROJECT_DIR"
source \$(conda info --base)/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        ChatMode Server v3.0 - Multi-Provider AI System        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Starting server on http://localhost:$DEFAULT_PORT"
echo "🔑 Default login: admin / admin"
echo ""
echo "📚 Provider System:"
echo "   • Auto-discovers models from configured providers"
echo "   • Supports: OpenAI, Fireworks, DeepSeek, xAI, Ollama, etc."
echo "   • API docs: http://localhost:$DEFAULT_PORT/docs"
echo ""
echo "⚙️  To add providers:"
echo "   1. Edit .env file with your API keys"
echo "   2. Or add to ~/.bashrc: export OPENAI_API_KEY=sk-..."
echo "   3. Restart the server"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Check if port is already in use
if lsof -i :$DEFAULT_PORT > /dev/null 2>&1; then
    echo "⚠️  WARNING: Port $DEFAULT_PORT is already in use!"
    echo "Trying alternative port 8003..."
    PORT=8003
else
    PORT=$DEFAULT_PORT
fi

# Start server
python -m uvicorn web_admin:app --host 0.0.0.0 --port \$PORT --reload
EOF

    chmod +x "$PROJECT_DIR/start.sh"
    print_success "Created start.sh launcher"
}

# Create provider helper script
create_provider_helper() {
    print_status "Creating provider helper script..."
    
    cat > "$PROJECT_DIR/add_provider.sh" << 'EOF'
#!/bin/bash
# Helper script to add a new provider
# Usage: ./add_provider.sh <name> <url> [api_key]

if [ $# -lt 2 ]; then
    echo "Usage: ./add_provider.sh <name> <url> [api_key]"
    echo ""
    echo "Examples:"
    echo "  ./add_provider.sh openai https://api.openai.com/v1 sk-..."
    echo "  ./add_provider.sh ollama http://localhost:11434/v1"
    echo "  ./add_provider.sh fireworks https://api.fireworks.ai/inference/v1 fw-..."
    exit 1
fi

PROVIDER_NAME=$1
PROVIDER_URL=$2
PROVIDER_KEY=${3:-}

cd "$(dirname "$0")"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate chatmode

python << PYTHON
import asyncio
import sys
sys.path.insert(0, '.')

from chatmode.database import SessionLocal
from chatmode.services.provider_init import create_provider_from_config, test_provider_connection

async def main():
    db = SessionLocal()
    try:
        # Test connection first
        print(f"🔍 Testing connection to {$PROVIDER_URL}...")
        result = await test_provider_connection("{$PROVIDER_URL}", "{$PROVIDER_KEY}" or None)
        
        if result["success"]:
            print(f"✅ Connection successful! Found {result['models_found']} models")
            
            # Create provider
            provider = create_provider_from_config(
                db=db,
                name="{$PROVIDER_NAME}",
                base_url="{$PROVIDER_URL}",
                api_key="{$PROVIDER_KEY}" or None,
                auto_sync=True
            )
            
            print(f"✅ Provider '{$PROVIDER_NAME}' added successfully!")
            print(f"   ID: {provider.id}")
            print(f"   Type: {provider.provider_type}")
            print(f"   Models will be synced automatically on next startup")
        else:
            print(f"❌ Connection failed: {result['error']}")
            print("   Provider added but may not work correctly")
    finally:
        db.close()

asyncio.run(main())
PYTHON
EOF

    chmod +x "$PROJECT_DIR/add_provider.sh"
    print_success "Created add_provider.sh helper"
}

# Update documentation
update_docs() {
    print_status "Updating documentation..."
    
    # Update README with correct credentials
    if [ -f "$PROJECT_DIR/README.md" ]; then
        sed -i 's/admin123/admin/g' "$PROJECT_DIR/README.md" 2>/dev/null || true
        print_success "Updated README.md"
    fi
}

# Show provider setup instructions
show_provider_setup() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║        Provider Setup Guide                                    ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "The new provider system supports automatic model discovery!"
    echo ""
    echo "Quick Setup Options:"
    echo ""
    echo "1️⃣  .env file (recommended for production):"
    echo "   Edit .env and add your API keys:"
    echo "   OPENAI_API_KEY=sk-your-key-here"
    echo "   FIREWORKS_API_KEY=fw-your-key-here"
    echo ""
    echo "2️⃣  Shell config (.bashrc/.zshrc):"
    echo "   Add to ~/.bashrc or ~/.zshrc:"
    echo "   export OPENAI_API_KEY=sk-your-key-here"
    echo "   export FIREWORKS_API_KEY=fw-your-key-here"
    echo ""
    echo "   Then enable scanning in .env:"
    echo "   SCAN_SHELL_CONFIGS=true"
    echo ""
    echo "3️⃣  Via API (after server starts):"
    echo "   POST http://localhost:8002/providers"
    echo "   {\"name\": \"my-openai\", \"base_url\": \"...\", \"api_key\": \"...\"}"
    echo ""
    echo "Supported Providers:"
    echo "   • OpenAI (GPT-4, GPT-3.5)"
    echo "   • Fireworks AI (DeepSeek, Llama)"
    echo "   • DeepSeek (DeepSeek-V3)"
    echo "   • xAI/Grok (Grok-2)"
    echo "   • Anthropic (Claude)"
    echo "   • Ollama (Local - FREE!)"
    echo "   • LM Studio (Local GUI)"
    echo "   • vLLM (Self-hosted)"
    echo "   • Any OpenAI-compatible API"
    echo ""
}

# Main installation function
main() {
    echo -e "${YELLOW}Starting ChatMode v3.0 installation...${NC}"
    echo ""
    
    # Run all setup steps
    check_conda
    setup_conda_env
    install_deps
    setup_directories
    scan_shell_configs  # Ask about shell config scanning
    setup_env
    init_database
    verify_agent_config
    create_launcher
    create_provider_helper
    update_docs
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Installation Complete! ✨                               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    show_provider_setup
    
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  1. Edit .env file with your API keys: nano .env"
    if [ "$SCAN_SHELL_CONFIGS" = "true" ]; then
        echo "     ℹ️  Shell config scanning is ENABLED - keys from .bashrc/.zshrc will be detected"
    fi
    echo "  2. Start the server: ./start.sh"
    echo "  3. Open browser: http://localhost:$DEFAULT_PORT"
    echo "  4. Login with: admin / admin"
    echo ""
    echo -e "${BLUE}Provider Management:${NC}"
    echo "  • View providers: GET http://localhost:$DEFAULT_PORT/providers"
    echo "  • Sync models: POST http://localhost:$DEFAULT_PORT/providers/sync-all"
    echo "  • Add provider: ./add_provider.sh <name> <url> [key]"
    echo ""
    echo -e "${BLUE}Default Agents:${NC}"
    cat "$PROJECT_DIR/agent_config.json" | grep '"name"' | sed 's/.*"name": "\([^"]*\)".*/  • \1/'
    echo ""
    echo -e "${YELLOW}Note: Make sure Ollama is running if using local models${NC}"
    echo ""
    
    # Ask if user wants to start now
    read -p "Would you like to start ChatMode now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        "$PROJECT_DIR/start.sh"
    else
        echo ""
        echo "You can start ChatMode anytime by running: ./start.sh"
        echo ""
        echo "To add a provider later, use: ./add_provider.sh <name> <url> [api_key]"
    fi
}

# Run main function
main
