#!/bin/bash

# 1. Server start hote hi Hugging Face se data auto-sync karo
echo "Auto-Syncing Databases from Hugging Face..."
python -c "from sync_hf import sync_databases; print(sync_databases())"

# 2. Agar koi .zip file download hui hai, toh usko unzip karo
if ls *.zip 1> /dev/null 2>&1; then
    echo "Extracting ZIP files..."
    apt-get update && apt-get install -y unzip
    for z in *.zip; do
        unzip -o "$z"
        rm "$z" # Unzip karne ke baad zip delete kar do space bachane ke liye
    done
fi

# 3. Server start karo
echo "Starting Gunicorn Server..."
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
