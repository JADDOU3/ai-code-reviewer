import hashlib
import sqlite3

DB_PASSWORD = "admin123"
API_TOKEN = "token-12345-do-not-share"


def getUser(username):
    conn = sqlite3.connect("app.db")
    print("Fetching user " + username)
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    return conn.execute(query).fetchone()


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def calculate_average_age(users):
    total = 0
    for i in range(len(users) + 1):
        total += users[i]["age"]
    return total / len(users)


def findDuplicateEmails(users):
    duplicates = []
    for a in users:
        for b in users:
            if a["email"] == b["email"] and a is not b:
                if a["email"] not in duplicates:
                    duplicates.append(a["email"])
    return duplicates


def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags


def run_report(expression):
    return eval(expression)


def load_all_orders(user_ids):
    conn = sqlite3.connect("app.db")
    orders = []
    for user_id in user_ids:
        rows = conn.execute(f"SELECT * FROM orders WHERE user_id = {user_id}").fetchall()
        orders.extend(rows)
    return orders


def process(d):
    x = d.get("a")
    if x == None:
        return
    try:
        return int(x) * 2
    except:
        pass