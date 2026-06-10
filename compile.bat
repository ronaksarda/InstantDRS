@echo off
echo Compiling incident_sorter...
g++ -std=c++17 -O2 -o incident_sorter.exe incident_sorter.cpp
if %errorlevel% neq 0 (
    echo Compilation failed!
    exit /b %errorlevel%
)
echo Success! incident_sorter.exe is ready.
