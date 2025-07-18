# database.py
import sqlite3

def connect_db(db_path):
    """建立到指定数据库文件的连接"""
    return sqlite3.connect(db_path)

def ensure_db_tables(db_path):
    """确保数据库和表存在，如果不存在则创建"""
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_text TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS value_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id INTEGER NOT NULL,
            value_text TEXT NOT NULL,
            FOREIGN KEY (key_id) REFERENCES keys (id)
        )
    ''')
    conn.commit()
    conn.close()

# --- 读取数据 ---
def get_all_keys(db_path):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, key_text FROM keys ORDER BY key_text")
    keys = cursor.fetchall()
    conn.close()
    return keys # 返回 (id, text) 元组列表

def get_values_for_key(db_path, key_id):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, value_text FROM value_items WHERE key_id = ? ORDER BY value_text", (key_id,))
    values = cursor.fetchall()
    conn.close()
    return values # 返回 (id, text) 元组列表

# --- 写入/修改数据 ---
def add_key(db_path, key_text):
    if not key_text: return False, "键不能为空"
    conn = connect_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO keys (key_text) VALUES (?)", (key_text,))
        conn.commit()
        return True, "添加成功"
    except sqlite3.IntegrityError:
        return False, "键已存在"
    finally:
        conn.close()

def update_key(db_path, key_id, new_text):
    conn = connect_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE keys SET key_text = ? WHERE id = ?", (new_text, key_id))
        conn.commit()
        return True, "更新成功"
    except sqlite3.IntegrityError:
        return False, "该键名已存在"
    finally:
        conn.close()

def delete_key(db_path, key_id):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM value_items WHERE key_id = ?", (key_id,))
    cursor.execute("DELETE FROM keys WHERE id = ?", (key_id,))
    conn.commit()
    conn.close()
    return True, "删除成功"

def add_value(db_path, key_id, value_text):
    if not value_text: return False, "值不能为空"
    conn = connect_db(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO value_items (key_id, value_text) VALUES (?, ?)", (key_id, value_text))
        conn.commit()
        return True, "添加成功"
    except sqlite3.IntegrityError: # 假设 (key_id, value_text) 是唯一的
        return False, "该值已存在"
    finally:
        conn.close()

def update_value(db_path, value_id, new_text):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE value_items SET value_text = ? WHERE id = ?", (new_text, value_id))
    conn.commit()
    conn.close()
    return True, "更新成功"

def delete_value(db_path, value_id):
    conn = connect_db(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM value_items WHERE id = ?", (value_id,))
    conn.commit()
    conn.close()
    return True, "删除成功"
