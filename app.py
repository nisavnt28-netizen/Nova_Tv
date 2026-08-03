from flask import Flask, request, jsonify, render_template_string
import sqlite3
import uuid
import datetime
import csv
import os
import subprocess

app = Flask(__name__)
DB_NAME = 'admin.db'
UPLOAD_FOLDER = '.'  # Current folder se file read karega
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS api_keys
                 (key TEXT PRIMARY KEY, api_name TEXT, db_file TEXT, search_column TEXT, expiry TEXT, active INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- UI CODE (Dark/Neon Hacker Theme) ---
HTML_DASHBOARD = '''
<!DOCTYPE html>
<html>
<head>
    <title>ITACHI API HUB</title>
    <style>
        body { font-family: 'Courier New', Courier, monospace; background: #0d1117; color: #c9d1d9; padding: 15px; }
        h1 { text-align: center; color: #58a6ff; text-shadow: 0 0 10px #58a6ff; }
        .card { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; box-shadow: 0 0 15px rgba(88, 166, 255, 0.1); }
        h2 { color: #3fb950; border-bottom: 1px solid #30363d; padding-bottom: 10px; }
        input, select { width: 95%; padding: 12px; margin: 10px 0; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; border-radius: 5px; box-sizing: border-box; }
        button { background: #238636; color: white; border: none; padding: 12px; width: 95%; font-weight: bold; border-radius: 5px; cursor: pointer; box-sizing: border-box; }
        button:hover { background: #2ea043; }
        .api-box { background: #0d1117; padding: 15px; margin: 10px 0; border-left: 4px solid #f778ba; border-radius: 5px; }
        .api-box b { color: #f778ba; }
        a { color: #58a6ff; text-decoration: none; }
    </style>
</head>
<body>
    <h1>[ ITACHI API HUB ]</h1>
    <div class="card">
        <h2>> Upload Database (.csv, .ac)</h2>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <input type="file" name="db_file" accept=".csv,.ac" required>
            <button type="submit">[ INITIATE UPLOAD ]</button>
        </form>
    </div>

    <div class="card">
        <h2>> Configure New API</h2>
        <form action="/setup" method="GET">
            <select name="file"><option value="">-- Select Database File --</option>{% for f in files %}<option value="{{ f }}">{{ f }}</option>{% endfor %}</select>
            <button type="submit">[ PROCEED TO SETUP ]</button>
        </form>
    </div>

    <div class="card">
        <h2>> Active API Endpoints</h2>
        {% for api in apis %}
        <div class="api-box">
            <b>Endpoint:</b> /api/{{ api.key }}/{{ api.api_name }}/SEARCH_VALUE <br>
            <b>Database:</b> {{ api.db_file }} <br>
            <b>Search By:</b> {{ api.search_column }} <br>
            <b>Expiry:</b> {{ api.expiry }}
        </div>
        {% endfor %}
    </div>
    <p style="text-align:center; color:#30363d;">dev:- ITACHI.....</p>
</body>
</html>
'''

HTML_SETUP = '''
<!DOCTYPE html>
<html><head><title>Setup API</title><style>body{font-family:'Courier New';background:#0d1117;color:#c9d1d9;padding:15px;}h2{color:#3fb950;}.card{background:#161b22;padding:20px;border-radius:8px;border:1px solid #30363d;}input,select{width:95%;padding:12px;margin:10px 0;background:#0d1117;border:1px solid #30363d;color:#c9d1d9;border-radius:5px;}button{background:#238636;color:white;border:none;padding:12px;width:95%;font-weight:bold;border-radius:5px;cursor:pointer;}a{color:#58a6ff;}</style></head>
<body>
    <div class="card">
        <h2>> API Settings - {{ file }}</h2>
        <form action="/generate" method="POST">
            <input type="hidden" name="db_file" value="{{ file }}">
            <label>API Name (e.g., tg_to_num):</label>
            <input type="text" name="api_name" placeholder="tg_to_num" required>
            
            <label>Search Column:</label>
            <select name="search_column">
                {% for col in columns %}
                <option value="{{ col }}">{{ col }}</option>
                {% endfor %}
            </select>
            
            <label>Validity (Days):</label>
            <input type="number" name="days" value="30" required>
            <button type="submit">[ GENERATE API KEY ]</button>
        </form>
        <br><a href="/"><< Back to Dashboard</a>
    </div>
</body></html>
'''

@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM api_keys")
    apis = c.fetchall()
    conn.close()
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(('.csv', '.ac'))]
    api_list = [{'key': r[0], 'api_name': r[1], 'db_file': r[2], 'search_column': r[3], 'expiry': r[4]} for r in apis]
    return render_template_string(HTML_DASHBOARD, files=files, apis=api_list)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['db_file']
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    return "Upload successful! <a href='/'>Go Back</a>"

@app.route('/setup', methods=['GET'])
def setup():
    filename = request.args.get('file')
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        columns = next(reader)
    return render_template_string(HTML_SETUP, file=filename, columns=columns)

@app.route('/generate', methods=['POST'])
def generate():
    db_file = request.form['db_file']
    api_name = request.form['api_name']
    search_column = request.form['search_column']
    days = int(request.form['days'])
    
    new_key = str(uuid.uuid4()).replace('-', '')[:16]
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO api_keys (key, api_name, db_file, search_column, expiry, active) VALUES (?, ?, ?, ?, ?, 1)",
              (new_key, api_name, db_file, search_column, expiry_date))
    conn.commit()
    conn.close()
    
    return f"API Ready! <br>Key: {new_key} <br>Name: {api_name} <br><a href='/'>Dashboard par jao</a>"

@app.route('/api/<api_key>/<api_name>/<search_value>')
def get_data(api_key, api_name, search_value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT db_file, search_column, expiry FROM api_keys WHERE key=? AND api_name=? AND active=1", (api_key, api_name))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"status": "error", "message": "Invalid API Key or Name", "dev": "ITACHI....."}), 403
        
    db_file, search_col, expiry = row
    if datetime.datetime.now().strftime('%Y-%m-%d') > expiry:
        return jsonify({"status": "error", "message": "API Key Expired", "dev": "ITACHI....."})
        
    filepath = os.path.join(UPLOAD_FOLDER, db_file)
    with open(filepath, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.DictReader(f)
        for r in reader:
            db_val = str(r.get(search_col, '')).replace(" ", "").strip()
            search_val_clean = search_value.replace(" ", "").strip()
            if db_val == search_val_clean:
                r["dev"] = "ITACHI....."
                return jsonify({"status": "success", "data": r, "dev": "ITACHI....."})
                
    return jsonify({"status": "error", "message": "Record not found", "dev": "ITACHI....."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
