@echo off
chcp 65001 >nul
echo ========================================
echo        DPKI Platform Launcher
echo ========================================
echo.

REM Set working directory
cd /d "%~dp0"

echo [1/6] Checking for existing processes...

REM Kill existing Node.js processes on port 3001
echo Stopping existing web server processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3001 2^>nul') do (
    echo   Stopping web server process %%a...
    taskkill /f /pid %%a >nul 2>&1
)

REM Kill existing omni.exe processes
echo Stopping existing blockchain processes...
taskkill /f /im omni.exe >nul 2>&1

REM Kill existing Java processes (DID service)
echo Stopping existing DID service processes...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq java.exe" /fo table /nh 2^>nul') do (
    for /f "tokens=*" %%b in ('netstat -ano ^| findstr :8080 ^| findstr %%a 2^>nul') do (
        echo   Stopping DID service process %%a...
        taskkill /f /pid %%a >nul 2>&1
    )
)

REM Additional cleanup for any remaining Java processes running omni-did
wmic process where "commandline like '%%omni-did%%'" delete >nul 2>&1

echo   Cleaned up existing processes.

echo.
echo [2/6] Starting blockchain platform...
echo Starting omni.exe...
start "DPKI Blockchain" /D "%~dp0bin" omni.exe -f "..\config\omni.toml"

echo.
echo [3/6] Waiting for blockchain initialization...
timeout /t 5 /nobreak >nul

echo.
echo [4/6] Starting DID service...
echo Starting DID Service...
start "DID Service" /D "%~dp0omni-did" java -jar target/omni-did-0.0.1-SNAPSHOT.jar

echo.
echo [5/6] Waiting for services initialization...
timeout /t 3 /nobreak >nul

echo.
echo [6/6] Starting web server...
echo Starting DPKI Web Server...
start "DPKI Web Server" node web-server.js

echo.
echo ========================================
echo   DPKI Platform Started Successfully!
echo.
echo   Access URLs:
echo   - Home: http://localhost:3001
echo   - CA Management: http://localhost:3001/ca.html  
echo   - UE Management: http://localhost:3001/ue.html
echo   - DID Management: http://localhost:3001/did.html
echo   - DID Service API: http://localhost:8080
echo.
echo   Press any key to exit launcher...
echo ========================================
pause >nul