@echo off
echo Clearing Python cache...

REM Clear main __pycache__
if exist __pycache__ (
    rmdir /s /q __pycache__
    echo Cleared: __pycache__
)

REM Clear auth __pycache__
if exist auth\__pycache__ (
    rmdir /s /q auth\__pycache__
    echo Cleared: auth\__pycache__
)

REM Clear Flask cache
if exist .flask_session (
    rmdir /s /q .flask_session
    echo Cleared: .flask_session
)

echo.
echo Cache cleared successfully!
echo Please restart the Flask server.
echo.
pause
