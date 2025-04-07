import sqlite3

DB = 'bot_store.db'

def validate_coupon(code):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT file_ids FROM coupons WHERE code = ?", (code,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0].split(',')  # Devuelve lista de file_ids
    return None

def coupon_used_by_user(user_id, code):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM redemptions WHERE user_id = ? AND coupon_code = ?", (user_id, code))
    result = c.fetchone()
    conn.close()
    return result is not None

def register_redemption(user_id, code):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO redemptions (user_id, coupon_code) VALUES (?, ?)", (user_id, code))
    conn.commit()
    conn.close()

def get_file_by_id(file_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name, file_id FROM files WHERE id = ?", (file_id,))
    result = c.fetchone()
    conn.close()
    return result  # (name, file_id)

def get_user_files(user_id):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT DISTINCT coupon_code FROM redemptions WHERE user_id = ?", (user_id,))
    coupons = c.fetchall()
    files = []

    for (code,) in coupons:
        c.execute("SELECT file_ids FROM coupons WHERE code = ?", (code,))
        result = c.fetchone()
        if result:
            for file_id in result[0].split(','):
                file = get_file_by_id(file_id)
                if file:
                    files.append(file)
    conn.close()
    return files

def add_coupon(code):
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    try:
        c.execute("INSERT INTO coupons (code, file_ids) VALUES (?, ?)", (code, ""))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
