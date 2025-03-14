import sqlite3

def execute_query(query, id):
    conn = sqlite3.connect(f'{id}.db')
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

