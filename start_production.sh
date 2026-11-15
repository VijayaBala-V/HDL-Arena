#!/bin/sh
# HDL Arena — Standalone Production Launch Script
# Version: 2.2.0

echo "=========================================================="
echo "  🚀 HDL Arena — Production Launch (v2.2.0)"
echo "=========================================================="

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIST="$PROJECT_DIR/frontend/dist"

# 1. Stop any currently running instances
pkill -f "main.py" 2>/dev/null
sleep 0.5

# 2. Acquire Termux wake-lock to prevent background sleep
if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
    echo "✓ Termux wake-lock acquired."
fi

# 3. Detect Python executable
if [ -f "$BACKEND_DIR/.venv/bin/python3" ]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python3"
elif [ -f "$BACKEND_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$BACKEND_DIR/.venv/bin/python"
elif [ -f "$BACKEND_DIR/venv/bin/python3" ]; then
    PYTHON_BIN="$BACKEND_DIR/venv/bin/python3"
else
    PYTHON_BIN="python3"
fi

echo "✓ Using Python: $PYTHON_BIN"

# 4. Verify production frontend build exists
if [ -f "$FRONTEND_DIST/index.html" ]; then
    echo "✓ Production UI bundle verified ($FRONTEND_DIST)"
else
    echo "⚠️ Warning: $FRONTEND_DIST/index.html not found; fallback API mode active."
fi

# 5. Run pre-launch database backup & integrity check
echo "✓ Verifying database integrity..."
"$PYTHON_BIN" -c "
import sys
sys.path.insert(0, '$BACKEND_DIR')
import database
ok, info = database.backup_database_with_integrity_check()
if ok:
    print('✓ Database integrity check passed & verified backup stored.')
else:
    print('⚠️ Database check warning:', info)
"

# 6. Launch production integrated server on port 8000
echo "✓ Starting Production Server on http://0.0.0.0:8000..."
cd "$BACKEND_DIR" && "$PYTHON_BIN" main.py &
SERVER_PID=$!

sleep 1.5

echo ""
echo "=========================================================="
echo "  🎉 HDL ARENA IS PUBLISHED & LIVE!"
echo "=========================================================="
echo "  Local Browser Access:     http://127.0.0.1:8000"
echo "  LAN / Wi-Fi Access:       http://<device-ip>:8000"
echo "  Production Architecture:  Integrated Single-Process"
echo "                            (Flask API + Pre-built SPA)"
echo "=========================================================="
echo "  Press Ctrl+C to stop the production server."
echo "=========================================================="

trap "kill $SERVER_PID 2>/dev/null; exit" INT TERM
wait $SERVER_PID
