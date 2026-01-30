#!/bin/bash
# ChatMode Auto-Installer Script
# This script automatically installs ChatMode with conda environment,
# initializes the database, and prepares the system for launch.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONDA_ENV_NAME="chatmode"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PORT=8002

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        ChatMode Auto-Installer v2.0                   ║${NC}"
echo -e "${BLUE}║   AI Agent Orchestration System                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
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

# Setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    cd "$PROJECT_DIR"
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
            print_warning "Please edit .env with your API keys and settings"
        else
            print_warning "No .env.example found, creating minimal .env"
            cat > .env << 'EOF'
# ChatMode Configuration
# LLM Provider
OPENAI_API_KEY=ollama
OPENAI_BASE_URL=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434

# Embeddings
EMBEDDING_PROVIDER=ollama
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_BASE_URL=http://localhost:11434

# Storage
CHROMA_DIR=./data/chroma
DATABASE_URL=sqlite:///./data/chatmode.db

# TTS (disabled by default)
TTS_ENABLED=false

# Security
SECRET_KEY=change-this-in-production
ALLOWED_ORIGINS=*

# Conversation Settings
MAX_CONTEXT_TOKENS=32000
MAX_OUTPUT_TOKENS=512
TEMPERATURE=0.9
EOF
            print_success "Created minimal .env file"
        fi
    else
        print_warning ".env file already exists, skipping"
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
# ChatMode Launcher Script
# Auto-generated by autoinstall.sh

cd "$PROJECT_DIR"
source \$(conda info --base)/etc/profile.d/conda.sh
conda activate $CONDA_ENV_NAME

echo "╔════════════════════════════════════════════════════════╗"
echo "║        ChatMode Server Launcher                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "Starting server on http://localhost:$DEFAULT_PORT"
echo "Default login: admin / admin"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Check if port is already in use
if lsof -i :$DEFAULT_PORT > /dev/null 2>&1; then
    echo "WARNING: Port $DEFAULT_PORT is already in use!"
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

# Update documentation
update_docs() {
    print_status "Updating documentation..."
    
    # Update README with correct credentials
    if [ -f "$PROJECT_DIR/README.md" ]; then
        sed -i 's/admin123/admin/g' "$PROJECT_DIR/README.md"
        print_success "Updated README.md with admin/admin credentials"
    fi
    
    # Update SETUP.md
    if [ -f "$PROJECT_DIR/docs/SETUP.md" ]; then
        sed -i 's/admin123/admin/g' "$PROJECT_DIR/docs/SETUP.md"
        print_success "Updated docs/SETUP.md with admin/admin credentials"
    fi
}

# Main installation function
main() {
    echo -e "${YELLOW}Starting ChatMode installation...${NC}"
    echo ""
    
    # Run all setup steps
    check_conda
    setup_conda_env
    install_deps
    setup_directories
    setup_env
    init_database
    verify_agent_config
    create_launcher
    update_docs
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║        Installation Complete!                         ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}Quick Start:${NC}"
    echo "  1. Edit .env file with your API keys: nano .env"
    echo "  2. Start the server: ./start.sh"
    echo "  3. Open browser: http://localhost:$DEFAULT_PORT"
    echo "  4. Login with: admin / admin"
    echo ""
    echo -e "${BLUE}Default Agents:${NC}"
    cat "$PROJECT_DIR/agent_config.json" | grep '"name"' | sed 's/.*"name": "\([^"]*\)".*/  - \1/'
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
    fi
}

# Run main function
main
