#!/bin/bash

# Server start hote hi Auto-Sync (Download -> Unzip -> Convert to DB)
echo "Auto-Syncing & Converting Databases from Hugging Face..."
python -c "from sync_hf import sync_databases; print(sync_databases())"

# Server start karo
echo "Starting Gunicorn Server..."
gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
