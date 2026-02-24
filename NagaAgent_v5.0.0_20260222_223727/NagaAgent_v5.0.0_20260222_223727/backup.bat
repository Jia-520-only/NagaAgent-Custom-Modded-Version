@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ============================================================
echo.
echo              NagaAgent Full Backup Tool
echo.
echo     Complete Migration - All Configs & Files
echo.
echo ============================================================
echo.

python backup_project.py

pause

