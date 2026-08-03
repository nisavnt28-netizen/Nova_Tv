import os
import subprocess
import zipfile
import csv
import sqlite3
from huggingface_hub import HfApi, hf_hub_download

def convert_csv_to_db(csv_filename):
    db_filename = csv_filename.rsplit('.', 1)[0] + '.db'
    if os.path.exists(db_filename):
        return
        
    print(f"Converting {csv_filename} to SQLite DB...")
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    with open(csv_filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Clean headers
        clean_headers = []
        for h in headers:
            clean_h = str(h).replace('\x00', '').replace('\ufeff', '').strip()
            if not clean_h:
                clean_h = f"col_{len(clean_headers)}"
            clean_headers.append(clean_h)
        
        cols = ', '.join([f'"{h}"' for h in clean_headers])
        c.execute('DROP TABLE IF EXISTS api_data')
        c.execute(f'CREATE TABLE api_data ({cols})')
        
        batch = []
        count = 0
        for row in reader:
            row = (row + [None] * len(clean_headers))[:len(clean_headers)]
            batch.append(row)
            if len(batch) >= 5000:
                placeholders = ', '.join(['?'] * len(clean_headers))
                c.executemany(f'INSERT INTO api_data VALUES ({placeholders})', batch)
                conn.commit()
                batch = []
                count += 5000
        if batch:
            placeholders = ', '.join(['?'] * len(clean_headers))
            c.executemany(f'INSERT INTO api_data VALUES ({placeholders})', batch)
            conn.commit()
    conn.close()
    print(f"✓ {db_filename} ban gaya!")
    os.remove(csv_filename) # Delete CSV to save space

def sync_databases():
    token = os.environ.get("HF_TOKEN")
    repo_id = os.environ.get("HF_REPO_ID")
    
    if not token or not repo_id:
        return "Environment Variables (HF_TOKEN, HF_REPO_ID) set nahi hain!"
        
    try:
        api = HfApi()
        files = api.list_repo_files(repo_id=repo_id, repo_type="dataset", token=token)
        
        downloaded = []
        for file in files:
            if file.endswith(('.db', '.csv', '.zip')):
                if not os.path.exists(file) and not os.path.exists(file.replace('.csv', '.db').replace('.zip', '.db')):
                    print(f"Downloading {file}...")
                    hf_hub_download(repo_id=repo_id, filename=file, repo_type="dataset", token=token, local_dir=".")
                    downloaded.append(file)
                    
        # Process downloaded files
        for file in downloaded:
            if file.endswith('.csv'):
                convert_csv_to_db(file)
            elif file.endswith('.zip'):
                print(f"Extracting {file}...")
                with zipfile.ZipFile(file, 'r') as zip_ref:
                    zip_ref.extractall('.')
                os.remove(file)
                # Agar zip ke andar CSV nikla, toh usko bhi DB bana do
                for root, dirs, files in os.walk('.'):
                    for f in files:
                        if f.endswith('.csv'):
                            convert_csv_to_db(f)
                            
        if not downloaded:
            return "Sab files pehle se synced hain. Koi nayi file nahi mili."
        else:
            # Clean up downloaded list for message
            processed = [f.replace('.csv', '.db').replace('.zip', '.db') for f in downloaded]
            return f"Successfully Synced & Processed: {', '.join(processed)}"
            
    except Exception as e:
        return f"Error: {str(e)}"
