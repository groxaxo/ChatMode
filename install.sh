#!/bin/bash
# ChatMode Installation Script
# Simplified installer that checks for conda and delegates to autoinstall.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              ChatMode Installer                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if conda is installed
find_conda() {
    if command -v conda &> /dev/null; then
        echo "conda"
        return 0
    fi

    local paths=(
        "$HOME/miniconda3/bin/conda"
        "$HOME/anaconda3/bin/conda"
        "$HOME/miniconda/bin/conda"
        "$HOME/anaconda/bin/conda"
        "/opt/conda/bin/conda"
        "/opt/anaconda3/bin/conda"
        "/opt/miniconda3/bin/conda"
        "/usr/local/anaconda3/bin/conda"
        "/usr/local/miniconda3/bin/conda"
    )

    for path in "${paths[@]}"; do
        if [ -x "$path" ]; then
            echo "$path"
            return 0
        fi
    done

    return 1
}

CONDA_EXE=$(find_conda)
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Conda is not installed!${NC}"
    echo ""
    echo "Please install Miniconda or Anaconda first:"
    echo "  - Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    echo "  - Anaconda: https://www.anaconda.com/download"
    echo ""
    exit 1
fi

if [[ "$CONDA_EXE" != "conda" ]]; then
    export PATH="$(dirname "$CONDA_EXE"):$PATH"
    echo -e "${GREEN}✓ Conda detected at $CONDA_EXE${NC}"
else
    echo -e "${GREEN}✓ Conda detected${NC}"
fi
echo ""

# Check if autoinstall.sh exists and is executable
if [ ! -f "./autoinstall.sh" ]; then
    echo -e "${RED}Error: autoinstall.sh not found!${NC}"
    echo "Please ensure you are running this script from the ChatMode directory."
    exit 1
fi

# Make sure it's executable
chmod +x ./autoinstall.sh

# Run the comprehensive autoinstaller
echo "Running comprehensive auto-installer..."
echo ""

./autoinstall.sh
