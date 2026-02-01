# ChatMode Quick Start Guide

Get up and running with ChatMode Agent Manager in 3 minutes!

## Prerequisites
- Python 3.11+
- ChatMode repository cloned
- Dependencies installed (see README.md)

## Setup (3 Steps)

### Step 1: Initialize Admin User
```bash
python bootstrap.py --username admin --password admin123
```
✓ Creates admin account  
✓ Initializes database

### Step 2: Load Personalities
```bash
python bootstrap_personalities.py
```
✓ Loads 5 diverse agent personalities  
✓ Configures settings automatically

### Step 3: Start Server
```bash
python -m uvicorn chatmode.main:app --host 0.0.0.0 --port 8002 --reload
```
✓ Server runs on port 8002  
✓ Auto-reloads on code changes

## Access the Interface

Open your browser to: **http://localhost:8002**

### The 5 Personalities

**Good Characters:**
1. 🌞 **Sunny McBright** - Optimistic cheerleader
2. ⛪ **Eleanor Price** - Moral crusader

**Bad Characters:**
3. 😠 **Dante King** - Street operator with attitude
4. 💋 **Lena Marquez** - Drama-loving gossip columnist

**Neutral:**
5. ⚖️ **Vivian Cross** - Ruthless trial attorney

## Quick Test

Try it out:
```bash
# Run automated tests
./test_agent_manager.sh

# Should show:
# ✓ Login successful
# ✓ Found 5 agents
# ✓ Web interface accessible
```

## Using the Interface

### Login to Agent Manager
1. Click **Agent Manager** tab
2. Enter credentials: `admin` / `admin123`
3. See all 5 personalities listed

### Start a Conversation
1. Go to **Session Control** tab
2. Enter topic: `"The future of AI ethics"`
3. Click **Start**
4. Switch to **Live Monitor** tab to watch debate

### Edit Personalities
1. In Agent Manager, click **Edit** on any agent
2. Modify system prompt, temperature, or model
3. Click **Save Agent**
4. Changes apply immediately

## Next Steps

- Read `AGENT_MANAGER_SETUP.md` for detailed configuration
- Check `AGENT_MANAGER_FIX.md` for technical details
- Explore API docs at http://localhost:8002/docs
- Create your own custom agents!

## Troubleshooting

**Can't login?**
```bash
# Reset database
python bootstrap.py
python bootstrap_personalities.py
```

**Server won't start?**
```bash
# Check if port 8002 is in use
lsof -i :8002
# Kill existing process
pkill -f "uvicorn chatmode.main"
```

**Agents not showing?**
- Make sure you ran `bootstrap_personalities.py`
- Check database exists: `ls data/chatmode.db`
- Restart server

## Success Criteria

You should see:
- ✅ 5 agents in Agent Manager
- ✅ Different personalities with unique prompts
- ✅ Temperature values: 0.6 to 0.9
- ✅ All agents enabled
- ✅ Can start/stop sessions
- ✅ Messages appear in Live Monitor

**Enjoy your multi-agent conversations!** 🎉
