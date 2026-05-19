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
            month TEXT NOT NULL,
            modality TEXT NOT NULL,
            model TEXT NOT NULL,
            token REAL NOT NULL,
            revenue REAL NOT NULL,
            calls REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_month ON model_data(month)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_model ON model_data(model)
    ''')
    
    conn.commit()
    conn.close()

def insert_data(month, modality, model, token, revenue, calls):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO model_data (month, modality, model, token, revenue, calls)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (month, modality, model, token, revenue, calls))
    
    conn.commit()
    conn.close()

def get_data_by_month(month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT month, modality, model, token, revenue, calls
        FROM model_data
        WHERE month = ?
        ORDER BY modality, model
    ''', (month,))
    
    columns = ['month', 'modality', 'model', 'token', 'revenue', 'calls']
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    
    return data

def get_all_months():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT month
        FROM model_data
        ORDER BY month DESC
    ''')
    
    months = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return months

def check_month_exists(month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM model_data WHERE month = ?
    ''', (month,))
    
    count = cursor.fetchone()[0]
    conn.close()
    
    return count > 0

def delete_month_data(month):
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        DELETE FROM model_data WHERE month = ?
    ''', (month,))
    
    conn.commit()
    conn.close()
