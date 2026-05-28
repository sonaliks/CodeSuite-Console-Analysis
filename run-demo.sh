#!/usr/bin/env bash
#
# run-demo.sh — Start all CodeSuite Diagnostics Demo services with a single command.
#
# Services started:
#   1. CodeCommit MCP Server   (mcp-servers/codecommit/server.py)
#   2. CodePipeline MCP Server (mcp-servers/codepipeline/server.py)
#   3. Backend API             (backend/app.py via uvicorn)
#   4. Frontend Dev Server     (demo-ui via npm run dev)
#
# Usage:
#   ./run-demo.sh
#
# Press Ctrl+C to stop all services.

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"

# --- Colors for output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Track child PIDs for cleanup ---
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}⏹  Shutting down all services...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    # Wait briefly then force-kill any remaining
    sleep 1
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    echo -e "${GREEN}✔  All services stopped.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# --- Helper: print a status message ---
info() {
    echo -e "${BLUE}▶  $1${NC}"
}

error() {
    echo -e "${RED}✖  $1${NC}"
}

success() {
    echo -e "${GREEN}✔  $1${NC}"
}

# --- Pre-flight checks ---
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   CodeSuite Diagnostics Demo — Starting Up      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python is available
if ! command -v python3 &>/dev/null; then
    error "python3 is not installed or not in PATH"
    exit 1
fi

# Check Node/npm is available
if ! command -v npm &>/dev/null; then
    error "npm is not installed or not in PATH"
    exit 1
fi

# --- Start CodeCommit MCP Server ---
info "Starting CodeCommit MCP Server..."
cd "$SCRIPT_DIR/mcp-servers/codecommit"
python3 server.py &
PIDS+=($!)
success "CodeCommit MCP Server started (PID: ${PIDS[-1]})"

# --- Start CodePipeline MCP Server ---
info "Starting CodePipeline MCP Server..."
cd "$SCRIPT_DIR/mcp-servers/codepipeline"
python3 server.py &
PIDS+=($!)
success "CodePipeline MCP Server started (PID: ${PIDS[-1]})"

# --- Start Backend API Server ---
info "Starting Backend API Server (uvicorn on port $BACKEND_PORT)..."
cd "$SCRIPT_DIR/backend"
python3 -m uvicorn app:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload &
PIDS+=($!)
success "Backend API Server started (PID: ${PIDS[-1]})"

# --- Start Frontend Dev Server ---
info "Starting Frontend Dev Server (Vite)..."
cd "$SCRIPT_DIR/demo-ui"
npm run dev &
PIDS+=($!)
success "Frontend Dev Server started (PID: ${PIDS[-1]})"

# --- Ready ---
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   All services are running!                      ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║   Frontend:  http://localhost:5173                ║${NC}"
echo -e "${GREEN}║   Backend:   http://localhost:${BACKEND_PORT}                ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}║   Press Ctrl+C to stop all services.             ║${NC}"
echo -e "${GREEN}║                                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# --- Wait for all background processes ---
wait
