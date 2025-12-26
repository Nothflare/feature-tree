: << 'CMDBLOCK'
@echo off
REM Capture current directory (project dir) before changing to plugin root
set "PROJECT_DIR=%CD%"
uv run --directory "%~dp0.." feature-tree --project "%PROJECT_DIR%"
exit /b
CMDBLOCK

# Unix shell
PROJECT_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
uv run --directory "${SCRIPT_DIR}/.." feature-tree --project "${PROJECT_DIR}"
