@echo off
chcp 65001 > nul
if "%~1"=="" (
    start pythonw "%~dp0Merge_PDF.py"
) else (
    python "%~dp0Merge_PDF.py" %*
    pause
)
