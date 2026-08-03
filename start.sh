#!/bin/bash

# Agar data.db pehle se nahi bani hai, toh CSV download karo
if [ ! -f "data.db" ]; then
    echo "Downloading CSV file from Google Drive..."
    # Niche wali line mein apna Google Drive Direct Link dalo
    wget "https://drive.google.com/uc?export=download&id=19yUG5W5ea4SNkNTAIjsAnvRI_2yc2XVe" -O data.csv
    
    if [ -f "data.csv" ]; then
        echo "Converting CSV to SQLite DB..."
        python convert_db.py
        
        echo "Cleaning up space (Deleting CSV)..."
        rm data.csv
    else
        echo "Error: data.csv could not be downloaded!"
    fi
fi

# Server start karo
echo "Starting Gunicorn Server..."
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
