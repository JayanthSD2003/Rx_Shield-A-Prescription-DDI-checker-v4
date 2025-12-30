import sqlite3
import os

DB_NAME = "rx_shield.db"

def clear_database():
    if not os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} not found.")
        return

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # 1. Clear Analyses
        cursor.execute("DELETE FROM analyses")
        print(f"Cleared 'analyses' table.")
        
        # 2. Clear Login Logs
        cursor.execute("DELETE FROM login_logs")
        print(f"Cleared 'login_logs' table.")
        
        # 3. Clear Users except 'admin' and 'root' (preserving root admin)
        # Assuming 'admin' is the default root or we check based on role.
        # Let's check roles first.
        cursor.execute("SELECT username, role FROM users")
        users = cursor.fetchall()
        print("Existing users:", users)
        
        # Strategy: Delete everyone who is NOT 'RootAdmin' OR username 'admin'.
        # Adjust 'admin' check based on actual root username if known, usually 'admin'.
        cursor.execute("DELETE FROM users WHERE role != 'RootAdmin' AND username != 'admin'")
        deleted_count = cursor.rowcount
        print(f"Deleted {deleted_count} users. Preserved RootAdmin/admin.")
        
        conn.commit()
        conn.close()
        print("Database cleanup complete.")
        
    except Exception as e:
        print(f"Error clearing database: {e}")

if __name__ == "__main__":
    clear_database()
