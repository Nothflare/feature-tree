: << 'CMDBLOCK'
@echo off
REM Polyglot wrapper: runs Python scripts cross-platform
REM Usage: run-python-hook.cmd <script-name>

python "%~dp0%~1"
exit /b
CMDBLOCK

# Unix shell runs from here
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
python3 "${SCRIPT_DIR}/${SCRIPT_NAME}"
