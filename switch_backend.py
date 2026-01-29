#!/usr/bin/env python3
"""
ChatMode Switcher - Toggle between legacy and CrewAI backends.

Usage:
    python switch_backend.py [crewai|legacy]
    
This script manages symbolic links or imports to switch between
the legacy custom agent system and the new CrewAI-based backend.
"""

import os
import sys
import shutil

# File mappings: target -> (crewai_source, legacy_source)
FILE_MAPPINGS = {
    "main_active.py": ("main_crewai.py", "main.py"),
    "session_active.py": ("session_crewai.py", "session.py"),
    "web_admin_active.py": ("web_admin_crewai.py", "web_admin.py"),
}


def switch_to_crewai():
    """Switch to CrewAI backend."""
    print("Switching to CrewAI backend...")
    
    for target, (crewai_src, _) in FILE_MAPPINGS.items():
        if os.path.exists(crewai_src):
            # Create symlink or copy
            if os.path.exists(target):
                os.remove(target)
            os.symlink(crewai_src, target)
            print(f"  ✓ {target} -> {crewai_src}")
        else:
            print(f"  ✗ {crewai_src} not found!")
    
    print("\n✓ Switched to CrewAI backend")
    print("\nTo start:")
    print("  CLI:  python main_crewai.py")
    print("  Web:  uvicorn web_admin_crewai:app --reload")


def switch_to_legacy():
    """Switch to legacy backend."""
    print("Switching to legacy backend...")
    
    for target, (_, legacy_src) in FILE_MAPPINGS.items():
        if os.path.exists(legacy_src):
            if os.path.exists(target):
                os.remove(target)
            os.symlink(legacy_src, target)
            print(f"  ✓ {target} -> {legacy_src}")
        else:
            print(f"  ✗ {legacy_src} not found!")
    
    print("\n✓ Switched to legacy backend")
    print("\nTo start:")
    print("  CLI:  python main.py")
    print("  Web:  uvicorn web_admin:app --reload")


def show_status():
    """Show current backend status."""
    print("Current backend status:")
    print()
    
    crewai_files = ["main_crewai.py", "session_crewai.py", "web_admin_crewai.py"]
    legacy_files = ["main.py", "session.py", "web_admin.py"]
    
    crewai_exists = all(os.path.exists(f) for f in crewai_files)
    legacy_exists = all(os.path.exists(f) for f in legacy_files)
    
    print(f"  CrewAI backend available: {'✓' if crewai_exists else '✗'}")
    print(f"  Legacy backend available: {'✓' if legacy_exists else '✗'}")
    print()
    
    if crewai_exists:
        print("  To use CrewAI:")
        print("    python main_crewai.py")
        print("    uvicorn web_admin_crewai:app --reload")
    
    if legacy_exists:
        print("  To use Legacy:")
        print("    python main.py")
        print("    uvicorn web_admin:app --reload")


def main():
    if len(sys.argv) < 2:
        show_status()
        print("\nUsage: python switch_backend.py [crewai|legacy|status]")
        return
    
    command = sys.argv[1].lower()
    
    if command == "crewai":
        switch_to_crewai()
    elif command == "legacy":
        switch_to_legacy()
    elif command == "status":
        show_status()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python switch_backend.py [crewai|legacy|status]")


if __name__ == "__main__":
    main()
