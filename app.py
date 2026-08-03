from flask import Flask, request, jsonify, render_template_string
import sqlite3
import uuid
import datetime
import os

app = Flask(__name__)
DB_NAME = 'admin.db'
DATA_DB = 'data.db' # Ye aapki 2GB ki file ka DB banega

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
        .api-box { background: #0d1117; padding: 15px; margin: 10px 0; border-left: 4px solid #f778ba; border-radius: 5px; }
        .api-box b { color: #f778ba; }
        a { color: #58a6ff; text-decoration: none; }
    </style>
</head>
<body>
    <h1>[ ITACHI API HUB ]</h1>
    <div class="card">
        <h2>> Database Status</h2>
        {% if db_exists %}
        <p style="color: #3fb950;">✓ SQLite Database (data.db) Loaded Successfully!</p>
        {% else %}
        <p style="color: #f85149;">✗ Database Not Found. Please check start.sh logs.</p>
        {% endif %}
    </div>

    <div class="card">
        <h2>> Configure New API</h2>
        <form action="/setup" method="GET">
            <input type="hidden" name="file" value="data.db">
            <button type="submit">[ PROCEED TO SETUP ]</button>
        </form>
    </div>

    <div class="card">
        <h2>> Active API Endpoints</h2>
        {% for api in apis %}
        <div class="api-box">
            <b>Endpoint:</b> /api/{{ api.key }}/{{ api.api_name }}/SEARCH_VALUE <br>
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
    db_exists = os.path.exists(DATA_DB)
    api_list = [{'key': r[0], 'api_name': r[1], 'db_file': r[2], 'search_column': r[3], 'expiry': r[4]} for r in apis]
    return render_template_string(HTML_DASHBOARD, db_exists=db_exists, apis=api_list)

@app.route('/setup', methods=['GET'])
def setup():
    # SQLite DB ke columns read kar rhe hain
    conn = sqlite3.connect(DATA_DB)
    c = conn.cursor()
    c.execute("PRAGMA table_info(api_data)") # api_data table ka naam hai
    columns = [row[1] for row in c.fetchall()]
    conn.close()
    return render_template_string(HTML_SETUP, file="data.db", columns=columns)

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

# --- ASLI API ENDPOINT (SQLite Search) ---
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
        
    # SQLite Database mein search karenge ab (bahut fast hoga)
    conn = sqlite3.connect(DATA_DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Spaces hata kar search karenge taaki Aadhar number mil jaye
    query = f'SELECT * FROM api_data WHERE REPLACE("{search_col}", " ", "") = ?'
    c.execute(query, (search_value.replace(" ", "").strip(),))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        data = dict(result)
        data["dev"] = "ITACHI....."
        return jsonify({"status": "success", "data": data, "dev": "ITACHI....."})
        
    return jsonify({"status": "error", "message": "Record not found", "dev": "ITACHI....."}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
