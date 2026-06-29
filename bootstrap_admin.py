#!/usr/bin/env python3
"""
Bootstrap script to create initial admin user.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatmode.database import init_db, SessionLocal
from chatmode.auth import create_initial_admin

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    # Password may be passed as second argument; omit to auto-generate a secure one
    password = sys.argv[2] if len(sys.argv) > 2 else None

    print("Initializing database...")
    init_db()

    print("Creating initial admin user...")
    db = SessionLocal()
    try:
        admin = create_initial_admin(db, username=username, password=password)
        if not admin:
            print("Admin user already exists or other users exist — skipping creation")
    finally:
        db.close()
