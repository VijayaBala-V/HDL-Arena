#!/usr/bin/env python3
"""
HDL Arena — Python Production Server Launcher (v2.2.0)
Can be executed with:
    python3 start_production.py
or:
    python3 backend/main.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = PROJECT_DIR / "backend"
FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"

# Ensure all launcher scripts have executable permissions (+x)
for script_name in ["start_production.sh", "start.sh"]:
    p = PROJECT_DIR / script_name
    if p.exists():
        try:
            current_mode = os.stat(p).st_mode
            os.chmod(p, current_mode | 0o755)
        except Exception as e:
            pass

# Add backend directory to sys.path so we can import modules
sys.path.insert(0, str(BACKEND_DIR))

# Termux wake-lock acquisition
try:
    subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✓ Termux wake-lock acquired.")
except Exception:
    pass

print("==========================================================")
print("  🚀 HDL Arena — Production Launch (v2.2.0)")
print("==========================================================")

# Verify production frontend build exists
index_html = FRONTEND_DIST / "index.html"
if index_html.exists():
    print(f"✓ Production UI bundle verified ({FRONTEND_DIST})")
else:
    print(f"⚠️ Warning: {index_html} not found; API mode only.")

# Database backup and integrity check
try:
    import database
    ok, info = database.backup_database_with_integrity_check()
    if ok:
        print(f"✓ Database integrity check passed & verified backup stored.")
    else:
        print(f"⚠️ Database backup/integrity warning: {info}")
except Exception as e:
    print(f"⚠️ Database check error: {e}")

print("==========================================================")
print("  🎉 HDL ARENA IS PUBLISHED & LIVE!")
print("==========================================================")
print("  Local Browser Access:     http://127.0.0.1:8000")
print("  LAN / Mobile Access:      http://0.0.0.0:8000")
print("  Production Architecture:  Integrated Single-Process")
print("                            (Flask API + Pre-built SPA)")
print("==========================================================")
print("  Press Ctrl+C to stop the server.")
print("==========================================================")

# Change directory to backend and run main.py
os.chdir(BACKEND_DIR)
from main import app
app.run(host="0.0.0.0", port=8000, debug=False)
