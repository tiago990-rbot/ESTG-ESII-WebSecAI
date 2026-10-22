@echo off
cd /d "%~dp0frontend"
if not exist .env.local copy .env.example .env.local
npm.cmd install
npm.cmd run dev
pause
