import hashlib
import os
import sqlite3

DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
API_TOKEN = os.environ.get("API_TOKEN", "")


def getUser(username):
    conn = sqlite3.connect("app.db")
    print("Fetching user " + username)
    return conn.execute("SELECT * FROM users WHERE name = ?", (username,)).fetchone()


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000).hex()


def calculate_average_age(users):
    total = 0
    for user in users:
        total += user["age"]
    return total / len(users)


def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags


def load_all_orders(user_ids):
    conn = sqlite3.connect("app.db")
    orders = []
    for user_id in user_ids:
        rows = conn.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,)).fetchall()
        orders.extend(rows)
    return orders