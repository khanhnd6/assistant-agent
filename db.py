import sqlite3

def execute_query(query):
    conn = sqlite3.connect('money.db')
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        if query.strip().lower().startswith(("insert", "update", "delete", "create", "drop", "alter")):
            conn.commit()
        result = cursor.fetchall()
    except sqlite3.Error as e:
        result = f"Lỗi SQL: {e}"
    finally:
        conn.close()
    return result

def get_db_schema():
    conn = sqlite3.connect('money.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    schema = {}

    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()

        schema[table_name] = [
            {"id": col[0], "name": col[1], "type": col[2], "notnull": bool(col[3]), "default": col[4], "pk": bool(col[5])}
            for col in columns
        ]

    conn.close()
    return schema

