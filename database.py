# database.py
import sqlite3
import os

DB_FILE = "quick_kv.db"

def connect_db():
    return sqlite3.connect(DB_FILE)

def ensure_db_tables():
    # 如果文件不存在，直接创建最新版本
    if not os.path.exists(DB_FILE):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version = 4")
        cursor.execute('''
            CREATE TABLE keys (
                id INTEGER PRIMARY KEY, key_text TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0, parent_id INTEGER DEFAULT 0, is_group INTEGER DEFAULT 0)
        ''')
        cursor.execute('''
            CREATE TABLE value_items (
                id INTEGER PRIMARY KEY, value_text TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0, parent_id INTEGER DEFAULT 0, is_group INTEGER DEFAULT 0)
        ''')
        conn.commit()
        conn.close()
        print("已创建全新的最新版本数据库。")
        return

    # 如果文件存在，检查版本并升级
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA user_version")
        db_version = cursor.fetchone()[0]
    except (sqlite3.OperationalError, TypeError):
        db_version = 0

    APP_DB_VERSION = 4

    if db_version < APP_DB_VERSION:
        print(f"数据库版本过旧 ({db_version})，正在升级到 {APP_DB_VERSION}...")
        # ... (升级逻辑与上一版相同，此处省略) ...
        # 为了保证升级的原子性，我们总是基于一个干净的状态来重建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='keys'")
        keys_exist = cursor.fetchone()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='value_items'")
        values_exist = cursor.fetchone()

        old_keys, old_values = [], []
        if keys_exist:
            cols = [desc[1] for desc in cursor.execute("PRAGMA table_info(keys)").fetchall()]
            if 'sort_order' in cols:
                cursor.execute("SELECT id, key_text, sort_order FROM keys")
                old_keys = cursor.fetchall()
            else:
                cursor.execute("SELECT id, key_text FROM keys")
                old_keys = [(r[0], r[1], 0) for r in cursor.fetchall()]
            cursor.execute("DROP TABLE keys")

        if values_exist:
            cols = [desc[1] for desc in cursor.execute("PRAGMA table_info(value_items)").fetchall()]
            if 'sort_order' in cols:
                cursor.execute("SELECT id, value_text, sort_order FROM value_items")
                old_values = cursor.fetchall()
            else:
                cursor.execute("SELECT id, value_text FROM value_items")
                old_values = [(r[0], r[1], 0) for r in cursor.fetchall()]
            cursor.execute("DROP TABLE value_items")

        # 创建最新结构的表
        cursor.execute('''
            CREATE TABLE keys (
                id INTEGER PRIMARY KEY, key_text TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0, parent_id INTEGER DEFAULT 0, is_group INTEGER DEFAULT 0)
        ''')
        cursor.execute('''
            CREATE TABLE value_items (
                id INTEGER PRIMARY KEY, value_text TEXT NOT NULL,
                sort_order INTEGER DEFAULT 0, parent_id INTEGER DEFAULT 0, is_group INTEGER DEFAULT 0)
        ''')
        
        if old_keys:
            cursor.executemany("INSERT INTO keys (id, key_text, sort_order) VALUES (?,?,?)", old_keys)
        if old_values:
            cursor.executemany("INSERT INTO value_items (id, value_text, sort_order) VALUES (?,?,?)", old_values)
        
        cursor.execute(f"PRAGMA user_version = {APP_DB_VERSION}")
        conn.commit()
        print("数据库升级完成。")
    conn.close()

# <<< NEW: 批量替换数据的事务函数 >>>
def replace_all_items(table_name, items_to_insert):
    """使用事务一次性替换表中的所有数据"""
    if table_name not in ["keys", "value_items"]: return False, "无效的表名"
    field_name = "key_text" if table_name == "keys" else "value_text"
    
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("BEGIN TRANSACTION")
        # 1. 清空旧数据
        cursor.execute(f"DELETE FROM {table_name}")
        # 2. 批量插入新数据
        # items_to_insert 格式: [(text, parent_id, is_group, sort_order), ...]
        cursor.executemany(
            f"INSERT INTO {table_name} ({field_name}, parent_id, is_group, sort_order) VALUES (?, ?, ?, ?)",
            items_to_insert
        )
        cursor.execute("COMMIT")
        return True, "导入成功"
    except Exception as e:
        cursor.execute("ROLLBACK")
        return False, f"导入失败: {e}"
    finally:
        conn.close()

# ... 其他 database 函数与上一版完全相同，此处省略 ...
def get_all_items(table_name, sort_mode="tree"):
    if table_name not in ["keys", "value_items"]: return []
    field_name = "key_text" if table_name == "keys" else "value_text"
    conn = connect_db()
    cursor = conn.cursor()
    if sort_mode == "tree":
        order_clause = "ORDER BY parent_id, sort_order"
    elif sort_mode == "alpha_asc":
        order_clause = f"ORDER BY {field_name} ASC"
    elif sort_mode == "alpha_desc":
        order_clause = f"ORDER BY {field_name} DESC"
    else:
        order_clause = "ORDER BY parent_id, sort_order"
    cursor.execute(f"SELECT id, {field_name}, parent_id, is_group, sort_order FROM {table_name} {order_clause}")
    items = cursor.fetchall()
    conn.close()
    return items
def add_item(table_name, text, parent_id=0, is_group=0):
    if table_name not in ["keys", "value_items"]: return False, "无效的表名"
    field_name = "key_text" if table_name == "keys" else "value_text"
    if not text: return False, "内容不能为空"
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO {table_name} ({field_name}, parent_id, is_group) VALUES (?, ?, ?)", (text, parent_id, is_group))
        conn.commit()
        return True, "添加成功"
    except sqlite3.IntegrityError:
        return False, "该内容已存在"
    finally:
        conn.close()
def update_item_text(table_name, item_id, new_text):
    if table_name not in ["keys", "value_items"]: return False, "无效的表名"
    field_name = "key_text" if table_name == "keys" else "value_text"
    conn = connect_db()
    try:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE {table_name} SET {field_name} = ? WHERE id = ?", (new_text, item_id))
        conn.commit()
        return True, "更新成功"
    except sqlite3.IntegrityError:
        return False, "该内容已存在"
    finally:
        conn.close()
def delete_item_recursive(table_name, item_id):
    if table_name not in ["keys", "value_items"]: return
    conn = connect_db()
    cursor = conn.cursor()
    children_to_delete = [item_id]
    processed_children = set()
    while set(children_to_delete) - processed_children:
        newly_found = list(set(children_to_delete) - processed_children)
        processed_children.update(newly_found)
        placeholders = ','.join('?' for _ in newly_found)
        cursor.execute(f"SELECT id FROM {table_name} WHERE parent_id IN ({placeholders})", newly_found)
        new_children = [row[0] for row in cursor.fetchall()]
        if not new_children:
            break
        children_to_delete.extend(new_children)
    placeholders = ','.join('?' for _ in children_to_delete)
    cursor.execute(f"DELETE FROM {table_name} WHERE id IN ({placeholders})", children_to_delete)
    conn.commit()
    conn.close()
def update_item_structure(table_name, item_id, new_parent_id, new_sort_order):
    if table_name not in ["keys", "value_items"]: return
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table_name} SET parent_id = ?, sort_order = ? WHERE id = ?", (new_parent_id, new_sort_order, item_id))
    conn.commit()
    conn.close()
