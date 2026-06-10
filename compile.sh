#!/bin/bash
echo "Compiling incident_sorter..."
g++ -std=c++17 -O2 -o incident_sorter incident_sorter.cpp
if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi
echo "Success! incident_sorter is ready."
