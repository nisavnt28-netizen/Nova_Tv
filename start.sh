#!/bin/bash

# Agar data.db pehle se nahi bani hai, toh download karo
if [ ! -f "data.db" ]; then
    echo "Downloading file from Google Drive..."
    wget "https://drive.google.com/uc?export=download&id=1oly9xfhKoPE0_pMMqPSJROmzHYich4N6" -O downloaded_file
    
    # Check karo ki downloaded file DB hai ya CSV
    if grep -q "SQLite format 3" downloaded_file; then
        echo "Downloaded file is already a DB. Renaming to data.db..."
        mv downloaded_file data.db
    else
        echo "Downloaded file is CSV. Converting to DB..."
        mv downloaded_file data.csv
        python convert_db.py
        rm data.csv # Space bachane ke liye CSV delete karo
    fi
fi

# Server start karo
echo "Starting Gunicorn Server..."
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
