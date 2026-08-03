import csv
import sqlite3
import os
import sys

def convert(csv_filename):
    db_filename = "data.db"
    if os.path.exists(db_filename):
        print("DB already exists. Skipping conversion.")
        return

    print(f"Converting {csv_filename} to SQLite DB...")
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    with open(csv_filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Table banayenge
        cols = ', '.join([f'"{h}"' for h in headers])
        c.execute(f'CREATE TABLE IF NOT EXISTS api_data ({cols})')
        
        # Data insert karenge batches mein
        batch = []
        count = 0
        for row in reader:
            # Agar row mein columns kam/zyada hain toh adjust karo
            row = (row + [None] * len(headers))[:len(headers)]
            batch.append(row)
            
            if len(batch) >= 5000:
                placeholders = ', '.join(['?'] * len(headers))
                c.executemany(f'INSERT INTO api_data VALUES ({placeholders})', batch)
                conn.commit()
                batch = []
                count += 5000
                print(f"Inserted {count} rows...")
        
        if batch:
            placeholders = ', '.join(['?'] * len(headers))
            c.executemany(f'INSERT INTO api_data VALUES ({placeholders})', batch)
            conn.commit()
            
    conn.close()
    print("Conversion Complete!")

if __name__ == '__main__':
    # Ye script run hote waqt CSV file ka naam lega
    convert("data.csv")
