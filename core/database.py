import sqlite3
import os
import datetime

DB_NAME = "rx_shield.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table with role and approval status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'User',
            is_approved INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analysis table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT NOT NULL, 
            image_path TEXT NOT NULL, 
            result_text TEXT NOT NULL, 
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    # Login logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(username, password_hash, role='User', is_approved=0):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password_hash, role, is_approved) VALUES (?, ?, ?, ?)', 
                      (username, password_hash, role, is_approved))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
    users = cursor.fetchall()
    conn.close()
    return users

def update_user_approval(username, is_approved):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_approved = ? WHERE username = ?', (is_approved, username))
    conn.commit()
    conn.close()

def update_user_password(username, new_password_hash):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_password_hash, username))
    conn.commit()
    conn.close()

def log_login(username, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO login_logs (username, status) VALUES (?, ?)', (username, status))
    conn.commit()
    conn.close()

def get_login_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM login_logs ORDER BY timestamp DESC')
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_analysis_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analyses ORDER BY timestamp DESC')
    logs = cursor.fetchall()
    conn.close()
    return logs

def get_admin_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM users WHERE role = 'Admin'")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_analyses_by_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM analyses WHERE username = ? ORDER BY timestamp DESC', (username,))
    logs = cursor.fetchall()
    conn.close()
    return logs

def save_analysis(username, image_path, result_text):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO analyses (username, image_path, result_text) VALUES (?, ?, ?)", 
                  (username, image_path, result_text))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error saving analysis: {e}")
        return False
    finally:
        conn.close()

def get_recent_analysis(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT image_path, result_text FROM analyses WHERE username=? ORDER BY timestamp DESC LIMIT 1", (username,))
        result = cursor.fetchone()
        return result # (image_path, result_text) or None
    except Exception as e:
        print(f"Error getting analysis: {e}")
        return None
    finally:
        conn.close()
