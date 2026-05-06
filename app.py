from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import sqlite3
from datetime import datetime
import io
import csv

app = Flask(__name__)
CORS(app)

DB_NAME = 'surveys.db'

def init_db():
    """Create tables if they don't exist – never drop or delete existing data."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS surveys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        role TEXT,
        years TEXT,
        we1 INTEGER, we2 INTEGER, we3 INTEGER,
        wl1 INTEGER, wl2 INTEGER, wl3 INTEGER,
        mg1 INTEGER, mg2 INTEGER, mg3 INTEGER,
        js1 INTEGER, js2 INTEGER, js3 INTEGER,
        tr1 INTEGER, tr2 INTEGER,
        challenge TEXT, improve TEXT, additional TEXT
    )''')
    conn.commit()
    conn.close()
    print("Database ready (existing data preserved).")

def serialize_survey(row):
    return {
        "id": row[0],
        "timestamp": row[1],
        "role": row[2],
        "years": row[3],
        "ratings": {
            "workEnv": [row[4], row[5], row[6]],
            "workload": [row[7], row[8], row[9]],
            "management": [row[10], row[11], row[12]],
            "jobSat": [row[13], row[14], row[15]],
            "training": [row[16], row[17]]
        },
        "openEnded": {
            "challenge": row[18] or "",
            "improve": row[19] or "",
            "additional": row[20] or ""
        }
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_survey():
    data = request.json
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO surveys 
        (timestamp, role, years,
         we1, we2, we3,
         wl1, wl2, wl3,
         mg1, mg2, mg3,
         js1, js2, js3,
         tr1, tr2,
         challenge, improve, additional)
        VALUES (?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?, ?,?,?)''',
        (datetime.now().isoformat(),
         data['role'], data['years'],
         data['ratings']['workEnv'][0], data['ratings']['workEnv'][1], data['ratings']['workEnv'][2],
         data['ratings']['workload'][0], data['ratings']['workload'][1], data['ratings']['workload'][2],
         data['ratings']['management'][0], data['ratings']['management'][1], data['ratings']['management'][2],
         data['ratings']['jobSat'][0], data['ratings']['jobSat'][1], data['ratings']['jobSat'][2],
         data['ratings']['training'][0], data['ratings']['training'][1],
         data['openEnded']['challenge'], data['openEnded']['improve'], data['openEnded']['additional']))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})

@app.route('/api/surveys', methods=['GET'])
def get_surveys():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM surveys ORDER BY id')
    rows = c.fetchall()
    conn.close()
    surveys = [serialize_survey(row) for row in rows]
    return jsonify(surveys)

@app.route('/admin/reset', methods=['POST'])
def reset_data():
    pwd = request.json.get('password')
    if pwd != 'admin123':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM surveys')
    conn.commit()
    conn.close()
    return jsonify({"status": "reset done"})

@app.route('/admin/restore', methods=['POST'])
def restore_data():
    pwd = request.json.get('password')
    if pwd != 'admin123':
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json.get('data')
    if not isinstance(data, list):
        return jsonify({"error": "Invalid data"}), 400
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM surveys')
    for s in data:
        c.execute('''INSERT INTO surveys 
            (timestamp, role, years,
             we1, we2, we3,
             wl1, wl2, wl3,
             mg1, mg2, mg3,
             js1, js2, js3,
             tr1, tr2,
             challenge, improve, additional)
            VALUES (?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?,?, ?,?, ?,?,?)''',
            (s['timestamp'], s['role'], s['years'],
             s['ratings']['workEnv'][0], s['ratings']['workEnv'][1], s['ratings']['workEnv'][2],
             s['ratings']['workload'][0], s['ratings']['workload'][1], s['ratings']['workload'][2],
             s['ratings']['management'][0], s['ratings']['management'][1], s['ratings']['management'][2],
             s['ratings']['jobSat'][0], s['ratings']['jobSat'][1], s['ratings']['jobSat'][2],
             s['ratings']['training'][0], s['ratings']['training'][1],
             s['openEnded']['challenge'], s['openEnded']['improve'], s['openEnded']['additional']))
    conn.commit()
    conn.close()
    return jsonify({"status": "restored"})

@app.route('/admin/export/csv', methods=['GET'])
def export_csv():
    pwd = request.args.get('password')
    if pwd != 'admin123':
        return jsonify({"error": "Unauthorized"}), 401
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT * FROM surveys')
    rows = c.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Timestamp', 'Role', 'Years',
                     'WE_Q1','WE_Q2','WE_Q3',
                     'WL_Q1','WL_Q2','WL_Q3',
                     'MGMT_Q1','MGMT_Q2','MGMT_Q3',
                     'JS_Q1','JS_Q2','JS_Q3',
                     'TRAIN_Q1','TRAIN_Q2',
                     'Challenge','Improvement','Additional'])
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='gweru_survey_data.csv')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)