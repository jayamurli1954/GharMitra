@echo off
REM Auto-detect IP address for Windows
REM Returns the first non-localhost IPv4 address

for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set IP=%%a
    set IP=!IP:~1!
    echo !IP!
    exit /b
)

echo localhost

