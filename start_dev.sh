#!/data/data/com.termux/files/usr/bin/bash

cd "$HOME/hdl-judge-mvp/backend" || exit 1
source .venv/bin/activate
python main.py &
BACKEND_PID=$!

cd "$HOME/hdl-judge-mvp/frontend" || exit 1
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

trap 'kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null; exit' INT TERM
wait
