#!/bin/sh
# HDL Arena — Launch Script for Termux / Linux

echo "⚡ Starting HDL Arena Environment..."

# 1. Kill any existing instances on port 8000 and 5173
pkill -f "main.py" 2>/dev/null
pkill -f "vite" 2>/dev/null

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 2. Acquire wake lock in Termux if tool is available so Android does not kill server in background
if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
    echo "✓ Termux wake-lock acquired."
fi

# 3. Detect Python executable (checking backend virtual environment first)
if [ -f "$PROJECT_DIR/backend/.venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_DIR/backend/.venv/bin/python3"
elif [ -f "$PROJECT_DIR/backend/.venv/bin/python" ]; then
    PYTHON_BIN="$PROJECT_DIR/backend/.venv/bin/python"
elif [ -f "$PROJECT_DIR/backend/venv/bin/python3" ]; then
    PYTHON_BIN="$PROJECT_DIR/backend/venv/bin/python3"
else
    PYTHON_BIN="python3"
fi

echo "✓ Using Python: $PYTHON_BIN"
echo "✓ Starting Flask Backend on http://0.0.0.0:8000..."
cd "$PROJECT_DIR/backend" && "$PYTHON_BIN" main.py &
BACKEND_PID=$!

# Wait 1.5 seconds for Flask to bind
sleep 1.5

# 4. Start Vite Frontend on port 5173
echo "✓ Starting Vite Frontend on http://0.0.0.0:5173..."
cd "$PROJECT_DIR/frontend" && npm run dev -- --host &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo "  🚀 HDL Arena is running!"
echo "=========================================================="
echo "  Vite Dev Server (HMR):  http://127.0.0.1:5173"
echo "  Integrated Backend:     http://127.0.0.1:8000"
echo "=========================================================="
echo "  NOTE: In Chrome/browser, always use http://127.0.0.1:5173"
echo "        (Do not use https:// and avoid 'localhost' on Android)"
echo "=========================================================="
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
