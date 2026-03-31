#!/bin/bash
# Start AutoCut backend with venv
cd /www/wwwroot/autocut-video/backend
source venv/bin/activate
exec uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
