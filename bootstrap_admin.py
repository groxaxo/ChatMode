#!/usr/bin/env python3
"""
Bootstrap script to create initial admin user.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from chatmode.database import init_db, SessionLocal
from chatmode.auth import create_initial_admin

if __name__ == "__main__":
    print("Initializing database...")
    init_db()

    print("Creating initial admin user...")
    db = SessionLocal()
    try:
        admin = create_initial_admin(db, username="admin", password="admin")
        if admin:
            print(f"✓ Created admin user: admin / admin")
        else:
            print("✓ Admin user already exists or other users exist")
    finally:
        db.close()

    print("\nLogin credentials:")
    print("  Username: admin")
    print("  Password: admin")
