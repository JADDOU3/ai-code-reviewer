import sqlite3

API_KEY = "sk-123456789"  # hardcoded secret

def get_user(username):
    conn = sqlite3.connect("app.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"  # SQL injection
    return conn.execute(query).fetchall()  # connection never closed

def average(numbers):
    return sum(numbers) / len(numbers)  # crashes on empty list