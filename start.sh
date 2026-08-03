#!/bin/bash

# Agar data.db pehle se nahi bani hai, toh ye process karo
if [ ! -f "data.db" ]; then
    echo "Installing required tools..."
    apt-get update && apt-get install -y unrar wget
    
    echo "Downloading RAR file..."
    wget "YAHAN_APNA_GOOGLE_DRIVE_DIRECT_LINK_DALEIN" -O data.rar
    
    echo "Extracting RAR file..."
    unrar x -o+ data.rar
    
    # Dhyan rahe: extract hone ke baad aapki CSV file ka naam 'data.csv' hona chahiye
    # Agar naam alag hai, toh niche wali line mein naam change kar lein
    if [ -f "data.csv" ]; then
        echo "Converting to SQLite DB..."
        python convert_db.py
        
        echo "Cleaning up space (Deleting RAR and CSV)..."
        rm data.rar
        rm data.csv
    else
        echo "Error: data.csv not found after extraction!"
    fi
fi

# Server start karo
echo "Starting Gunicorn Server..."
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
