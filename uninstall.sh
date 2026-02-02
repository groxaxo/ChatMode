#!/bin/bash
# ChatMode Uninstallation Script
# Removes the conda environment and cleans up generated files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CONDA_ENV_NAME="chatmode"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           ChatMode Uninstaller                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Warning
echo -e "${YELLOW}WARNING: This will:${NC}"
echo "  - Remove the conda environment 'chatmode'"
echo "  - Delete generated data (database, vector store, audio files)"
echo "  - Remove log files"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Remove conda environment
if conda env list | grep -q "^${CONDA_ENV_NAME} "; then
    echo -e "${BLUE}[1/4]${NC} Removing conda environment: $CONDA_ENV_NAME"
    conda env remove -n $CONDA_ENV_NAME -y
    echo -e "${GREEN}✓ Environment removed${NC}"
else
    echo -e "${YELLOW}[1/4]${NC} Environment '$CONDA_ENV_NAME' not found, skipping"
fi

# Remove data directory
if [ -d "data" ]; then
    echo -e "${BLUE}[2/4]${NC} Removing data directory..."
    rm -rf data/
    echo -e "${GREEN}✓ Data directory removed${NC}"
else
    echo -e "${YELLOW}[2/4]${NC} Data directory not found, skipping"
fi

# Remove TTS output directory
if [ -d "tts_out" ]; then
    echo -e "${BLUE}[3/4]${NC} Removing TTS output directory..."
    rm -rf tts_out/
    echo -e "${GREEN}✓ TTS output directory removed${NC}"
else
    echo -e "${YELLOW}[3/4]${NC} TTS output directory not found, skipping"
fi

# Remove log files
echo -e "${BLUE}[4/4]${NC} Removing log files..."
rm -f *.log backend_restart.log server.out uvicorn.log
echo -e "${GREEN}✓ Log files removed${NC}"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║    Uninstallation Complete!                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "The following were preserved:"
echo "  - Source code (chatmode/, profiles/, templates/, frontend/)"
echo "  - Configuration files (requirements.txt, environment.yml, .env)"
echo "  - Documentation (docs/, README.md)"
echo ""
echo "To reinstall, run: ./install.sh"
