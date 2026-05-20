import sqlite3
import os
from flask import current_app

def get_db_path():
    return os.path.join(current_app.config['DATABASE_FOLDER'], 'model_data.db')

def init_database():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            month TEXT NOT NULL,
            modality TEXT NOT NULL,
            model TEXT NOT NULL,
            token REAL NOT NULL,
            revenue REAL NOT NULL,
            calls REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("PRAGMA table_info(model_data)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'company' not in columns:
        cursor.execute('ALTER TABLE model_data ADD COLUMN company TEXT NOT NULL DEFAULT "未知"')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_company_month ON model_data(company, month)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_model ON model_data(model)
    ''')
    
    conn.commit()
    conn.close()

def insert_data(company, month, modality, model, token, revenue, calls):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO model_data (company, month, modality, model, token, revenue, calls)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (company, month, modality, model, token, revenue, calls))
    
    conn.commit()
    conn.close()

def get_data_by_month(company, month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT company, month, modality, model, token, revenue, calls
        FROM model_data
        WHERE company = ? AND month = ?
        ORDER BY modality, model
    ''', (company, month))
    
    columns = ['company', 'month', 'modality', 'model', 'token', 'revenue', 'calls']
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return data

def get_all_months():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT company, month
        FROM model_data
        ORDER BY company DESC, month DESC
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def check_month_exists(company, month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM model_data WHERE company = ? AND month = ?
    ''', (company, month))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def delete_month_data(company, month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM model_data WHERE company = ? AND month = ?
    ''', (company, month))
    
    cursor.execute('''
        DELETE FROM scenario_data WHERE company = ? AND month = ?
    ''', (company, month))
    
    conn.commit()
    conn.close()

def init_scenario_database():
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scenario_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            month TEXT NOT NULL,
            scenario TEXT NOT NULL,
            calls REAL NOT NULL DEFAULT 0,
            token REAL NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_scenario_company_month ON scenario_data(company, month)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_scenario ON scenario_data(scenario)
    ''')
    
    conn.commit()
    conn.close()

def insert_scenario_data(company, month, scenario, calls, token):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO scenario_data (company, month, scenario, calls, token)
        VALUES (?, ?, ?, ?, ?)
    ''', (company, month, scenario, calls, token))
    
    conn.commit()
    conn.close()

def get_scenario_by_month(company, month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT company, month, scenario, calls, token
        FROM scenario_data
        WHERE company = ? AND month = ?
        ORDER BY scenario
    ''', (company, month))
    
    columns = ['company', 'month', 'scenario', 'calls', 'token']
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return data
