#!/usr/bin/env python3
import sqlite3
import os

db_path = "echotuner.db"
if not os.path.exists(db_path):
    print(f"Database file not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# Check auth_sessions table structure
cursor.execute("PRAGMA table_info(auth_sessions)")
schema = cursor.fetchall()
print("auth_sessions schema:", schema)

# Check recent sessions
cursor.execute("SELECT session_id, device_id, spotify_user_id, expires_at, account_type FROM auth_sessions ORDER BY created_at DESC LIMIT 5")
sessions = cursor.fetchall()
print("Recent sessions:")
for session in sessions:
    print(f"  Session: {session[0][:8]}..., Device: {session[1][:20]}..., User: {session[2]}, Expires: {session[3]}, Type: {session[4]}")

# Check all sessions
cursor.execute("SELECT COUNT(*) FROM auth_sessions")
count = cursor.fetchone()[0]
print(f"Total sessions: {count}")

conn.close()
