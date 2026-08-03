import csv
import sqlite3
import os

def convert():
    csv_filename = "data.csv"
    db_filename = "data.db"
    
    print(f"Converting {csv_filename} to SQLite DB...")
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    with open(csv_filename, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        headers = next(reader)
        
        # Clean headers (Null characters remove karna)
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
                print(f"Inserted {count} rows...")
                
        if batch:
            placeholders = ', '.join(['?'] * len(clean_headers))
            c.executemany(f'INSERT INTO api_data VALUES ({placeholders})', batch)
            conn.commit()
            
    conn.close()
    print("Conversion Complete!")

if __name__ == '__main__':
    convert()
