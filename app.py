from flask import Flask, request, jsonify, render_template_string
import sqlite3
import uuid
import datetime
import os
from sync_hf import sync_databases  # Hugging Face Sync script

app = Flask(__name__)
DB_NAME = 'admin.db'

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
        button { background: #238636; color: white; border: none; padding: 12px; width: 95%; font-weight: bold; border-radius: 5px; cursor: pointer; box-sizing: border-box; margin-top: 10px; }
        button:hover { background: #2ea043; }
        .api-box { background: #0d1117; padding: 15px; margin: 10px 0; border-left: 4px solid #f778ba; border-radius: 5px; }
        .api-box b { color: #f778ba; }
        a { color: #58a6ff; text-decoration: none; }
        .sync-btn { background: #f778ba; width: 95%; }
        .sync-btn:hover { background: #d65aa0; }
        .msg { color: #3fb950; margin-top: 10px; font-weight: bold; }
        select[multiple] { height: 120px; }
    </style>
</head>
<body>
    <h1>[ ITACHI API HUB ]</h1>
    
    <!-- Hugging Face Sync Card -->
    <div class="card">
        <h2>> Auto-Sync Hugging Face</h2>
        <form action="/sync" method="POST">
            <button type="submit" class="sync-btn">[ SYNC DATABASES NOW ]</button>
        </form>
        {% if sync_msg %}
        <p class="msg">{{ sync_msg }}</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>> Available Databases</h2>
        {% if files %}
            <ul style="color: #3fb950; padding-left: 20px;">
            {% for f in files %}
                <li>{{ f }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p style="color: #f85149;">✗ No databases found. Sync from Hugging Face or check logs.</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>> Configure New API</h2>
        <form action="/setup" method="GET">
            <label>Select Database(s) [Ctrl/Cmd + Click for Multiple]:</label>
            <select name="file" multiple required>
                {% for f in files %}
                <option value="{{ f }}">{{ f }}</option>
                {% endfor %}
            </select>
            <button type="submit">[ PROCEED TO SETUP ]</button>
        </form>
    </div>

    <div class="card">
        <h2>> Active API Endpoints</h2>
        {% for api in apis %}
        <div class="api-box">
            <b>Endpoint:</b> /api/{{ api.key }}/{{ api.api_name }}/SEARCH_VALUE <br>
            <b>Database(s):</b> {{ api.db_file }} <br>
            <b>Search By:</b> {{ api.search_column }} <br>
            <b>Expiry:</b> {{ api.expiry }}
        </div>
        {% else %}
        <p>No active APIs yet.</p>
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
        <h2>> API Settings</h2>
        <form action="/generate" method="POST">
            <input type="hidden" name="db_files" value="{{ files }}">
            <label>API Name (e.g., all_info):</label>
            <input type="text" name="api_name" placeholder="all_info" required>
            
            {% if is_multi %}
                <!-- Multi DB Smart Search -->
                <label>Search Keyword (e.g., phone, number, aadhar):</label>
                <input type="text" name="search_column" placeholder="number" required>
                <p style="font-size: 12px; color: #8b949e;">* Smart Mode: System will auto-detect similar columns (like Phone, Mobile, Contact) in all selected DBs.</p>
            {% else %}
                <!-- Single DB Dropdown -->
                <label>Select Search Column:</label>
                <select name="search_column">
                    {% for col in columns %}
                    <option value="{{ col }}">{{ col }}</option>
                    {% endfor %}
                </select>
            {% endif %}
            
            <label>Validity (Days):</label>
            <input type="number" name="days" value="30" required>
            <button type="submit">[ GENERATE API KEY ]</button>
        </form>
        <br><a href="/"><< Back to Dashboard</a>
    </div>
</body></html>
'''

def render_dashboard(sync_msg=''):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM api_keys")
    apis = c.fetchall()
    conn.close()
    files = [f for f in os.listdir('.') if f.endswith('.db') and f != 'admin.db']
    api_list = [{'key': r[0], 'api_name': r[1], 'db_file': r[2], 'search_column': r[3], 'expiry': r[4]} for r in apis]
    return render_template_string(HTML_DASHBOARD, files=files, apis=api_list, sync_msg=sync_msg)

@app.route('/')
def dashboard():
    return render_dashboard()

@app.route('/sync', methods=['POST'])
def sync_now():
    msg = sync_databases()
    return render_dashboard(sync_msg=msg)

@app.route('/setup', methods=['GET'])
def setup():
    files = request.args.getlist('file')
    files_str = ", ".join(files)
    
    # Agar 1 se zyada DB select ki hai, toh text box dikhao. Agar 1 hai toh list dikhao
    if len(files) > 1:
        return render_template_string(HTML_SETUP, files=files_str, is_multi=True, columns=[])
    else:
        # Single DB ke columns nikalo
        try:
            conn = sqlite3.connect(files[0])
            c = conn.cursor()
            c.execute("PRAGMA table_info(api_data)")
            columns = [row[1] for row in c.fetchall()]
            conn.close()
        except:
            columns = []
        return render_template_string(HTML_SETUP, files=files_str, is_multi=False, columns=columns)

@app.route('/generate', methods=['POST'])
def generate():
    db_files = request.form['db_files']
    api_name = request.form['api_name']
    search_column = request.form['search_column']
    days = int(request.form['days'])
    
    new_key = str(uuid.uuid4()).replace('-', '')[:16]
    expiry_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO api_keys (key, api_name, db_file, search_column, expiry, active) VALUES (?, ?, ?, ?, ?, 1)",
              (new_key, api_name, db_files, search_column, expiry_date))
    conn.commit()
    conn.close()
    
    return f"API Ready! <br>Key: {new_key} <br>Name: {api_name} <br>Databases: {db_files} <br><a href='/'>Dashboard par jao</a>"

# --- ASLI API ENDPOINT (Smart Multi-DB Search) ---
@app.route('/api/<api_key>/<api_name>/<search_value>')
def get_data(api_key, api_name, search_value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT db_file, search_column, expiry FROM api_keys WHERE key=? AND api_name=? AND active=1", (api_key, api_name))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"status": "error", "message": "Invalid API Key or Name", "dev": "ITACHI....."}), 403
        
    db_files_str, search_hint, expiry = row
    if datetime.datetime.now().strftime('%Y-%m-%d') > expiry:
        return jsonify({"status": "error", "message": "API Key Expired contact admin @ITACHI_UCHIHA_34", "dev": "ITACHI....."})
        
    db_files = [f.strip() for f in db_files_str.split(',')]
    search_val_clean = search_value.replace(" ", "").strip()
    
    # Smart keywords jo automatically column dhoondhne ke kaam aayenge
    keywords = ['phone', 'mobile', 'number', 'contact', 'tel', 'cell', 'no', 'uid', 'aadhar', 'id', search_hint.lower()]
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            continue
            
        try:
            db_conn = sqlite3.connect(db_file)
            db_conn.row_factory = sqlite3.Row
            db_c = db_conn.cursor()
            
            # DB ke saare columns nikalo
            db_c.execute("PRAGMA table_info(api_data)")
            all_cols = [row[1] for row in db_c.fetchall()]
            
            # Smart Match: Check karo kis column mein phone/number jaisa word hai
            target_cols = []
            for col in all_cols:
                col_lower = col.lower()
                if any(kw in col_lower for kw in keywords):
                    target_cols.append(col)
                    
            # Agar exact match na mile, toh user ne jo hint diya usko use karo
            if not target_cols and search_hint in all_cols:
                target_cols = [search_hint]
                
            if not target_cols:
                db_conn.close()
                continue # Is DB mein koi relevant column nahi hai, next DB check karo
                
            # Jo columns match hue, un sab mein search karo
            query_parts = [f'REPLACE("{c}", " ", "") = ?' for c in target_cols]
            query = f'SELECT * FROM api_data WHERE {" OR ".join(query_parts)} LIMIT 1'
            params = [search_val_clean] * len(target_cols)
            
            db_c.execute(query, params)
            result = db_c.fetchone()
            db_conn.close()
            
            if result:
                data = dict(result)
                data["dev"] = "ITACHI....."
                data["matched_columns"] = target_cols
                return jsonify({"status": "success", "data": data, "dev": "ITACHI....."})
                
        except Exception as e:
            continue
            
    return jsonify({"status": "error", "message": "Record not found in any database", "dev": "ITACHI....."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
