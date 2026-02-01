# Agent Manager Setup Guide

This guide will help you set up ChatMode with preloaded agent personalities.

## Quick Start

### 1. Initialize the Database

First, create the admin user and initialize the database:

```bash
python bootstrap.py --username admin --password admin123
```

This creates:
- SQLite database at `./data/chatmode.db`
- Admin user with credentials: `admin` / `admin123`

### 2. Load Personality Profiles

Load 5 diverse agent personalities into the database:

```bash
python bootstrap_personalities.py
```

This creates 5 distinct personalities:

#### Good Personalities
- **Sunny McBright** - Eternally optimistic and cheerful, spreads joy everywhere
- **Eleanor Price** - Zealous moral crusader with unwavering convictions

#### Bad Personalities
- **Dante King** - Volatile street operator, confrontational and aggressive
- **Lena Marquez** - Manipulative gossip columnist who thrives on chaos

#### Neutral Personalities
- **Vivian Cross** - Ruthless trial attorney, theatrical and demanding

### 3. Start the Server

```bash
# Using uvicorn directly
python -m uvicorn chatmode.main:app --host 0.0.0.0 --port 8002 --reload

# OR using the launch script
./launch.sh
```

### 4. Access the Web Interface

Open your browser to: **http://localhost:8002**

## Using the Agent Manager

### Login

1. Click on the **Agent Manager** tab
2. Login with credentials:
   - Username: `admin`
   - Password: `admin123`

### Managing Agents

Once logged in, you can:

- **View All Agents** - See the 5 preloaded personalities
- **Edit Agents** - Modify system prompts, temperature, model settings
- **Create New Agents** - Add additional personalities
- **Delete Agents** - Remove agents you don't need
- **Configure Voice Settings** - Enable TTS/STT for each agent
- **Set Permissions** - Configure content filters and rate limits
- **View JSON** - Inspect the full agent configuration

### Starting a Conversation

1. Go to **Session Control** tab
2. Enter a topic (e.g., "The future of AI")
3. Click **Start**
4. Watch the agents debate in the **Live Monitor** tab

## Agent Personalities Overview

### Sunny McBright (Good)
- **Personality**: Eternally optimistic, cheerful, uplifting
- **Temperature**: 0.8 (creative and varied)
- **Style**: Short, conversational, positive
- **Example**: "Oh that's wonderful! How delightful!"

### Dante King (Bad)
- **Personality**: Volatile, confrontational, street-smart
- **Temperature**: 0.9 (highly unpredictable)
- **Style**: Sharp, aggressive, uses slang
- **Example**: "What you tryin' to pull here? Don't play me!"

### Vivian Cross (Neutral)
- **Personality**: Ruthless attorney, theatrical, demanding
- **Temperature**: 0.7 (balanced and strategic)
- **Style**: Legal jargon, cross-examination style
- **Example**: "Objection, Client! That's pure speculation!"

### Eleanor Price (Good)
- **Personality**: Moral crusader, stern, persuasive
- **Temperature**: 0.6 (consistent and principled)
- **Style**: Quotes scripture, condemns corruption
- **Example**: "Repent! Your hypocrisy shall not stand!"

### Lena Marquez (Bad)
- **Personality**: Gossip columnist, charming, manipulative
- **Temperature**: 0.85 (creative and dramatic)
- **Style**: Uses terms of endearment, stirs drama
- **Example**: "Oh honey, you won't believe what I heard..."

## Advanced Configuration

### Customizing Agents

Edit any agent through the web interface:

1. Click **Edit** on any agent
2. Modify:
   - **System Prompt** - Changes personality and behavior
   - **Temperature** - Higher = more creative, Lower = more consistent
   - **Max Tokens** - Response length limit
   - **Model** - Change AI model (gpt-4o, gpt-4o-mini, etc.)

### Adding More Personalities

You can create additional agents by:

1. Using the **Create Agent** button in Agent Manager
2. Running `demo_setup.py` for pre-configured demo agents
3. Editing `bootstrap_personalities.py` to add your own

### Content Filtering

Enable per-agent content filtering:

1. Edit an agent
2. Scroll to **Content Filter Settings**
3. Enable filter and configure:
   - Blocked words/phrases
   - Filter action (block, censor, warn)
   - Custom filter message

## Troubleshooting

### Database Issues

If you see schema errors, reset the database:

```bash
# Backup old database
mv data/chatmode.db data/chatmode.db.backup

# Reinitialize
python bootstrap.py
python bootstrap_personalities.py
```

### Agent Not Appearing

Check if agent is enabled:
```bash
TOKEN=$(curl -s -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

curl -H "Authorization: Bearer $TOKEN" http://localhost:8002/api/v1/agents/
```

### Server Won't Start

Check if port 8002 is already in use:
```bash
lsof -i :8002
# Kill existing process if needed
pkill -f "uvicorn chatmode.main"
```

## File Structure

```
ChatMode/
├── bootstrap.py                    # Creates admin user
├── bootstrap_personalities.py      # Loads 5 personalities
├── data/
│   └── chatmode.db                # SQLite database
├── profiles/                       # Legacy JSON profiles
│   ├── sunny.json
│   ├── crook.json
│   ├── lawyer.json
│   ├── church_woman.json
│   └── prostitute.json
├── frontend/
│   └── unified.html               # Web interface
└── agent_config.json              # Agent file references
```

## API Access

All agent management can be done via REST API:

```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r .access_token)

# List agents
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8002/api/v1/agents/

# Get specific agent
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8002/api/v1/agents/{agent_id}

# Create agent
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"new_agent","model":"gpt-4o-mini",...}' \
  http://localhost:8002/api/v1/agents/

# Update agent
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"display_name":"Updated Name",...}' \
  http://localhost:8002/api/v1/agents/{agent_id}

# Delete agent
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  http://localhost:8002/api/v1/agents/{agent_id}
```

API documentation: http://localhost:8002/docs

## Security Notes

⚠️ **Change Default Credentials in Production**

The default admin credentials (`admin`/`admin123`) are for development only. 
In production, create secure credentials:

```bash
python bootstrap.py --username your_admin --password your_secure_password
```

## Next Steps

- Explore the **Live Monitor** tab to watch agents debate
- Try different topics to see how personalities interact
- Create your own custom agents with unique traits
- Enable TTS to hear agents speak their responses
- Configure content filters for specific use cases

For more information, see:
- Main README: `README.md`
- API Documentation: http://localhost:8002/docs
- Demo Setup: `demo_setup.py`
