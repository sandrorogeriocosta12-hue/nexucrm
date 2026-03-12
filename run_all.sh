#!/usr/bin/env bash
# helper script to start backend and static server for manual testing

set -e

# ensure we are in project root
cd "$(dirname "$0")"

# activate virtualenv if exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtualenv..."
    # shellcheck disable=SC1091
    source venv/bin/activate
fi

# install deps if necessary
if [ ! -d "venv" ]; then
    echo "Virtualenv not found; creating and installing requirements..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# start backend in background
echo "Starting FastAPI backend on port 8080..."
nohup uvicorn app.api:app --reload --host 0.0.0.0 --port 8080 > backend.log 2>&1 &
BACK_PID=$!

echo "Backend PID: $BACK_PID"

# serve templates folder
TEMPLATES_DIR="vexus_core/templates"
if [ -d "$TEMPLATES_DIR" ]; then
    echo "Serving HTML files from $TEMPLATES_DIR on port 8000..."
    # use nohup to ensure server persists after script exits
    nohup bash -c "cd '$TEMPLATES_DIR' && python3 -m http.server 8000" > static.log 2>&1 &
    HTML_PID=$!
    echo "Static server PID: $HTML_PID"
else
    echo "Templates directory not found: $TEMPLATES_DIR" >&2
fi

echo "
Done. Open http://localhost:8000/dashboard.html in your browser, log in and navigate through the pages."
echo "To stop the servers, run: kill $BACK_PID $HTML_PID"
