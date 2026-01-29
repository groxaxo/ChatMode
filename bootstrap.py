#!/usr/bin/env python3
"""
Bootstrap Script for ChatMode

Creates the initial admin user and sets up the database.
Run this once before starting the server for the first time.

Usage:
    python bootstrap.py [--username admin] [--password admin123] [--email admin@example.com]
"""

import argparse
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, get_db, SessionLocal
from models import User
from auth import hash_password
import uuid


def create_admin_user(username: str, password: str, email: str = None):
    """Create the initial admin user."""
    print(f"Initializing database...")
    init_db()
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"User '{username}' already exists.")
            if existing.role != "admin":
                existing.role = "admin"
                db.commit()
                print(f"Updated '{username}' to admin role.")
            return existing
        
        # Create admin user
        admin = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            enabled=True
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print(f"Created admin user: {username}")
        print(f"  ID: {admin.id}")
        print(f"  Email: {email or '(not set)'}")
        print(f"  Role: admin")
        print()
        print("You can now login with these credentials.")
        
        return admin
        
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Bootstrap ChatMode with an admin user")
    parser.add_argument("--username", default="admin", help="Admin username")
    parser.add_argument("--password", default="admin123", help="Admin password")
    parser.add_argument("--email", default=None, help="Admin email (optional)")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("ChatMode Bootstrap")
    print("=" * 50)
    print()
    
    create_admin_user(args.username, args.password, args.email)
    
    print()
    print("Bootstrap complete!")
    print()
    print("Next steps:")
    print("  1. Start the server: uvicorn web_admin:app --reload")
    print("  2. Open: http://localhost:8000/frontend/agent_manager.html")
    print("  3. Login with your admin credentials")
    print("  4. (Optional) Run demo_setup.py to create demo agents")


if __name__ == "__main__":
    main()
