#!/bin/bash
# ChatMode Stop Script

echo "🛑 Stopping ChatMode server..."

# Find and kill the process
pkill -f "uvicorn chatmode.main"

# Wait a moment
sleep 2

# Check if server stopped
if pgrep -f "uvicorn chatmode.main" > /dev/null; then
    echo "⚠️  Server still running. Force killing..."
    pkill -9 -f "uvicorn chatmode.main"
    sleep 1
fi

if ! pgrep -f "uvicorn chatmode.main" > /dev/null; then
    echo "✅ ChatMode server stopped successfully"
else
    echo "❌ Failed to stop server"
    exit 1
fi
