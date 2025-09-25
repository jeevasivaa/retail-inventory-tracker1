import sqlite3
import os

# Check if database exists
db_path = 'instance/inventory.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== TRANSACTIONS TABLE SCHEMA ===")
    cursor.execute('PRAGMA table_info(transactions)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"{col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
    
    print("\n=== SAMPLE DATA ===")
    cursor.execute('SELECT * FROM transactions LIMIT 3')
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    print(f"\n=== TOTAL TRANSACTIONS ===")
    cursor.execute('SELECT COUNT(*) FROM transactions')
    print(f"Total transactions: {cursor.fetchone()[0]}")
    
    conn.close()
else:
    print(f"Database not found at {db_path}")