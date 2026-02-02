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
if ! command -v conda &> /dev/null; then
    echo -e "${RED}Error: Conda is not installed!${NC}"
    echo ""
    echo "Please install Miniconda or Anaconda first:"
    echo "  - Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    echo "  - Anaconda: https://www.anaconda.com/download"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Conda detected${NC}"
echo ""

# Run the comprehensive autoinstaller
echo "Running comprehensive auto-installer..."
echo ""

./autoinstall.sh
