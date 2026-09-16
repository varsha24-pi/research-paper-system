#!/usr/bin/env bash
# ==============================================================================
# AI-Powered Research Paper Intelligence System - Linux/macOS Launcher
# ==============================================================================

echo "==========================================================================="
echo "   AI-POWERED RESEARCH PAPER INTELLIGENCE SYSTEM"
echo "   Automated Setup & Launch Script (Linux / macOS)"
echo "==========================================================================="

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install Python 3.10+."
    exit 1
fi

# 2. Virtual Environment
if [ ! -d "venv" ]; then
    echo "[*] Creating Python virtual environment (venv)..."
    python3 -m venv venv
fi

echo "[*] Activating virtual environment..."
source venv/bin/activate

# 3. Install requirements
echo "[*] Installing dependencies from requirements.txt..."
pip install -r requirements.txt --quiet

# 4. Setup .env
if [ ! -f ".env" ]; then
    echo "[*] Copying .env.example to .env..."
    cp .env.example .env
    echo "[!] Please configure your MySQL password in .env if required."
fi

# 5. Verify Database
echo "[*] Verifying database connection..."
python tests/test_db_connection.py

# 6. Start Backend Server
echo "==========================================================================="
echo "[SUCCESS] Starting FastAPI Backend at http://127.0.0.1:8000"
echo "API Docs: http://127.0.0.1:8000/docs"
echo "==========================================================================="

uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
