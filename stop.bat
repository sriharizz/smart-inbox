@echo off
title Clinevo Smart Inbox - Stop All Services
cls

echo =====================================================================
echo          STOPPING CLINEVO SMART INBOX SERVICES
echo =====================================================================
echo.

echo [INFO] Terminating processes on Port 4200 (Angular)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":4200" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo [INFO] Terminating processes on Port 8081 (Spring Boot)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8081" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo [INFO] Terminating processes on Port 8000 (Python AI Service)...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>nul
)

echo.
echo [OK] All Clinevo Smart Inbox services stopped.
echo.
pause
