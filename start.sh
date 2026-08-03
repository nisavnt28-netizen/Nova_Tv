#!/bin/bash

# Agar server pe file nahi hai, toh Google Drive se download karo
if [ ! -f "data.csv" ]; then
    echo "Downloading database from Google Drive..."
    wget "LINK_HERE" -O data.csv
fi

# Gunicorn server start karo (Render ke liye)
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
