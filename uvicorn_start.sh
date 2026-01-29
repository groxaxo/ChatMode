#!/usr/bin/env bash
set -euo pipefail
cd /home/op/ChatMode
exec conda run -n ChatMode python -m uvicorn web_admin:app --host 0.0.0.0 --port 8001
