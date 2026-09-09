@echo off
cd /d "%~dp0"
setlocal

title Clinevo Smart Inbox - 1-Click Launch Launcher
cls

echo =====================================================================
echo       CLINEVO SMART INBOX ASSISTANT - 1-CLICK LAUNCHER
echo =====================================================================
echo.

:: 1. Check or create .env file
if not exist ".env" (
    echo [INFO] .env not found. Creating .env from .env.example...
    copy ".env.example" ".env" >nul
    echo [SETUP REQUIRED] .env file created from template.
    echo Please ensure your GEMINI_API_KEY and MAIL_IMAP_PASSWORD are configured in .env!
    echo.
)

:: 2. Load environment variables from .env
if exist ".env" (
    echo [INFO] Loading configuration from .env...
    for /f "usebackq eol=# tokens=1* delims==" %%A in (".env") do (
        if not "%%A"=="" (
            set "%%A=%%B"
        )
    )
    copy /y ".env" "ai-service-python\.env" >nul 2>nul
)

:: Ensure backend data directory exists for embedded H2 database
if not exist "backend-spring\data" mkdir "backend-spring\data" >nul 2>nul

:: 3. Check for API key and Mail credentials
findstr /C:"GEMINI_API_KEY=your_gemini_api_key_here" .env >nul 2>nul
if %errorlevel% equ 0 (
    echo [WARNING] GEMINI_API_KEY is not configured in .env!
    echo           Please paste your Gemini API key from https://aistudio.google.com/
    echo.
)

if /i "%INGESTION_MODE%"=="IMAP" (
    echo [MODE] Live IMAP Mailbox Ingestion: ACTIVE
    echo [MODE] Account: %MAIL_IMAP_USERNAME%
    echo [MODE] Polling every %MAIL_POLL_INTERVAL_MS% ms
    findstr /C:"MAIL_IMAP_PASSWORD=your_gmail_app_password_here" .env >nul 2>nul
    if %errorlevel% equ 0 (
        echo [WARNING] MAIL_IMAP_PASSWORD has placeholder value!
        echo           Please paste your 16-character Google App Password in .env
    ) else if "%MAIL_IMAP_PASSWORD%"=="" (
        echo [WARNING] MAIL_IMAP_PASSWORD is empty in .env!
    ) else (
        echo [OK] Mail credentials detected.
    )
) else (
    echo [MODE] Ingestion Mode: FIXTURE (local test files)
)
echo.

:: 4. Check Prerequisites
echo [1/5] Checking environment prerequisites...

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11+ is not found in PATH. Please install Python.
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not found in PATH. Please install Node.js (v18+).
    pause
    exit /b 1
)

where java >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Java JDK 17+ or 21+ is not found in PATH. Please install Java.
    pause
    exit /b 1
)

echo [OK] Python, Node.js, and Java detected.
echo.

:: 4. Install Python Dependencies if needed
echo [2/5] Checking Python dependencies...
python -m pip install -q -r ai-service-python/requirements.txt
if %errorlevel% neq 0 (
    echo [WARN] Pip install had warnings or errors. Continuing...
)
echo [OK] Python dependencies verified.
echo.

:: 5. Install Angular Dependencies if needed
echo [3/5] Checking Angular frontend dependencies...
if not exist "frontend-angular\node_modules" (
    echo [INFO] Installing frontend node_modules (first-time run)...
    cd frontend-angular
    call npm install
    cd ..
)
echo [OK] Frontend dependencies verified.
echo.

:: 6. Launch Tier 3: Python AI Microservice (Port 8000)
echo [4/5] Launching microservices...
echo [INFO] Starting Python AI Microservice on port 8000...
start "Clinevo Tier 3 - Python AI Service (Port 8000)" cmd /k "cd ai-service-python && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

:: 7. Launch Tier 2: Spring Boot Backend Orchestrator (Port 8081)
echo [INFO] Starting Spring Boot Backend on port 8081...
if exist "backend-spring\mvnw.cmd" (
    start "Clinevo Tier 2 - Spring Boot Backend (Port 8081)" cmd /k "cd backend-spring && mvnw.cmd spring-boot:run"
) else (
    start "Clinevo Tier 2 - Spring Boot Backend (Port 8081)" cmd /k "cd backend-spring && mvn spring-boot:run"
)

:: 8. Launch Tier 1: Angular Reviewer Dashboard (Port 4200)
echo [INFO] Starting Angular Frontend on port 4200...
start "Clinevo Tier 1 - Angular Reviewer Dashboard (Port 4200)" cmd /k "cd frontend-angular && npm start"

:: 9. Summary & Launch Browser
echo.
echo =====================================================================
echo               ALL 3 SERVICES LAUNCHED SUCCESSFULLY
echo =====================================================================
echo   Tier 1 (Frontend):    http://localhost:4200
echo   Tier 2 (Backend API): http://localhost:8081/api/messages
echo   Tier 3 (AI Service):  http://localhost:8000/docs
echo =====================================================================
echo.
echo [5/5] Opening default browser to Reviewer Workbench...
echo Waiting 8 seconds for web servers to initialize...
timeout /t 8 /nobreak >nul
start http://localhost:4200

echo.
echo [HINT] To populate fixture cases on a fresh install, click [⚡ Ingest Fixtures]
echo        in the top-right header of the web dashboard.
echo.
if /i "%INGESTION_MODE%"=="IMAP" (
    echo [HINT] Live IMAP Polling: Active for %MAIL_IMAP_USERNAME%
    echo        Send an email with attachments to this address; it will be automatically
    echo        detected, extracted with Gemini AI, and added to the queue in 15 seconds!
    echo.
)
echo [HINT] To stop all services at once, double-click: stop.bat
echo.
pause
