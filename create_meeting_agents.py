#!/usr/bin/env python3
"""
Create meeting agents for testing ChatMode with DeepSeek.
"""
import sys
from sqlalchemy.orm import Session
from chatmode.database import get_db, init_db
from chatmode import crud
from chatmode.schemas import AgentCreate

# Initialize database
init_db()

# Create agents for a meeting scenario
agents_to_create = [
    {
        "name": "meeting-ceo",
        "display_name": "Sarah Chen - CEO",
        "system_prompt": "You are Sarah Chen, the CEO of a growing tech startup. You're strategic, visionary, and focus on company growth and market positioning. You ask tough questions about ROI and scalability. Keep responses concise and business-focused.",
        "model": "deepseek-chat",
        "provider": "openai",
        "api_url": "https://api.deepseek.com/v1",
        "temperature": 0.8,
        "max_tokens": 300,
        "enabled": True
    },
    {
        "name": "meeting-cto",
        "display_name": "Marcus Williams - CTO",
        "system_prompt": "You are Marcus Williams, the CTO with deep technical expertise. You care about architecture, scalability, security, and technical feasibility. You're pragmatic and detail-oriented. Keep responses technical but accessible.",
        "model": "deepseek-chat",
        "provider": "openai",
        "api_url": "https://api.deepseek.com/v1",
        "temperature": 0.7,
        "max_tokens": 300,
        "enabled": True
    },
    {
        "name": "meeting-product",
        "display_name": "Jessica Park - Product Manager",
        "system_prompt": "You are Jessica Park, a product manager focused on user experience and market fit. You advocate for customer needs, usability, and iterative development. You balance business goals with user satisfaction.",
        "model": "deepseek-chat",
        "provider": "openai",
        "api_url": "https://api.deepseek.com/v1",
        "temperature": 0.9,
        "max_tokens": 300,
        "enabled": True
    },
    {
        "name": "meeting-marketing",
        "display_name": "David Rodriguez - Marketing Director",
        "system_prompt": "You are David Rodriguez, the Marketing Director. You think about brand positioning, customer acquisition, and competitive differentiation. You're creative and data-driven, always considering market trends and customer perception.",
        "model": "deepseek-chat",
        "provider": "openai",
        "api_url": "https://api.deepseek.com/v1",
        "temperature": 0.85,
        "max_tokens": 300,
        "enabled": True
    }
]

def main():
    # Get database session
    db: Session = next(get_db())
    
    try:
        for agent_data in agents_to_create:
            # Check if agent already exists
            existing = crud.get_agent_by_name(db, agent_data["name"])
            if existing:
                print(f"✓ Agent '{agent_data['name']}' already exists, skipping...")
                continue
            
            # Create agent
            agent_create = AgentCreate(**agent_data)
            agent = crud.create_agent(db, agent_create)
            print(f"✓ Created agent: {agent.name} ({agent.display_name})")
        
        print("\n✓ All agents created successfully!")
        print("\nYou can now start a meeting conversation with:")
        print("  Topic: 'Planning our Q2 product roadmap and marketing strategy'")
        
    except Exception as e:
        print(f"Error creating agents: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
