#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database example
"""

import sqlite3

def create_database(db_name):
    """Create a SQLite database and a sample table."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create a table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"Database {db_name} created with users table")

def insert_user(db_name, name, email, age):
    """Insert a user into the database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
            (name, email, age)
        )
        conn.commit()
        print(f"User {name} added to database")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def get_all_users(db_name):
    """Get all users from the database."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    conn.close()
    return users

# Example usage
if __name__ == '__main__':
    db_name = 'example.db'
    
    # Create the database and table
    create_database(db_name)
    
    # Insert some users
    insert_user(db_name, 'Alice', 'alice@example.com', 30)
    insert_user(db_name, 'Bob', 'bob@example.com', 25)
    insert_user(db_name, 'Charlie', 'charlie@example.com', 35)
    
    # Get and display all users
    users = get_all_users(db_name)
    print("\nAll Users:")
    for user in users:
        print(f"ID: {user[0]}, Name: {user[1]}, Email: {user[2]}, Age: {user[3]}")
