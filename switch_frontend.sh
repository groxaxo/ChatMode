#!/bin/bash
# Switch between classic and React frontends

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ "$1" = "react" ]; then
    # Enable React frontend
    if grep -q "USE_REACT_FRONTEND" "$ENV_FILE" 2>/dev/null; then
        sed -i 's/USE_REACT_FRONTEND=.*/USE_REACT_FRONTEND=true/' "$ENV_FILE"
    else
        echo "USE_REACT_FRONTEND=true" >> "$ENV_FILE"
    fi
    echo "✅ Switched to React frontend"
    echo "   Access at: http://localhost:8000/"
    echo "   Or directly: http://localhost:8000/react"
    
elif [ "$1" = "classic" ]; then
    # Disable React frontend (use classic)
    if grep -q "USE_REACT_FRONTEND" "$ENV_FILE" 2>/dev/null; then
        sed -i 's/USE_REACT_FRONTEND=.*/USE_REACT_FRONTEND=false/' "$ENV_FILE"
    else
        echo "USE_REACT_FRONTEND=false" >> "$ENV_FILE"
    fi
    echo "✅ Switched to classic frontend"
    echo "   Access at: http://localhost:8000/"
    
elif [ "$1" = "build" ]; then
    # Build React frontend
    echo "🔨 Building React frontend..."
    cd "$SCRIPT_DIR/frontend/react-app"
    npm install
    npm run build
    echo "✅ React frontend built"
    
elif [ "$1" = "dev" ]; then
    # Start React dev server
    echo "🚀 Starting React dev server..."
    cd "$SCRIPT_DIR/frontend/react-app"
    npm run dev
    
else
    echo "ChatMode Frontend Switcher"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  react   - Use React frontend as default"
    echo "  classic - Use classic (unified.html) frontend"
    echo "  build   - Build React frontend"
    echo "  dev     - Start React dev server (with hot reload)"
    echo ""
    echo "After switching, restart the backend server for changes to take effect."
    echo ""
    echo "Access URLs:"
    echo "  Classic: http://localhost:8000/"
    echo "  React:   http://localhost:8000/react"
fi
