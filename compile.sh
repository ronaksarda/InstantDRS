#!/bin/bash
echo "Compiling priority_engine..."
g++ -std=c++17 -O2 -o priority_engine priority_engine.cpp
if [ $? -ne 0 ]; then
    echo "Compilation failed."
    exit 1
fi
echo "Success! priority_engine is ready."
