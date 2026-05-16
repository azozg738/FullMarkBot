import sqlite3
from datetime import datetime

DB_NAME = "orders.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            full_name TEXT,
            whatsapp TEXT,
            service_type TEXT,
            sub_service TEXT,
            status TEXT DEFAULT 'جديد',
            file_id TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def insert_order(user_id, username, full_name, whatsapp, service_type, sub_service, file_id=None):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO orders (user_id, username, full_name, whatsapp, service_type, sub_service, file_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, full_name, whatsapp, service_type, sub_service, file_id, created_at))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id

def update_order_status(order_id, status):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()

def search_orders(query):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if query.isdigit():
        cur.execute("SELECT * FROM orders WHERE order_id = ?", (int(query),))
    else:
        cur.execute("SELECT * FROM orders WHERE full_name LIKE ?", (f"%{query}%",))
    results = cur.fetchall()
    conn.close()
    return results

def get_order_by_id(order_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order = cur.fetchone()
    conn.close()
    return order

def get_statistics():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM orders")
    total = cur.fetchone()[0]
    cur.execute("SELECT status, COUNT(*) FROM orders GROUP BY status")
    statuses = cur.fetchall()
    conn.close()
    return total, statuses