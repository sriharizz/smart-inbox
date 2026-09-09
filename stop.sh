#!/usr/bin/env bash
echo "Stopping all Clinevo Smart Inbox services..."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "spring-boot:run" 2>/dev/null
pkill -f "ng serve" 2>/dev/null
echo "All services stopped."
