import sqlite3

def init_db():
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()

    # Tabla de archivos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        telegram_file_id TEXT NOT NULL UNIQUE
    )
    """)

    # Tabla de cupones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupons (
        code TEXT PRIMARY KEY
    )
    """)

    # Asociación entre cupones y archivos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS coupon_files (
        coupon_code TEXT,
        file_id INTEGER,
        FOREIGN KEY (coupon_code) REFERENCES coupons(code),
        FOREIGN KEY (file_id) REFERENCES files(id)
    )
    """)

    # Redenciones
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS redemptions (
        user_id INTEGER,
        coupon_code TEXT,
        FOREIGN KEY (coupon_code) REFERENCES coupons(code)
    )
    """)

    conn.commit()
    conn.close()

# Otras funciones que usas en tu bot:

def add_file(name, telegram_file_id):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (name, telegram_file_id) VALUES (?, ?)", (name, telegram_file_id))
    conn.commit()
    conn.close()

def add_coupon(code):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO coupons (code) VALUES (?)", (code,))
    conn.commit()
    conn.close()

def validate_coupon(code):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM coupons WHERE code = ?", (code,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def coupon_used_by_user(user_id, code):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM redemptions WHERE user_id = ? AND coupon_code = ?", (user_id, code))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def register_redemption(user_id, code):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO redemptions (user_id, coupon_code) VALUES (?, ?)", (user_id, code))
    conn.commit()
    conn.close()

def get_file_by_id(file_id):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_file_id FROM files WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def associate_file_with_coupon(coupon_code, file_id):
    conn = sqlite3.connect("bot_store.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO coupon_files (coupon_code, file_id) VALUES (?, ?)",
        (coupon_code, file_id)
    )
    conn.commit()
    conn.close()
