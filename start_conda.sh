#!/bin/bash
# ChatMode Start Script (Conda Edition)

# Activate conda environment
source ~/miniconda/bin/activate chatmode

# Navigate to project directory
cd ~/ChatMode

# Check if server is already running
if pgrep -f "uvicorn chatmode.main" > /dev/null; then
    echo "⚠️  ChatMode server is already running!"
    echo "   PID: $(pgrep -f 'uvicorn chatmode.main')"
    echo "   URL: http://localhost:8002"
    exit 1
fi

# Start server
echo "🚀 Starting ChatMode server on port 8002..."
nohup python -m uvicorn chatmode.main:app --host 0.0.0.0 --port 8002 --reload > chatmode.log 2>&1 &

# Wait a moment for startup
sleep 3

# Check if server started successfully
if pgrep -f "uvicorn chatmode.main" > /dev/null; then
    echo "✅ ChatMode server started successfully!"
    echo "   PID: $(pgrep -f 'uvicorn chatmode.main')"
    echo "   URL: http://localhost:8002"
    echo "   Logs: ~/ChatMode/chatmode.log"
    echo ""
    echo "Default login:"
    echo "   Username: admin"
    echo "   Password: admin"
else
    echo "❌ Server failed to start. Check logs:"
    echo "   tail -f ~/ChatMode/chatmode.log"
    exit 1
fi
