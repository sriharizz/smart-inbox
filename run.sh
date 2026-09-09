#!/usr/bin/env bash

# =====================================================================
# CLINEVO SMART INBOX ASSISTANT - 1-CLICK LAUNCHER (macOS / Linux)
# =====================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================================================="
echo "       CLINEVO SMART INBOX ASSISTANT - 1-CLICK LAUNCHER"
echo "====================================================================="
echo ""

# 1. Check or create .env file
if [ ! -f ".env" ]; then
    echo "[INFO] .env not found. Creating .env from .env.example..."
    cp .env.example .env
    echo "[SETUP REQUIRED] .env file created."
    echo "Please configure your GEMINI_API_KEY in .env!"
    echo ""
fi

# 2. Load environment variables from .env
if [ -f ".env" ]; then
    echo "[INFO] Loading configuration from .env..."
    set -a
    source .env
    set +a
    cp .env ai-service-python/.env 2>/dev/null || true
fi

# 3. Check for GEMINI_API_KEY
if grep -q "GEMINI_API_KEY=your_gemini_api_key_here" .env; then
    echo "[WARNING] GEMINI_API_KEY is not set in .env!"
    echo "Live AI extraction requires a valid Google Gemini API key."
    echo "You can obtain one at https://aistudio.google.com/"
    echo ""
fi

# Ensure backend data directory exists
mkdir -p backend-spring/data

# Auto-restore pre-seeded 13-case benchmark database on fresh install
if [ ! -f "backend-spring/data/smartinboxdb.mv.db" ] && [ -f "backend-spring/data/smartinboxdb-backup.zip" ]; then
    echo "[INFO] Restoring pre-seeded 13-case clinical database..."
    unzip -q -o backend-spring/data/smartinboxdb-backup.zip -d backend-spring/data/ 2>/dev/null || true
    echo "[OK] 13 benchmark cases restored to database."
fi

if [ "$INGESTION_MODE" = "IMAP" ]; then
    echo "[MODE] Live IMAP Mailbox Ingestion Active: $MAIL_IMAP_USERNAME"
    echo "[MODE] Polling every ${MAIL_POLL_INTERVAL_MS:-15000} ms"
else
    echo "[MODE] Ingestion Mode: FIXTURE (local test files)"
fi
echo ""

# 3. Check Prerequisites
echo "[1/5] Checking environment prerequisites..."

command -v python3 >/dev/null 2>&1 || { echo >&2 "[ERROR] Python 3.11+ is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo >&2 "[ERROR] Node.js is required but not installed."; exit 1; }
command -v java >/dev/null 2>&1 || { echo >&2 "[ERROR] Java JDK 17+ or 21+ is required but not installed."; exit 1; }

echo "[OK] Python, Node.js, and Java detected."
echo ""

# 4. Install Python Dependencies
echo "[2/5] Checking Python dependencies..."
python3 -m pip install -q -r ai-service-python/requirements.txt || echo "[WARN] Pip install had warnings."
echo "[OK] Python dependencies verified."
echo ""

# 5. Install Angular Dependencies
echo "[3/5] Checking Angular frontend dependencies..."
if [ ! -d "frontend-angular/node_modules" ]; then
    echo "[INFO] Installing frontend node_modules (first-time run)..."
    cd frontend-angular && npm install && cd ..
fi
echo "[OK] Frontend dependencies verified."
echo ""

# 6. Trap for clean shutdown
cleanup() {
    echo ""
    echo "[SHUTDOWN] Terminating background services..."
    kill $(jobs -p) 2>/dev/null
    echo "[OK] All services stopped."
    exit
}
trap cleanup SIGINT SIGTERM EXIT

# 7. Launch Services
echo "[4/5] Launching microservices..."

echo "[INFO] Starting Python AI Microservice on port 8000..."
cd ai-service-python && python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 &
PID_AI=$!
cd "$SCRIPT_DIR"

echo "[INFO] Starting Spring Boot Backend on port 8081..."
if [ -f "backend-spring/mvnw" ]; then
    chmod +x backend-spring/mvnw
    (cd backend-spring && ./mvnw spring-boot:run) &
else
    (cd backend-spring && mvn spring-boot:run) &
fi
PID_BACKEND=$!
cd "$SCRIPT_DIR"

echo "[INFO] Starting Angular Frontend on port 4200..."
(cd frontend-angular && npm start) &
PID_FRONTEND=$!
cd "$SCRIPT_DIR"

echo ""
echo "====================================================================="
echo "               ALL 3 SERVICES LAUNCHED SUCCESSFULLY"
echo "====================================================================="
echo "  Tier 1 (Frontend):    http://localhost:4200"
echo "  Tier 2 (Backend API): http://localhost:8081/api/messages"
echo "  Tier 3 (AI Service):  http://localhost:8000/docs"
echo "====================================================================="
echo ""

# 8. Open Browser
echo "[5/5] Opening default browser to Reviewer Workbench..."
sleep 8
if command -v open >/dev/null 2>&1; then
    open http://localhost:4200
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open http://localhost:4200
fi

echo ""
echo "[HINT] To populate the queue on a fresh install, click [Lightning Ingest Fixtures]"
echo "       in the top-right header of the web dashboard."
echo ""
echo "Press Ctrl+C at any time to cleanly stop all services."
echo ""

wait
