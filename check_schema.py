#!/usr/bin/env python3
import sqlite3
import os

# Check if database exists
db_path = 'instance/inventory.db'
if not os.path.exists(db_path):
    print(f"Database {db_path} does not exist!")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== Database Schema Analysis ===\n")

# Get all tables
tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Tables found: {tables}\n")

# Check each table structure
for table in tables:
    print(f"=== {table.upper()} TABLE ===")
    columns = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # Show sample data
    try:
        sample = cursor.execute(f"SELECT * FROM {table} LIMIT 3").fetchall()
        if sample:
            print(f"  Sample data: {len(sample)} rows")
        else:
            print("  No data")
    except Exception as e:
        print(f"  Error reading data: {e}")
    print()

conn.close()
print("Schema analysis complete!")