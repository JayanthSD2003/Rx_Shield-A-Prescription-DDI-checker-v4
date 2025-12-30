
# Cleanup Script
import os
import sqlite3

# Clear Reports
reports_dir = 'reports'
if os.path.exists(reports_dir):
    for f in os.listdir(reports_dir):
        os.remove(os.path.join(reports_dir, f))
    print("Reports cleared.")

# Clear DB
try:
    conn = sqlite3.connect('rx_shield.db')
    cursor = conn.cursor()
    # Assuming 'history' table exists based on context, generic approach:
    cursor.execute("DELETE FROM history") 
    cursor.execute("DELETE FROM analysis_logs")
    conn.commit()
    conn.close()
    print("Database history cleared.")
except Exception as e:
    print(f"DB Error: {e}")
