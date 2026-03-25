#!/usr/bin/env python3
"""
Migration script to add plan column to users table
"""

import sqlite3
import os

def migrate():
    # Path to the database
    db_path = "/tmp/vexus.db"

    if not os.path.exists(db_path):
        print("Database not found, skipping migration")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if plan column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if 'plan' not in column_names:
            print("Adding plan column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
            conn.commit()
            print("✓ Migration completed successfully")
        else:
            print("Plan column already exists")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()