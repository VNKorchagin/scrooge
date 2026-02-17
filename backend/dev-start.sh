#!/bin/bash
# Development server with auto-restart on code changes

echo "Starting Scrooge backend development server..."

# Kill existing uvicorn processes
pkill -f "uvicorn app.main:app" 2>/dev/null || true

# Wait a moment
sleep 1

# Activate virtual environment
source venv/bin/activate

# Function to start server
start_server() {
    echo "[$(date '+%H:%M:%S')] Starting uvicorn..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
}

# Start with auto-reload on file changes
start_server
