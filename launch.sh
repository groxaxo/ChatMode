#!/bin/bash
# ChatMode Launcher - Easy access to all interfaces

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_menu() {
    echo "╔════════════════════════════════════════╗"
    echo "║     ChatMode Unified Launcher          ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "Choose an option:"
    echo ""
    echo "  1) 🌐 Start Web Interface (Unified)"
    echo "     Single-page app with all features"
    echo "     → http://localhost:8000"
    echo ""
    echo "  2) 📋 List Agents (CLI)"
    echo ""
    echo "  3) ▶️  Start Session (CLI)"
    echo ""
    echo "  4) 📊 Check Status (CLI)"
    echo ""
    echo "  5) 🛑 Stop Session (CLI)"
    echo ""
    echo "  6) 📖 View Documentation"
    echo ""
    echo "  0) Exit"
    echo ""
    echo -n "Enter choice [0-6]: "
}

while true; do
    show_menu
    read choice
    
    case $choice in
        1)
            echo ""
            echo "Starting Web Interface..."
            echo "Press Ctrl+C to stop"
            echo ""
            conda run -n base python web_admin.py
            ;;
        2)
            echo ""
            conda run -n base python agent_manager.py list-agents
            echo ""
            read -p "Press Enter to continue..."
            ;;
        3)
            echo ""
            echo -n "Enter topic: "
            read topic
            if [ -n "$topic" ]; then
                conda run -n base python agent_manager.py start "$topic"
            else
                echo "Topic cannot be empty"
            fi
            echo ""
            read -p "Press Enter to continue..."
            ;;
        4)
            echo ""
            conda run -n base python agent_manager.py status
            echo ""
            read -p "Press Enter to continue..."
            ;;
        5)
            echo ""
            conda run -n base python agent_manager.py stop
            echo ""
            read -p "Press Enter to continue..."
            ;;
        6)
            echo ""
            if [ -f "UNIFIED_INTERFACE_GUIDE.md" ]; then
                less UNIFIED_INTERFACE_GUIDE.md
            else
                echo "Documentation not found"
            fi
            ;;
        0)
            echo ""
            echo "Goodbye! 👋"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo "Invalid choice. Please try again."
            echo ""
            read -p "Press Enter to continue..."
            ;;
    esac
    
    echo ""
done
