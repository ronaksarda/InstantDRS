@echo off
echo Compiling priority_engine...
g++ -std=c++17 -O2 -o priority_engine.exe priority_engine.cpp
if %errorlevel% neq 0 (
    echo Compilation failed.
    exit /b %errorlevel%
)
echo Success! priority_engine.exe is ready.
