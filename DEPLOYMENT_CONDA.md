# ChatMode - Quick Deployment Guide (Conda)

## ✅ Installation Complete!

The ChatMode project has been successfully installed and deployed using conda.

## 🚀 Server Status

- **Server URL**: http://localhost:8002
- **Status**: Running ✅
- **Environment**: chatmode (conda)
- **Python Version**: 3.11.14

## 🔑 Login Credentials

```
Username: admin
Password: admin
```

**✅ VERIFIED**: Login tested and working!

**⚠️ IMPORTANT**: Change the default password after first login!

To test login from command line:
```bash
./test_login.sh
```

## 📋 Quick Commands

### Start Server
```bash
cd ~/ChatMode
./start_conda.sh
```

### Stop Server
```bash
cd ~/ChatMode
./stop.sh
```

### View Logs
```bash
tail -f ~/ChatMode/chatmode.log
```

### Test Login
```bash
cd ~/ChatMode
./test_login.sh
```

### Restart Server
```bash
cd ~/ChatMode
./stop.sh && ./start_conda.sh
```

### Manual Start (with conda)
```bash
cd ~/ChatMode
source ~/miniconda/bin/activate chatmode
python -m uvicorn chatmode.main:app --host 0.0.0.0 --port 8002 --reload
```

## 📁 Project Structure

```
ChatMode/
├── chatmode/           # Main application package
│   ├── main.py        # FastAPI application
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic
│   └── ...
├── data/              # Database & ChromaDB storage
├── profiles/          # Agent personality profiles
├── frontend/          # Web interface
├── .env               # Configuration file
├── start_conda.sh     # Start script
├── stop.sh            # Stop script
└── chatmode.log       # Application logs
```

## 🔧 Configuration

Edit the `.env` file to configure:
- LLM providers (Ollama, OpenAI, DeepSeek, etc.)
- API keys
- Embedding models
- TTS settings

## 🌐 Web Interface

Open your browser and navigate to:
- **Main Interface**: http://localhost:8002
- **Agent Manager**: http://localhost:8002 (Login required)
- **API Docs**: http://localhost:8002/docs

## 🐛 Troubleshooting

### Server won't start
```bash
# Check logs
tail -n 100 ~/ChatMode/chatmode.log

# Kill any stuck processes
pkill -9 -f "uvicorn chatmode.main"

# Try starting again
./start_conda.sh
```

### Port 8002 already in use
```bash
# Find what's using the port
lsof -i :8002

# Or change port in start_conda.sh
# Edit line: --port 8002 to --port XXXX
```

### Conda environment issues
```bash
# Recreate environment
conda env remove -n chatmode
conda env create -f environment.yml
```

## 📚 Next Steps

1. **Login** to http://localhost:8002 with admin/admin
2. **Create agents** via the Agent Manager tab
3. **Start conversations** between your AI agents
4. **Configure providers** in the .env file
5. **Review documentation** in the `docs/` folder

## 🔗 Additional Resources

- Full README: `~/ChatMode/README.md`
- Architecture docs: `~/ChatMode/docs/ARCHITECTURE.md`
- Setup guide: `~/ChatMode/docs/SETUP.md`
- Troubleshooting: `~/ChatMode/docs/TROUBLESHOOTING.md`

---

**Server is ready! Happy chatting! 🎉**
